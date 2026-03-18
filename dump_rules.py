import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from apps.workflows.models import Workflow
from apps.steps.models import Step
wf = Workflow.objects.filter(name='Leave Request Workflow').order_by('-created_at').first()

with open('rules_output.txt', 'w') as f:
    f.write(f'Workflow: {wf.name}\n')
    for step in wf.steps.all().order_by('order'):
        f.write(f'Step {step.order}: {step.name}\n')
        for rule in step.rules.all().order_by('priority'):
            if rule.next_step_id:
                try:
                    next_step_name = Step.objects.get(id=rule.next_step_id).name
                except Step.DoesNotExist:
                    next_step_name = 'Unknown Step ID'
            else:
                next_step_name = 'None'
            f.write(f'  - Rule: {rule.condition} -> {next_step_name}\n')
