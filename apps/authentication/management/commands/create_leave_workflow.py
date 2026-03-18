import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.models import Company
from apps.workflows.models import Workflow
from apps.steps.models import Step
from apps.rules.models import Rule

class Command(BaseCommand):
    help = 'Creates the complex Leave Request workflow for TechFlow'

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating Leave Request Workflow...")

        try:
            company = Company.objects.get(slug='techflow')
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR('TechFlow company not found. Run create_techflow_data first.'))
            return

        # Disable any old leave workflows for this company
        Workflow.objects.filter(company=company, name="Leave Request Workflow").update(is_active=False)

        workflow = Workflow.objects.create(
            company=company,
            name="Leave Request Workflow",
            version=1,
            is_active=True,
            input_schema={
                "fields": [
                    {"name": "employee_name", "type": "string", "required": True},
                    {"name": "leave_type", "type": "string", "required": True, "allowed_values": ["Sick", "Vacation", "Unpaid", "Emergency"]},
                    {"name": "days_requested", "type": "number", "required": True},
                    {"name": "reason", "type": "string", "required": True}
                ]
            }
        )

        # ---------------------------------------------------------------------
        # Create Steps
        # ---------------------------------------------------------------------
        
        # Step 1: Supervisor Approval
        step_supervisor = Step.objects.create(
            workflow=workflow,
            name="Supervisor Approval",
            step_type="approval",
            order=1,
            metadata={"assignee_email": "supervisor1@techflow.com"}
        )

        # Step 2: Manager Approval
        step_manager = Step.objects.create(
            workflow=workflow,
            name="Manager Approval",
            step_type="approval",
            order=2,
            metadata={"assignee_email": "manager1@techflow.com"}
        )

        # Step 3: CEO Approval
        step_ceo = Step.objects.create(
            workflow=workflow,
            name="CEO Approval",
            step_type="approval",
            order=3,
            metadata={"assignee_email": "ceo@techflow.com"}
        )

        # Step 4: HR Processing (Final Approval Route)
        step_hr = Step.objects.create(
            workflow=workflow,
            name="HR Processing (Approved)",
            step_type="task",
            order=4,
            metadata={"instructions": "Please deduct the PTO balance for this approved leave and notify the team."}
        )

        # Step 5: Notification - Approved
        step_notify_approved = Step.objects.create(
            workflow=workflow,
            name="Notify Employee - Approved",
            step_type="notification",
            order=5,
            metadata={
                "channel": "email",
                "subject": "Leave Approved: {days_requested} days",
                "template": "Hi {employee_name}, your request for {days_requested} days of {leave_type} leave has been APPROVED by management.",
                "recipients": ["employee1@techflow.com"] 
            }
        )

        # Step 6: Notification - Rejected
        step_notify_rejected = Step.objects.create(
            workflow=workflow,
            name="Notify Employee - Rejected",
            step_type="notification",
            order=6,
            metadata={
                "channel": "email",
                "subject": "Leave Request Rejected",
                "template": "Hi {employee_name}, unfortunately your request for {days_requested} days of {leave_type} leave has been REJECTED. Please contact your supervisor for details.",
                "recipients": ["employee1@techflow.com"] 
            }
        )

        # Set Start Step
        workflow.start_step_id = step_supervisor.id
        workflow.save()

        # ---------------------------------------------------------------------
        # Logic Rules & Branching
        # ---------------------------------------------------------------------
        
        # In Halleyx engine, approvals automatically create a 'sys_status' variable in data.
        # If rejected, it sets sys_status='rejected'. So we can route based on that!
        
        # -------------------------
        # Supervisor Rules
        # -------------------------
        # If Rejected by supervisor -> Go to Rejected Email
        Rule.objects.create(step=step_supervisor, condition="action == 'reject'", next_step_id=step_notify_rejected.id, priority=1)
        # If Approved AND days > 2 -> Go to Manager
        Rule.objects.create(step=step_supervisor, condition="days_requested > 2", next_step_id=step_manager.id, priority=2)
        # If Approved AND days <= 2 -> Skip directly to HR
        Rule.objects.create(step=step_supervisor, condition="DEFAULT", next_step_id=step_hr.id, priority=3)

        # -------------------------
        # Manager Rules
        # -------------------------
        # If Rejected by manager -> Go to Rejected Email
        Rule.objects.create(step=step_manager, condition="action == 'reject'", next_step_id=step_notify_rejected.id, priority=1)
        # If Approved AND days > 5 -> Go to CEO
        Rule.objects.create(step=step_manager, condition="days_requested > 5", next_step_id=step_ceo.id, priority=2)
        # If Approved AND days <= 5 -> Skip to HR
        Rule.objects.create(step=step_manager, condition="DEFAULT", next_step_id=step_hr.id, priority=3)

        # -------------------------
        # CEO Rules
        # -------------------------
        # If Rejected by CEO -> Go to Rejected Email
        Rule.objects.create(step=step_ceo, condition="action == 'reject'", next_step_id=step_notify_rejected.id, priority=1)
        # If Approved by CEO -> Go to HR
        Rule.objects.create(step=step_ceo, condition="DEFAULT", next_step_id=step_hr.id, priority=2)


        # -------------------------
        # HR Step Rules
        # -------------------------
        # HR task finished -> Send Approved Email
        Rule.objects.create(step=step_hr, condition="DEFAULT", next_step_id=step_notify_approved.id, priority=1)

        # Notifications are Terminal (No rules), workflow ENDS.

        self.stdout.write(self.style.SUCCESS('Leave Request Workflow generated successfully with full rejection & limits logic!'))
