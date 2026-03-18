import traceback
from django.utils import timezone
from apps.workflows.models import Workflow
from apps.executions.models import Execution
from apps.steps.models import Step
from apps.engine.rule_engine import RuleEngine, WorkflowTerminationException, MaxIterationsException
from apps.executions.tasks import send_notification_task, check_step_timeout
from rest_framework.exceptions import ValidationError

class ExecutionEngine:
    def start_execution(self, workflow_id, input_data, user, max_iterations=10):
        try:
            workflow = Workflow.objects.get(id=workflow_id, is_active=True, company=user.company)
        except Workflow.DoesNotExist:
            raise ValidationError("Active workflow not found.")

        self._validate_input_schema(workflow.input_schema, input_data)

        if not workflow.start_step_id:
            raise ValidationError("Workflow start_step_id is not set.")

        try:
            start_step = Step.objects.get(id=workflow.start_step_id, workflow=workflow)
        except Step.DoesNotExist:
            raise ValidationError("Start step does not exist.")

        execution = Execution.objects.create(
            workflow=workflow,
            company=workflow.company,
            workflow_version=workflow.version,
            status='pending',
            data=input_data,
            triggered_by=user,
            max_iterations=max_iterations,
        )

        execution.status = 'in_progress'
        execution.save()

        return self.process_step(execution, start_step)

    def _validate_input_schema(self, schema, data):
        fields = schema.get('fields', [])
        for field in fields:
            name = field.get('name')
            f_type = field.get('type')
            required = field.get('required', False)
            allowed = field.get('allowed_values', [])

            if required and name not in data:
                raise ValidationError({"detail": f"Field {name} is required."})
                
            if name in data:
                val = data[name]
                if f_type == 'number' and not isinstance(val, (int, float)):
                    raise ValidationError({"detail": f"Field {name} must be a number."})
                if f_type == 'string' and not isinstance(val, str):
                    raise ValidationError({"detail": f"Field {name} must be a string."})
                if f_type == 'boolean' and not isinstance(val, bool):
                    raise ValidationError({"detail": f"Field {name} must be a boolean."})
                
                if allowed and val not in allowed:
                    raise ValidationError({"detail": f"Field {name} has invalid value. Allowed: {allowed}"})

    def process_step(self, execution, step):
        execution.iteration_count += 1
        execution.current_step_id = step.id
        execution.save()

        if execution.iteration_count > execution.max_iterations:
            execution.status = 'failed'
            execution.logs.append({
                "step_id": str(step.id),
                "step_name": step.name,
                "error": "Max iterations exceeded",
                "terminated_at_step": step.name
            })
            execution.ended_at = timezone.now()
            execution.save()
            raise MaxIterationsException("Max iterations exceeded")

        now_str = timezone.now().isoformat()
        log_entry = {
            "step_id": str(step.id),
            "step_name": step.name,
            "step_type": step.step_type,
            "status": "started",
            "started_at": now_str
        }
        
        # Avoid saving directly if we modify logs, we'll save at logic end or during modifications
        temp_logs = execution.logs
        temp_logs.append(log_entry)
        execution.logs = temp_logs
        execution.save(update_fields=['logs', 'current_step_id', 'iteration_count'])

        try:
            if step.step_type == 'task':
                return self._process_task(execution, step)
            elif step.step_type == 'notification':
                return self._process_notification(execution, step)
            elif step.step_type == 'approval':
                return self._process_approval(execution, step)
        except WorkflowTerminationException as e:
            execution.status = 'completed'
            execution.ended_at = timezone.now()
            
            temp_logs = execution.logs
            temp_logs.append({
                "step_id": str(step.id),
                "step_name": step.name,
                "status": "completed",
                "info": "Workflow terminated normally."
            })
            execution.logs = temp_logs
            execution.save()
            return execution
        except Exception as e:
            execution.status = 'failed'
            execution.ended_at = timezone.now()
            
            temp_logs = execution.logs
            temp_logs.append({
                "step_id": str(step.id),
                "step_name": step.name,
                "status": "failed",
                "error": str(e)
            })
            execution.logs = temp_logs
            execution.save()
            return execution

    def _evaluate_rules(self, execution, step, eval_data=None):
        engine = RuleEngine()
        data_to_eval = eval_data if eval_data else execution.data
        return engine.evaluate(step.rules.all(), data_to_eval)

    def _process_task(self, execution, step):
        result = self._evaluate_rules(execution, step)
        
        temp_logs = execution.logs
        temp_logs.append({
            "step_id": str(step.id),
            "step_name": step.name,
            "status": "completed",
            "rule_matched": result['matched_condition'],
            "next_step_id": result['next_step_id'],
            "rule_evaluation_log": result['evaluation_log']
        })
        execution.logs = temp_logs
        execution.save(update_fields=['logs'])

        if not result['next_step_id']:
            execution.status = 'completed'
            execution.ended_at = timezone.now()
            execution.save()
            return execution

        next_step = Step.objects.get(id=result['next_step_id'])
        return self.process_step(execution, next_step)

    def _process_notification(self, execution, step):
        metadata = step.metadata
        channel = metadata.get('notification_channel', metadata.get('channel', 'email'))
        subject = metadata.get('subject', 'Workflow Notification')
        template = metadata.get('template', '')
        recipients = metadata.get('recipients', [])

        send_notification_task.delay(
            execution.id, step.id, channel, template, recipients, execution.data, subject, execution.company.id
        )

        result = self._evaluate_rules(execution, step)
        
        temp_logs = execution.logs
        temp_logs.append({
            "step_id": str(step.id),
            "step_name": step.name,
            "status": "completed",
            "rule_matched": result['matched_condition'],
            "next_step_id": result['next_step_id'],
            "rule_evaluation_log": result['evaluation_log']
        })
        execution.logs = temp_logs
        execution.save(update_fields=['logs'])

        if not result['next_step_id']:
            execution.status = 'completed'
            execution.ended_at = timezone.now()
            execution.save()
            return execution

        next_step = Step.objects.get(id=result['next_step_id'])
        return self.process_step(execution, next_step)

    def _process_approval(self, execution, step):
        assignee_email = step.metadata.get('assignee_email')
        timeout_hours = int(step.metadata.get('timeout_hours', 24))

        temp_logs = execution.logs
        temp_logs.append({
            "step_id": str(step.id),
            "step_name": step.name,
            "status": "pending_approval",
            "comment": f"Waiting for {assignee_email}",
            "action_at": timezone.now().isoformat()
        })
        execution.logs = temp_logs
        execution.assigned_to = assignee_email
        execution.save(update_fields=['logs', 'assigned_to'])

        check_step_timeout.apply_async(
            args=[execution.id, step.id],
            countdown=timeout_hours * 3600
        )
        return execution

    def handle_approval_action(self, execution_id, step_id, user, action, comment):
        execution = Execution.objects.get(id=execution_id)
        step = Step.objects.get(id=step_id)

        # Validate user
        if user:
            assignee_email = step.metadata.get('assignee_email')
            if user.email != assignee_email and user.role not in ['super_admin', 'admin']:
                raise ValidationError("You do not have permission to approve this step.")

        # Update log
        action_by = user.email if user else "system"
        
        temp_logs = execution.logs
        temp_logs.append({
            "step_id": str(step_id),
            "step_name": step.name,
            "status": action,
            "action_by": action_by,
            "action_at": timezone.now().isoformat(),
            "comment": comment
        })
        execution.logs = temp_logs
        execution.assigned_to = None
        execution.save(update_fields=['logs', 'assigned_to'])
        
        eval_data = {
            **execution.data,
            "approved": action == 'approve',
            "rejected": action == 'reject',
            "returned": action == 'return',
            "action": action
        }

        try:
            result = self._evaluate_rules(execution, step, eval_data=eval_data)
            
            temp_logs = execution.logs
            temp_logs.append({
                "step_id": str(step_id),
                "step_name": step.name,
                "status": "completed",
                "rule_matched": result['matched_condition'],
                "next_step_id": result['next_step_id'],
                "rule_evaluation_log": result['evaluation_log']
            })
            execution.logs = temp_logs
            execution.save(update_fields=['logs'])

            if not result['next_step_id']:
                execution.status = 'completed'
                execution.ended_at = timezone.now()
                execution.save()
                return execution

            next_step = Step.objects.get(id=result['next_step_id'])
            return self.process_step(execution, next_step)
            
        except WorkflowTerminationException:
            execution.status = 'completed'
            execution.ended_at = timezone.now()
            execution.save()
            return execution
        except Exception as e:
            execution.status = 'failed'
            execution.ended_at = timezone.now()
            
            temp_logs = execution.logs
            temp_logs.append({
                "step_id": str(step.id),
                "step_name": step.name,
                "status": "failed",
                "error": str(e)
            })
            execution.logs = temp_logs
            execution.save()
            return execution

    def retry_execution(self, execution_id, user):
        execution = Execution.objects.get(id=execution_id)
        if execution.status != 'failed':
            raise ValidationError("Only failed executions can be retried.")

        execution.iteration_count = 0
        execution.retries += 1
        execution.status = 'in_progress'
        
        temp_logs = execution.logs
        temp_logs.append({
            "action": "retry",
            "action_by": user.email,
            "timestamp": timezone.now().isoformat()
        })
        execution.logs = temp_logs
        execution.save(update_fields=['logs', 'iteration_count', 'retries', 'status'])

        step = Step.objects.get(id=execution.current_step_id)
        return self.process_step(execution, step)

    def cancel_execution(self, execution_id, user):
        execution = Execution.objects.get(id=execution_id)
        if execution.status not in ['pending', 'in_progress']:
            raise ValidationError("Only pending or in_progress executions can be canceled.")

        execution.status = 'canceled'
        execution.ended_at = timezone.now()
        
        temp_logs = execution.logs
        temp_logs.append({
            "action": "canceled",
            "action_by": user.email,
            "timestamp": timezone.now().isoformat()
        })
        execution.logs = temp_logs
        execution.save()
        return execution
