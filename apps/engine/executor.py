"""
Execution engine — orchestrates workflow execution.
Handles step processing, approval actions, retries, and cancellations.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from django.utils import timezone as django_timezone

from apps.engine.rule_engine import RuleEngine, WorkflowTerminationException, MaxIterationsException

logger = logging.getLogger(__name__)

rule_engine = RuleEngine()


def _now_iso():
    return django_timezone.now().isoformat()


def _validate_execution_input(input_schema: Dict, input_data: Dict) -> None:
    """
    Validate input_data against workflow.input_schema.
    Raises: rest_framework.exceptions.ValidationError if invalid.
    """
    from rest_framework.exceptions import ValidationError
    errors = {}

    for field in input_schema.get('fields', []):
        field_name = field['name']
        field_type = field.get('type', 'string')
        required = field.get('required', False)
        allowed = field.get('allowed_values', [])

        # Required check
        if required and field_name not in input_data:
            errors[field_name] = f'This field is required.'
            continue

        if field_name not in input_data:
            continue

        value = input_data[field_name]

        # Type check
        if field_type == 'number':
            try:
                float(str(value))
            except (ValueError, TypeError):
                errors[field_name] = f"Must be a number, got '{value}'."
        elif field_type == 'boolean':
            if not isinstance(value, bool):
                errors[field_name] = f"Must be true or false."
        elif field_type == 'string':
            if not isinstance(value, str):
                errors[field_name] = f"Must be a string."

        # Allowed values check
        if allowed and str(value) not in [str(a) for a in allowed]:
            errors[field_name] = f"Must be one of {allowed}, got '{value}'."

    if errors:
        raise ValidationError(errors)


class ExecutionEngine:
    """
    Orchestrates workflow execution including step processing,
    rule evaluation, approval handling, retries, and cancellations.
    """

    # ─────────────────────────────────────────────────────
    # METHOD 1: start_execution
    # ─────────────────────────────────────────────────────

    def start_execution(self, workflow_id: str, input_data: Dict, user, max_iterations: int = 10):
        """
        Start a new workflow execution.

        Steps:
        1. Get active workflow
        2. Validate input_data against schema
        3. Create Execution record
        4. Set status = in_progress
        5. Get and process start step
        """
        from apps.workflows.models import Workflow
        from apps.executions.models import Execution
        from rest_framework.exceptions import ValidationError, NotFound

        # Step 1: Get active workflow
        try:
            workflow = Workflow.objects.get(id=workflow_id, is_active=True)
        except Workflow.DoesNotExist:
            raise NotFound(f'Active workflow {workflow_id} not found.')

        # Step 2: Validate input_data against input_schema
        _validate_execution_input(workflow.input_schema, input_data)

        # Step 3: Validate at least one step exists
        from apps.steps.models import Step
        steps = Step.objects.filter(workflow=workflow)
        if not steps.exists():
            raise ValidationError({'detail': 'Workflow has no steps. Add steps before executing.'})

        if not workflow.start_step_id:
            raise ValidationError({'detail': 'Workflow has no start step configured.'})

        # Step 4: Create Execution record
        execution = Execution.objects.create(
            workflow=workflow,
            workflow_version=workflow.version,
            status='pending',
            data=input_data,
            triggered_by=user,
            max_iterations=max_iterations,
            iteration_count=0,
            logs=[],
        )

        # Step 5: Set in_progress and process start step
        execution.status = 'in_progress'
        execution.save(update_fields=['status'])

        try:
            start_step = Step.objects.get(id=workflow.start_step_id)
        except Step.DoesNotExist:
            execution.status = 'failed'
            execution.ended_at = django_timezone.now()
            execution.logs.append({
                'error': f'Start step {workflow.start_step_id} not found.',
                'timestamp': _now_iso(),
            })
            execution.save()
            return execution

        self.process_step(execution, start_step)
        return execution

    # ─────────────────────────────────────────────────────
    # METHOD 2: process_step
    # ─────────────────────────────────────────────────────

    def process_step(self, execution, step):
        """
        Process a single workflow step.
        Handles task, approval, and notification step types.
        Implements loop prevention via iteration_count.
        """
        # ── STEP 1: LOOP PREVENTION CHECK ──────────────────
        execution.iteration_count += 1
        execution.current_step_id = step.id
        execution.save(update_fields=['iteration_count', 'current_step_id'])

        if execution.iteration_count > execution.max_iterations:
            termination_log = {
                'error': 'Max iterations exceeded',
                'iteration_count': execution.iteration_count,
                'max_allowed': execution.max_iterations,
                'terminated_at_step': step.name,
                'timestamp': _now_iso(),
            }
            execution.logs = list(execution.logs) + [termination_log]
            execution.status = 'failed'
            execution.ended_at = django_timezone.now()
            execution.save()
            raise MaxIterationsException(
                f'Workflow terminated: exceeded {execution.max_iterations} max iterations. '
                f'Possible infinite loop detected.'
            )

        step_start_time = django_timezone.now()

        # ── STEP 2: Log step start ──────────────────────────
        step_log_entry = {
            'step_id': str(step.id),
            'step_name': step.name,
            'step_type': step.step_type,
            'status': 'started',
            'started_at': step_start_time.isoformat(),
            'action_by': None,
            'action_at': None,
            'comment': None,
            'rule_matched': None,
            'next_step_id': None,
            'next_step_name': None,
            'duration_seconds': None,
            'rule_evaluation_log': [],
        }
        execution.logs = list(execution.logs) + [step_log_entry]
        execution.save(update_fields=['logs'])

        # ── STEP 3: Handle by step_type ────────────────────
        if step.step_type == 'task':
            self._process_task_step(execution, step, step_log_entry, step_start_time)

        elif step.step_type == 'notification':
            self._process_notification_step(execution, step, step_log_entry, step_start_time)

        elif step.step_type == 'approval':
            self._process_approval_step(execution, step, step_log_entry)

    # ─────────────────────────────────────────────────────
    # STEP TYPE HANDLERS
    # ─────────────────────────────────────────────────────

    def _process_task_step(self, execution, step, log_entry: Dict, start_time):
        """Handle a task step — auto complete."""
        from apps.rules.models import Rule

        rules = Rule.objects.filter(step=step).order_by('priority')

        try:
            result = rule_engine.evaluate(rules, execution.data)
        except WorkflowTerminationException as exc:
            self._fail_execution(execution, step, log_entry, str(exc))
            return

        next_step_id = result.get('next_step_id')
        rule_eval_log = result.get('evaluation_log', [])

        # Update log entry
        duration = (django_timezone.now() - start_time).total_seconds()
        log_entry.update({
            'status': 'completed',
            'action_by': 'system',
            'action_at': django_timezone.now().isoformat(),
            'rule_matched': result.get('matched_condition'),
            'next_step_id': next_step_id,
            'duration_seconds': int(duration),
            'rule_evaluation_log': rule_eval_log,
        })
        self._update_log_entry(execution, log_entry)

        # Determine next step
        if next_step_id is None:
            execution.status = 'completed'
            execution.ended_at = django_timezone.now()
            execution.save()
            return

        try:
            from apps.steps.models import Step
            next_step = Step.objects.get(id=next_step_id)
            log_entry['next_step_name'] = next_step.name
            self._update_log_entry(execution, log_entry)
        except Exception:
            self._fail_execution(execution, step, log_entry, f'Next step {next_step_id} not found.')
            return

        # Recurse to next step
        self.process_step(execution, next_step)

    def _process_notification_step(self, execution, step, log_entry: Dict, start_time):
        """Handle a notification step — queue Celery task, auto continue."""
        from apps.rules.models import Rule
        from apps.executions.tasks import send_notification_task

        metadata = step.metadata or {}
        channel = metadata.get('notification_channel', 'email')
        template = metadata.get('template', '')
        recipients = metadata.get('recipients', [])

        # Queue the notification (don't wait for it)
        try:
            send_notification_task.delay(
                str(execution.id),
                str(step.id),
                channel,
                template,
                recipients,
                execution.data,
            )
        except Exception as exc:
            logger.warning('Failed to queue notification task: %s', exc)

        # Auto-complete, evaluate rules, move on
        rules = Rule.objects.filter(step=step).order_by('priority')

        try:
            result = rule_engine.evaluate(rules, execution.data)
        except WorkflowTerminationException as exc:
            self._fail_execution(execution, step, log_entry, str(exc))
            return

        next_step_id = result.get('next_step_id')
        duration = (django_timezone.now() - start_time).total_seconds()

        log_entry.update({
            'status': 'completed',
            'action_by': 'system',
            'action_at': django_timezone.now().isoformat(),
            'rule_matched': result.get('matched_condition'),
            'next_step_id': next_step_id,
            'duration_seconds': int(duration),
            'rule_evaluation_log': result.get('evaluation_log', []),
        })
        self._update_log_entry(execution, log_entry)

        if next_step_id is None:
            execution.status = 'completed'
            execution.ended_at = django_timezone.now()
            execution.save()
            return

        try:
            from apps.steps.models import Step
            next_step = Step.objects.get(id=next_step_id)
            log_entry['next_step_name'] = next_step.name
            self._update_log_entry(execution, log_entry)
            self.process_step(execution, next_step)
        except Exception as exc:
            self._fail_execution(execution, step, log_entry, str(exc))

    def _process_approval_step(self, execution, step, log_entry: Dict):
        """Handle an approval step — pause and wait for human action."""
        from apps.executions.tasks import check_step_timeout

        metadata = step.metadata or {}
        assignee = metadata.get('assignee_email', 'N/A')
        timeout_hours = metadata.get('timeout_hours', 24)

        log_entry.update({
            'status': 'pending_approval',
            'action_by': None,
            'action_at': None,
            'comment': f'Waiting for approval from {assignee}',
        })
        self._update_log_entry(execution, log_entry)

        execution.current_step_id = step.id
        execution.save(update_fields=['current_step_id'])

        # Queue timeout check
        try:
            check_step_timeout.apply_async(
                args=[str(execution.id), str(step.id)],
                countdown=timeout_hours * 3600,
            )
        except Exception as exc:
            logger.warning('Failed to queue timeout task: %s', exc)

    # ─────────────────────────────────────────────────────
    # METHOD 3: handle_approval_action
    # ─────────────────────────────────────────────────────

    def handle_approval_action(
        self,
        execution_id: str,
        step_id: str,
        user,
        action: str,
        comment: str = '',
    ):
        """
        Handle approve / reject / return action on an approval step.
        """
        from apps.executions.models import Execution
        from apps.steps.models import Step
        from apps.rules.models import Rule
        from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

        # Step 1: Get execution
        try:
            execution = Execution.objects.get(id=execution_id)
        except Execution.DoesNotExist:
            raise NotFound(f'Execution {execution_id} not found.')

        # Step 2: Get current step
        try:
            step = Step.objects.get(id=step_id)
        except Step.DoesNotExist:
            raise NotFound(f'Step {step_id} not found.')

        if str(execution.current_step_id) != str(step_id):
            raise ValidationError({'detail': 'This step is not the current active step.'})

        # Step 3: Validate user is assignee or admin
        metadata = step.metadata or {}
        assignee_email = metadata.get('assignee_email', '')
        if user.role not in ('super_admin', 'admin') and user.email != assignee_email:
            raise PermissionDenied(
                f'Only {assignee_email} or admin can act on this approval.'
            )

        action_time = django_timezone.now()

        # Step 4: Log the action
        logs = list(execution.logs)
        for entry in reversed(logs):
            if entry.get('step_id') == str(step_id) and entry.get('status') == 'pending_approval':
                entry.update({
                    'status': action,
                    'action_by': user.email,
                    'action_at': action_time.isoformat(),
                    'comment': comment,
                })
                break
        execution.logs = logs

        # Step 5: Build evaluation data with action context
        eval_data = {
            **execution.data,
            'approved': action == 'approve',
            'rejected': action == 'reject',
            'returned': action == 'return',
            'action': action,
            'comment': comment,
        }

        # Step 6: Evaluate rules
        rules = Rule.objects.filter(step=step).order_by('priority')
        try:
            result = rule_engine.evaluate(rules, eval_data)
        except WorkflowTerminationException as exc:
            execution.status = 'failed'
            execution.ended_at = action_time
            execution.logs = list(execution.logs) + [{'error': str(exc), 'timestamp': _now_iso()}]
            execution.save()
            return execution

        next_step_id = result.get('next_step_id')

        # Update the log entry with rule results
        for entry in execution.logs:
            if entry.get('step_id') == str(step_id):
                entry.update({
                    'rule_matched': result.get('matched_condition'),
                    'next_step_id': next_step_id,
                    'rule_evaluation_log': result.get('evaluation_log', []),
                })
                if 'started_at' in entry:
                    started = datetime.fromisoformat(entry['started_at'].replace('Z', '+00:00'))
                    duration = (action_time - started).total_seconds()
                    entry['duration_seconds'] = int(duration)
                break

        # Step 7: Determine next step
        if next_step_id is None:
            execution.status = 'completed'
            execution.ended_at = action_time
            execution.save()
            return execution

        execution.save(update_fields=['logs', 'status', 'ended_at'])

        try:
            from apps.steps.models import Step as StepModel
            next_step = StepModel.objects.get(id=next_step_id)
            self.process_step(execution, next_step)
        except Exception as exc:
            execution.status = 'failed'
            execution.ended_at = django_timezone.now()
            execution.logs = list(execution.logs) + [{'error': str(exc), 'timestamp': _now_iso()}]
            execution.save()

        return execution

    # ─────────────────────────────────────────────────────
    # METHOD 4: retry_execution
    # ─────────────────────────────────────────────────────

    def retry_execution(self, execution_id: str, user):
        """
        Retry a FAILED execution from the current (failed) step only.
        NOT the entire workflow from beginning.
        """
        from apps.executions.models import Execution
        from apps.steps.models import Step
        from rest_framework.exceptions import ValidationError, NotFound

        try:
            execution = Execution.objects.get(id=execution_id)
        except Execution.DoesNotExist:
            raise NotFound(f'Execution {execution_id} not found.')

        if execution.status != 'failed':
            raise ValidationError({'detail': 'Only failed executions can be retried.'})

        if not execution.current_step_id:
            raise ValidationError({'detail': 'No current step to retry from.'})

        try:
            step = Step.objects.get(id=execution.current_step_id)
        except Step.DoesNotExist:
            raise ValidationError({'detail': f'Step {execution.current_step_id} not found.'})

        execution.status = 'in_progress'
        execution.retries += 1
        execution.logs = list(execution.logs) + [{
            'action': 'retry',
            'retry_number': execution.retries,
            'retried_step': step.name,
            'retried_by': user.email,
            'retried_at': _now_iso(),
        }]
        execution.save()

        self.process_step(execution, step)
        return execution

    # ─────────────────────────────────────────────────────
    # METHOD 5: cancel_execution
    # ─────────────────────────────────────────────────────

    def cancel_execution(self, execution_id: str, user):
        """
        Cancel a running or pending execution.
        """
        from apps.executions.models import Execution
        from rest_framework.exceptions import ValidationError, NotFound

        try:
            execution = Execution.objects.get(id=execution_id)
        except Execution.DoesNotExist:
            raise NotFound(f'Execution {execution_id} not found.')

        if execution.status not in ('pending', 'in_progress'):
            raise ValidationError({
                'detail': f'Cannot cancel execution with status "{execution.status}".'
            })

        execution.status = 'canceled'
        execution.ended_at = django_timezone.now()
        execution.logs = list(execution.logs) + [{
            'action': 'canceled',
            'canceled_by': user.email,
            'canceled_at': _now_iso(),
            'reason': 'User manually canceled',
        }]
        execution.save()
        return execution

    # ─────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────────────────

    def _fail_execution(self, execution, step, log_entry: Dict, error_msg: str):
        """Mark execution as failed with error details."""
        log_entry.update({
            'status': 'failed',
            'error': error_msg,
            'timestamp': _now_iso(),
        })
        self._update_log_entry(execution, log_entry)
        execution.status = 'failed'
        execution.ended_at = django_timezone.now()
        execution.save()

    def _update_log_entry(self, execution, log_entry: Dict):
        """Update a specific log entry in the execution's logs."""
        step_id = log_entry.get('step_id')
        logs = list(execution.logs)
        for i, entry in enumerate(logs):
            if entry.get('step_id') == step_id and entry.get('started_at') == log_entry.get('started_at'):
                logs[i] = log_entry
                break
        execution.logs = logs
        execution.save(update_fields=['logs'])
