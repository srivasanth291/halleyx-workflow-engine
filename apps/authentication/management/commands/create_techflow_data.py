import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.models import Company, Role
from apps.workflows.models import Workflow
from apps.steps.models import Step
from apps.rules.models import Rule

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates TechFlow company, employees, and Expense Tracker workflow'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting TechFlow data generation...")

        company, created = Company.objects.get_or_create(
            name="TechFlow Inc",
            defaults={
                'slug': 'techflow',
                'plan': 'enterprise',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Created company TechFlow Inc'))
        else:
            self.stdout.write('Company TechFlow Inc already exists. Cleaning up users...')

        # Roles
        admin_role, _ = Role.objects.get_or_create(company=company, name='Admin', defaults={'is_admin': True})
        ceo_role, _ = Role.objects.get_or_create(company=company, name='CEO', defaults={'is_admin': False})
        manager_role, _ = Role.objects.get_or_create(company=company, name='Manager', defaults={'is_admin': False})
        supervisor_role, _ = Role.objects.get_or_create(company=company, name='Supervisor', defaults={'is_admin': False})
        employee_role, _ = Role.objects.get_or_create(company=company, name='Employee', defaults={'is_admin': False})

        # Delete existing techflow users
        User.objects.filter(email__endswith='@techflow.com').delete()

        password = "Pass123!"

        users_to_create = [
            {'email': 'admin@techflow.com', 'first': 'Tech', 'last': 'Admin', 'role': admin_role},
            {'email': 'ceo@techflow.com', 'first': 'Alice', 'last': 'CEO', 'role': ceo_role},
            {'email': 'manager1@techflow.com', 'first': 'Bob', 'last': 'Manager', 'role': manager_role},
            {'email': 'manager2@techflow.com', 'first': 'Charlie', 'last': 'Manager', 'role': manager_role},
            {'email': 'supervisor1@techflow.com', 'first': 'Dave', 'last': 'Supervisor', 'role': supervisor_role},
            {'email': 'supervisor2@techflow.com', 'first': 'Eve', 'last': 'Supervisor', 'role': supervisor_role},
            {'email': 'supervisor3@techflow.com', 'first': 'Frank', 'last': 'Supervisor', 'role': supervisor_role},
        ]

        for i in range(1, 41):
            users_to_create.append({
                'email': f'employee{i}@techflow.com',
                'first': 'Employee',
                'last': str(i),
                'role': employee_role
            })

        for u in users_to_create:
            user = User.objects.create_user(
                email=u['email'],
                password=password,
                first_name=u['first'],
                last_name=u['last'],
                role=u['role'],
                company=company
            )
            user.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(users_to_create)} users for TechFlow.'))

        # ---------------------------------------------------------------------
        # Create Expense Tracker Workflow
        # ---------------------------------------------------------------------
        # Disable any old expense workflows for this company
        Workflow.objects.filter(company=company, name="Expense Tracker").update(is_active=False)

        workflow = Workflow.objects.create(
            company=company,
            name="Expense Tracker",
            version=1,
            is_active=True,
            input_schema={
                "fields": [
                    {"name": "amount", "type": "number", "required": True},
                    {"name": "category", "type": "string", "required": True, "allowed_values": ["Travel", "Meals", "Office Supplies", "Software"]},
                    {"name": "description", "type": "string", "required": True}
                ]
            }
        )

        # Step 1: Supervisor Approval
        step1 = Step.objects.create(
            workflow=workflow,
            name="Supervisor Approval",
            step_type="approval",
            order=1,
            metadata={
                "assignee_email": "supervisor1@techflow.com", # Defaulting to sup 1 for demo
                "timeout_hours": 24,
                "on_timeout": "escalate",
                "escalate_to": "manager1@techflow.com"
            }
        )

        # Step 2: Manager Approval
        step2 = Step.objects.create(
            workflow=workflow,
            name="Manager Approval",
            step_type="approval",
            order=2,
            metadata={
                "assignee_email": "manager1@techflow.com",
                "timeout_hours": 48,
                "on_timeout": "escalate",
                "escalate_to": "ceo@techflow.com"
            }
        )

        # Step 3: CEO Approval
        step3 = Step.objects.create(
            workflow=workflow,
            name="CEO Approval",
            step_type="approval",
            order=3,
            metadata={
                "assignee_email": "ceo@techflow.com"
            }
        )

        # Step 4: Finance Processing
        step4 = Step.objects.create(
            workflow=workflow,
            name="Finance Processing",
            step_type="task",
            order=4,
            metadata={
                "instructions": "Please process the approved expense and initiate wire/ACH transfer. Verify receipts before executing transfer."
            }
        )

        # Step 5: Employee Notification
        step5 = Step.objects.create(
            workflow=workflow,
            name="Approval Notification",
            step_type="notification",
            order=5,
            metadata={
                "channel": "email",
                "subject": "Expense Approved: {category}",
                "template": "Your expense request for {amount} ({description}) has been fully approved and is being processed by Finance.",
                "recipients": ["employee1@techflow.com"] # In a real app this would use a dynamic variable
            }
        )

        # Set Start Step
        workflow.start_step_id = step1.id
        workflow.save()

        # ---------------------------------------------------------------------
        # Logic Rules
        # ---------------------------------------------------------------------
        # Step 1 -> If amount > 500 go to Manager, else Finance
        Rule.objects.create(step=step1, condition="amount > 500", next_step_id=step2.id, priority=1)
        Rule.objects.create(step=step1, condition="DEFAULT", next_step_id=step4.id, priority=2)

        # Step 2 -> If amount > 5000 go to CEO, else Finance
        Rule.objects.create(step=step2, condition="amount > 5000", next_step_id=step3.id, priority=1)
        Rule.objects.create(step=step2, condition="DEFAULT", next_step_id=step4.id, priority=2)

        # Step 3 -> CEO goes to Finance
        Rule.objects.create(step=step3, condition="DEFAULT", next_step_id=step4.id, priority=1)

        # Step 4 -> Finance goes to Notification
        Rule.objects.create(step=step4, condition="DEFAULT", next_step_id=step5.id, priority=1)

        # Step 5 -> End (no rules)

        self.stdout.write(self.style.SUCCESS('Expense Tracker Workflow created successfully!'))
