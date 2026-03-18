import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from apps.executions.models import Execution
from apps.steps.models import Step
exec = Execution.objects.order_by('-started_at').first()
print(f'ID: {exec.id}, Status: {exec.status}')
for log in exec.logs:
    step_id = log.get('step_id')
    step_name = 'System'
    if step_id:
        try:
            step_name = Step.objects.get(id=step_id).name
        except Step.DoesNotExist:
            step_name = f'Unknown Step {step_id}'
    print(f"-- Log: {log.get('status')} on step {step_name}")
