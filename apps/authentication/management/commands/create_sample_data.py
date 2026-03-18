import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.authentication.models import Company
from django.contrib.auth import get_user_model
from apps.workflows.models import Workflow
from apps.steps.models import Step
from apps.rules.models import Rule
from apps.executions.models import Execution, EmailNotification

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for Halleyx Workflow Management System'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating sample data...")

        company, _ = Company.objects.get_or_create(
            name="TCS India",
            defaults={'plan': 'pro'}
        )

        users_data = [
            {'email': 'superadmin@tcs.com', 'pwd': 'SuperAdmin123!', 'role': 'super_admin'},
            {'email': 'admin@tcs.com', 'pwd': 'Admin123!', 'role': 'admin'},
            {'email': 'manager@tcs.com', 'pwd': 'Manager123!', 'role': 'employee'},
            {'email': 'employee@tcs.com', 'pwd': 'Employee123!', 'role': 'employee'},
            {'email': 'director@tcs.com', 'pwd': 'Director123!', 'role': 'employee'},
        ]
        
        for u in users_data:
            if not User.objects.filter(email=u['email']).exists():
                user = User.objects.create_user(
                    email=u['email'],
                    password=u['pwd'],
                    role=u['role'],
                    company=company
                )
                if u['role'] == 'super_admin':
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()

        admin_user = User.objects.get(email='admin@tcs.com')

        wf1, created = Workflow.objects.get_or_create(
            name="Expense Approval",
            company=company,
            defaults={
                'version': 3,
                'input_schema': {
                    "fields": [
                        {"name": "amount", "type": "number", "required": True},
                        {"name": "country", "type": "string", "required": True, "allowed_values": ["US", "UK", "IN"]},
                        {"name": "priority", "type": "string", "required": True, "allowed_values": ["High", "Medium", "Low"]}
                    ]
                }
            }
        )

        if created:
            s1 = Step.objects.create(workflow=wf1, name="Manager Approval", step_type="approval", order=1, metadata={
                "assignee_email": "manager@tcs.com", "timeout_hours": 24, "on_timeout": "escalate", "escalate_to": "director@tcs.com"
            })
            s2 = Step.objects.create(workflow=wf1, name="CEO Approval", step_type="approval", order=2, metadata={
                "assignee_email": "director@tcs.com", "timeout_hours": 48, "on_timeout": "auto_approve"
            })
            s3 = Step.objects.create(workflow=wf1, name="Finance Notify", step_type="notification", order=3, metadata={
                "channel": "email", "subject": "Expense Approved!", "template": "Expense of {amount} from {country} has been approved!", "recipients": ["finance@tcs.com"]
            })
            s4 = Step.objects.create(workflow=wf1, name="Task Rejection", step_type="task", order=4, metadata={
                "instructions": "Mark expense as rejected"
            })

            Rule.objects.create(step=s1, condition="amount>100 && country=='US' && priority=='High'", next_step_id=s2.id, priority=1)
            Rule.objects.create(step=s1, condition="amount<=100", next_step_id=s3.id, priority=2)
            Rule.objects.create(step=s1, condition="DEFAULT", next_step_id=s4.id, priority=3)

            Rule.objects.create(step=s2, condition="approved==true", next_step_id=s3.id, priority=1)
            Rule.objects.create(step=s2, condition="DEFAULT", next_step_id=s4.id, priority=2)

            Rule.objects.create(step=s3, condition="DEFAULT", next_step_id=None, priority=1)
            Rule.objects.create(step=s4, condition="DEFAULT", next_step_id=None, priority=1)

            wf1.start_step_id = s1.id
            wf1.save()

            Execution.objects.create(
                workflow=wf1, company=company, workflow_version=3, status='failed',
                data={"amount": 5000, "country": "US", "priority": "High"},
                triggered_by=admin_user, iteration_count=1, max_iterations=10,
                logs=[{"status": "failed", "error": "timeout failure"}],
                started_at=timezone.now() - timezone.timedelta(minutes=5),
                ended_at=timezone.now()
            )

        wf2, created = Workflow.objects.get_or_create(
            name="Employee Onboarding",
            company=company,
            defaults={
                'version': 1,
                'input_schema': {
                    "fields": [
                        {"name": "employee_name", "type": "string", "required": True},
                        {"name": "department", "type": "string", "required": True, "allowed_values": ["Engineering", "HR", "Finance", "Sales"]},
                        {"name": "joining_date", "type": "string", "required": True}
                    ]
                }
            }
        )

        if created:
            w2s1 = Step.objects.create(workflow=wf2, name="HR Verification", step_type="approval", order=1, metadata={
                "assignee_email": "admin@tcs.com", "timeout_hours": 24
            })
            w2s2 = Step.objects.create(workflow=wf2, name="IT Setup", step_type="task", order=2, metadata={
                "instructions": "Create accounts, assign laptop"
            })
            w2s3 = Step.objects.create(workflow=wf2, name="Welcome Notification", step_type="notification", order=3, metadata={
                "channel": "email", "subject": "Welcome to TCS!", "template": "Welcome {employee_name} to the {department} team!", "recipients": ["admin@tcs.com"]
            })

            Rule.objects.create(step=w2s1, condition="department=='Engineering'", next_step_id=w2s2.id, priority=1)
            Rule.objects.create(step=w2s1, condition="DEFAULT", next_step_id=w2s3.id, priority=2)

            Rule.objects.create(step=w2s2, condition="DEFAULT", next_step_id=w2s3.id, priority=1)
            Rule.objects.create(step=w2s3, condition="DEFAULT", next_step_id=None, priority=1)

            wf2.start_step_id = w2s1.id
            wf2.save()

            Execution.objects.create(
                workflow=wf2, company=company, workflow_version=1, status='completed',
                data={"employee_name": "John Doe", "department": "Engineering", "joining_date": "2026-03-01"},
                triggered_by=admin_user, iteration_count=3, max_iterations=10,
                logs=[{"status": "completed", "info": "All steps completed"}],
                started_at=timezone.now() - timezone.timedelta(minutes=5),
                ended_at=timezone.now()
            )

        if not EmailNotification.objects.filter(company=company).exists():
            EmailNotification.objects.create(company=company, recipient="admin@tcs.com", subject="Welcome to TCS!", body="Welcome John Doe to the Engineering team!", channel="email", status="sent", sent_at=timezone.now())
            EmailNotification.objects.create(company=company, recipient="finance@tcs.com", subject="Expense Approved!", body="Expense of 5000 from US has been approved!", channel="email", status="sent", sent_at=timezone.now())

        self.stdout.write(self.style.SUCCESS("Sample data created successfully."))
