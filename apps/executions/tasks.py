"""
Celery tasks for executions:
1. send_notification_task — send notifications via email/slack/ui_message
2. check_step_timeout — handle approval step timeout
3. check_all_timeouts — periodic safety net (every 5 min via Celery Beat)
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _render_template(template: str, data: dict) -> str:
    """Replace {field_name} placeholders in template with actual values."""
    result = template
    for key, value in data.items():
        result = result.replace(f'{{{key}}}', str(value))
    return result


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_task(
    self,
    execution_id: str,
    step_id: str,
    channel: str,
    template: str,
    recipients: list,
    data: dict,
):
    """
    Send a notification for a notification-type step.

    Supports channels:
    - email    → Django email backend
    - slack    → HTTP POST to webhook (URL from data or settings)
    - ui_message → store in Redis for frontend polling

    Retries up to 3 times on failure.
    """
    from apps.executions.models import Execution

    try:
        execution = Execution.objects.get(id=execution_id)
    except Execution.DoesNotExist:
        logger.error('send_notification_task: Execution %s not found.', execution_id)
        return

    # Render template with actual data
    message = _render_template(template, data)

    success = False
    error_msg = None

    try:
        if channel == 'email':
            from django.core.mail import send_mail
            from django.conf import settings

            send_mail(
                subject='Workflow Notification',
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@halleyx.com'),
                recipient_list=recipients,
                fail_silently=False,
            )
            success = True

        elif channel == 'slack':
            import urllib.request
            import urllib.error
            import json as json_lib

            slack_webhook = data.get('slack_webhook_url', '')
            if not slack_webhook:
                from django.conf import settings
                slack_webhook = getattr(settings, 'SLACK_WEBHOOK_URL', '')

            if slack_webhook:
                payload = json_lib.dumps({'text': message}).encode('utf-8')
                req = urllib.request.Request(
                    slack_webhook,
                    data=payload,
                    headers={'Content-Type': 'application/json'},
                    method='POST',
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        success = True
                    else:
                        error_msg = f'Slack returned status {resp.status}'
            else:
                logger.warning('No Slack webhook URL configured.')
                success = True  # Don't fail if not configured

        elif channel == 'ui_message':
            import django_redis
            from django.core.cache import cache
            import json as json_lib

            key = f'ui_notification:{execution_id}'
            existing = cache.get(key, [])
            existing.append({
                'message': message,
                'step_id': step_id,
                'timestamp': timezone.now().isoformat(),
                'recipients': recipients,
            })
            cache.set(key, existing, timeout=86400)  # 24 hours
            success = True

        else:
            logger.warning('Unknown notification channel: %s', channel)
            success = True

    except Exception as exc:
        error_msg = str(exc)
        logger.error('send_notification_task failed (%s): %s', channel, exc)
        # Retry on failure
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error('Max retries exceeded for notification task %s.', self.request.id)

    # Log result in execution
    try:
        execution.refresh_from_db()
        log_entry = {
            'type': 'notification',
            'step_id': step_id,
            'channel': channel,
            'recipients': recipients,
            'message': message,
            'success': success,
            'error': error_msg,
            'sent_at': timezone.now().isoformat(),
        }
        execution.logs = list(execution.logs) + [log_entry]
        execution.save(update_fields=['logs'])
    except Exception as exc:
        logger.error('Failed to log notification result: %s', exc)


@shared_task(bind=True)
def check_step_timeout(self, execution_id: str, step_id: str):
    """
    Called after timeout_hours delay via apply_async(countdown=...).
    Checks if the approval step is still pending and handles it.

    on_timeout options:
    - 'escalate'     → change assignee to escalate_to email
    - 'auto_approve' → automatically approve
    - 'auto_reject'  → automatically reject
    - default        → mark step as failed
    """
    from apps.executions.models import Execution
    from apps.steps.models import Step
    from apps.engine.executor import ExecutionEngine

    try:
        execution = Execution.objects.get(id=execution_id)
    except Execution.DoesNotExist:
        logger.warning('check_step_timeout: Execution %s not found.', execution_id)
        return

    # Only handle if still at this step and in progress
    if execution.status != 'in_progress':
        return
    if str(execution.current_step_id) != str(step_id):
        return  # Step already advanced — no timeout needed

    try:
        step = Step.objects.get(id=step_id)
    except Step.DoesNotExist:
        logger.warning('check_step_timeout: Step %s not found.', step_id)
        return

    metadata = step.metadata or {}
    on_timeout = metadata.get('on_timeout', '')
    escalate_to = metadata.get('escalate_to', '')

    logger.info(
        'Timeout reached for execution %s step %s. Action: %s',
        execution_id, step_id, on_timeout
    )

    engine = ExecutionEngine()

    if on_timeout == 'escalate':
        # Change assignee to escalate_to
        if escalate_to:
            step.metadata['assignee_email'] = escalate_to
            step.save(update_fields=['metadata'])
            log_entry = {
                'type': 'timeout_escalation',
                'step_id': step_id,
                'step_name': step.name,
                'escalated_to': escalate_to,
                'timestamp': timezone.now().isoformat(),
            }
            execution.logs = list(execution.logs) + [log_entry]
            execution.save(update_fields=['logs'])

            # Queue another timeout for the escalated assignee
            timeout_hours = metadata.get('timeout_hours', 24)
            check_step_timeout.apply_async(
                args=[execution_id, step_id],
                countdown=timeout_hours * 3600,
            )
        else:
            # No escalate_to — fail the step
            _fail_step_on_timeout(execution, step)

    elif on_timeout == 'auto_approve':
        # Create a system user-like object for the action
        _system_approval_action(engine, execution, step, 'approve', 'Auto-approved due to timeout')

    elif on_timeout == 'auto_reject':
        _system_approval_action(engine, execution, step, 'reject', 'Auto-rejected due to timeout')

    else:
        _fail_step_on_timeout(execution, step)


def _fail_step_on_timeout(execution, step):
    """Mark execution as failed due to timeout."""
    execution.status = 'failed'
    execution.ended_at = timezone.now()
    execution.logs = list(execution.logs) + [{
        'type': 'timeout_failure',
        'step_id': str(step.id),
        'step_name': step.name,
        'error': 'Timeout: No action configured or no escalation target.',
        'timestamp': timezone.now().isoformat(),
    }]
    execution.save()


def _system_approval_action(engine, execution, step, action: str, comment: str):
    """Perform an auto approval action (auto_approve or auto_reject)."""
    try:
        # Create a minimal dummy user-like object
        class SystemActor:
            email = 'system@halleyx.com'
            role = 'super_admin'

        engine.handle_approval_action(
            execution_id=str(execution.id),
            step_id=str(step.id),
            user=SystemActor(),
            action=action,
            comment=comment,
        )
        execution.logs = list(execution.logs) + [{
            'type': f'timeout_{action}',
            'step_id': str(step.id),
            'step_name': step.name,
            'action_by': 'system',
            'comment': comment,
            'timestamp': timezone.now().isoformat(),
        }]
        execution.save(update_fields=['logs'])
    except Exception as exc:
        logger.error('_system_approval_action failed: %s', exc)
        _fail_step_on_timeout(execution, step)


@shared_task
def check_all_timeouts():
    """
    Periodic safety net — runs every 5 minutes via Celery Beat.
    Finds all in_progress executions where the approval step has timed out.
    """
    from apps.executions.models import Execution
    from apps.steps.models import Step
    import datetime

    in_progress = Execution.objects.filter(status='in_progress').exclude(current_step_id=None)

    for execution in in_progress:
        try:
            step = Step.objects.get(id=execution.current_step_id)
        except Step.DoesNotExist:
            continue

        if step.step_type != 'approval':
            continue

        metadata = step.metadata or {}
        timeout_hours = metadata.get('timeout_hours', 24)

        # Find when this step started from logs
        step_started_at = None
        for log_entry in execution.logs:
            if log_entry.get('step_id') == str(step.id) and 'started_at' in log_entry:
                try:
                    step_started_at = datetime.datetime.fromisoformat(
                        log_entry['started_at'].replace('Z', '+00:00')
                    )
                except (ValueError, AttributeError):
                    pass
                break

        if step_started_at is None:
            continue

        deadline = step_started_at + datetime.timedelta(hours=timeout_hours)
        if timezone.now() > deadline:
            logger.info(
                'check_all_timeouts: timeout detected for execution %s step %s',
                execution.id, step.id
            )
            check_step_timeout.delay(str(execution.id), str(step.id))
