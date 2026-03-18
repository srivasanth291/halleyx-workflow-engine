import os
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from apps.executions.models import Execution, EmailNotification, ActionToken
from apps.steps.models import Step
import json
from django.urls import reverse

@shared_task(bind=True, max_retries=3)
def send_notification_task(self, execution_id, step_id, channel, template, recipients, data, subject="Workflow Notification", company_id=None):
    try:
        execution = Execution.objects.get(id=execution_id) if execution_id else None
        step = Step.objects.get(id=step_id) if step_id else None
        
        processed_subject = subject
        processed_body = template
        for k, v in data.items():
            processed_subject = processed_subject.replace(f"{{{k}}}", str(v))
            processed_body = processed_body.replace(f"{{{k}}}", str(v))
            
        for recipient in recipients:
            notification = EmailNotification.objects.create(
                company_id=execution.company_id if execution else company_id,
                execution=execution,
                step_name=step.name if step else '',
                recipient=recipient,
                subject=processed_subject,
                body=processed_body,
                channel=channel,
                status='pending'
            )
            
            try:
                if channel == 'email':
                    # If this is an approval step, add links
                    final_body = processed_body
                    if step and step.step_type == 'approval':
                        base_url = "http://localhost:8000" # fallback if not in settings
                        approve_token = ActionToken.objects.create(
                            execution=execution, 
                            step_id=step.id,
                            action='approve',
                            expires_at=timezone.now() + timedelta(days=7)
                        )
                        reject_token = ActionToken.objects.create(
                            execution=execution,
                            step_id=step.id,
                            action='reject',
                            expires_at=timezone.now() + timedelta(days=7)
                        )
                        
                        approve_url = f"{base_url}/api/action-token/{approve_token.id}/"
                        reject_url = f"{base_url}/api/action-token/{reject_token.id}/"
                        
                        final_body += f"\n\nDirect Actions:\nApprove: {approve_url}\nReject: {reject_url}"

                    print(f"--- EMAIL DEMO ---")
                    print(f"To: {recipient}")
                    print(f"Subject: {processed_subject}")
                    print(f"Body: {final_body}")
                    print(f"-------------------")
                    send_mail(
                        subject=processed_subject,
                        message=final_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient],
                        fail_silently=False,
                    )
                notification.status = 'sent'
                notification.sent_at = timezone.now()
                notification.save()
            except Exception as e:
                notification.status = 'failed'
                notification.error = str(e)
                notification.save()
                raise e
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

@shared_task(bind=True)
def check_step_timeout(self, execution_id, step_id):
    try:
        from apps.engine.executor import ExecutionEngine
        execution = Execution.objects.get(id=execution_id)
        if str(execution.current_step_id) != str(step_id) or execution.status != 'in_progress':
            return
            
        step = Step.objects.get(id=step_id)
        
        # Must specifically be pending approval in logs
        is_pending = False
        for log in reversed(execution.logs):
            if log.get('status') == 'pending_approval' and str(log.get('step_id')) == str(step_id):
                is_pending = True
                break
            if str(log.get('step_id')) == str(step_id) and log.get('status') in ['completed', 'failed']:
                return # Already completed
                
        if not is_pending:
            return
            
        on_timeout = step.metadata.get('on_timeout')
        if not on_timeout:
            return
            
        engine = ExecutionEngine()
        if on_timeout == 'escalate':
            escalate_to = step.metadata.get('escalate_to')
            if escalate_to:
                # Add log for escalation
                log_entry = {
                    "step_id": str(step_id),
                    "step_name": step.name,
                    "step_type": step.step_type,
                    "status": "pending_approval",
                    "action_by": "system",
                    "action_at": timezone.now().isoformat(),
                    "comment": f"Escalated due to timeout to {escalate_to}"
                }
                
                execution.logs.append(log_entry)
                execution.save()
                
                step.metadata['assignee_email'] = escalate_to
                step.save()
                
                send_notification_task.delay(
                    execution_id, step_id, 'email',
                    f"Task requires your approval. It was escalated due to timeout.",
                    [escalate_to],
                    execution.data,
                    "Workflow Task Escalation"
                )
        elif on_timeout == 'auto_approve':
            engine.handle_approval_action(execution_id, step_id, None, 'approve', "Auto-approved (timeout)")
        elif on_timeout == 'auto_reject':
            engine.handle_approval_action(execution_id, step_id, None, 'reject', "Auto-rejected (timeout)")
            
    except Exception:
        pass

@shared_task
def check_all_timeouts():
    executions = Execution.objects.filter(status='in_progress')
    for execution in executions:
        if execution.current_step_id:
            try:
                step = Step.objects.get(id=execution.current_step_id)
                if step.step_type == 'approval':
                    timeout_hours = int(step.metadata.get('timeout_hours', 24))
                    
                    last_action_time = execution.started_at
                    for log in reversed(execution.logs):
                        if str(log.get('step_id')) == str(step.id) and log.get('status') == 'pending_approval':
                            if 'action_at' in log:
                                last_action_time = timezone.datetime.fromisoformat(log['action_at'].replace('Z', '+00:00'))
                            break
                            
                    if timezone.now() > last_action_time + timedelta(hours=timeout_hours):
                        check_step_timeout.delay(execution.id, step.id)
            except Step.DoesNotExist:
                continue
