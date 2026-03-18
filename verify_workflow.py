import os
import django
import sys

# Setup Django
sys.path.append('c:\\Users\\L E N O V O\\OneDrive\\Desktop\\halleyx-workflow-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.workflows.models import Workflow
from apps.authentication.models import User
from apps.executions.models import Execution, EmailNotification, ActionToken
from apps.engine.executor import ExecutionEngine

def verify():
    print("--- Workflow Verification ---")
    
    # 1. Get Workflow
    try:
        workflow = Workflow.objects.get(name='Leave Management Request')
        print(f"Found Workflow: {workflow.name} (ID: {workflow.id})")
    except Workflow.DoesNotExist:
        print("Workflow NOT FOUND. Run create_leave_workflow first.")
        return

    # 2. Get Worker
    try:
        worker = User.objects.get(email='kts.worker1@example.com')
        print(f"Executing as worker: {worker.email}")
    except User.DoesNotExist:
        print("Worker NOT FOUND. Run create_kts_data first.")
        return

    # 3. Trigger Execution
    engine = ExecutionEngine()
    data = {
        "leave_type": "Vacation",
        "start_date": "2026-04-01",
        "end_date": "2026-04-10",
        "reason": "Annual family trip"
    }
    
    execution = engine.start_execution(workflow.id, data, user=worker)
    print(f"Execution started! ID: {execution.id}")
    print(f"Status: {execution.status}")
    print(f"Assigned to: {execution.assigned_to}")
    
    # 4. Check for Notification and Action Tokens
    notifications = EmailNotification.objects.filter(execution=execution)
    print(f"Notifications generated: {notifications.count()}")
    for n in notifications:
        print(f"  To: {n.recipient}")
        print(f"  Subject: {n.subject}")
        # Check if body contains tokens
        if "Direct Actions:" in n.body:
            print("  [OK] Email contains Direct Action links.")
        else:
            print("  [ERROR] Email missing action links.")

    tokens = ActionToken.objects.filter(execution=execution)
    print(f"Action tokens generated: {tokens.count()}")
    for t in tokens:
        print(f"  Token: {t.id} (Action: {t.action})")

    if execution.assigned_to == 'kts.supervisor1@example.com':
        print("[OK] Task correctly assigned to supervisor.")
    else:
        print(f"[ERROR] Task assigned to {execution.assigned_to} instead of supervisor.")

if __name__ == "__main__":
    verify()
