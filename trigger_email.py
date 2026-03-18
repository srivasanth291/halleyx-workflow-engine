import os, django, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.authentication.models import User, Company
from apps.workflows.models import Workflow
from apps.executions.models import Execution
from apps.engine.executor import ExecutionEngine

engine = ExecutionEngine()
company = Company.objects.get(slug='techflow')
user = User.objects.get(email='employee1@techflow.com')
workflow = Workflow.objects.filter(name='Leave Request Workflow', is_active=True).first()

print(f"Starting execution for {workflow.name}")

# Start execution
execution = engine.start_execution(
    workflow_id=workflow.id,
    input_data={
        "employee_name": "Srivasanth",
        "leave_type": "Vacation",
        "days_requested": 1, # < 2 days so it skips Manager/CEO
        "reason": "Testing email demo"
    },
    user=user
)

print(f"Execution started: {execution.id}")

# The first step is Supervisor Approval
step_id = execution.current_step_id
print(f"Approving Supervisor Approval step (ID: {step_id})")

# Handle approval
engine.handle_approval_action(
    execution_id=execution.id,
    step_id=step_id,
    user=None, # system
    action='approve',
    comment='Approved for demo'
)

print("Workflow triggered. Checking for email files in 'emails/' directory...")
time.sleep(2)

