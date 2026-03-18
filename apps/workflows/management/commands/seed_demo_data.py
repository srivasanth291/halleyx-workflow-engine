from django.core.management.base import BaseCommand
from apps.authentication.models import Company, User
from apps.workflows.models import Workflow
from apps.steps.models import Step
from apps.rules.models import Rule
import uuid

class Command(BaseCommand):
    help = 'Seed demo data for the Workflow Management System'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # 1. Create Company
        company, created = Company.objects.get_or_create(
            name='TCS India',
            defaults={'plan': 'pro'}
        )
        if created:
            self.stdout.write(f'Created company: {company.name}')

        # 2. Create Users
        users_to_create = [
            {'email': 'admin@tcs.com', 'first_name': 'Admin', 'last_name': 'User', 'role': 'admin', 'password': 'Admin123!'},
            {'email': 'manager@tcs.com', 'first_name': 'Manager', 'last_name': 'One', 'role': 'admin', 'password': 'Manager123!'},
            {'email': 'finance@tcs.com', 'first_name': 'Finance', 'last_name': 'Officer', 'role': 'employee', 'password': 'Finance123!'},
            {'email': 'employee@tcs.com', 'first_name': 'Rajesh', 'last_name': 'Kumar', 'role': 'employee', 'password': 'Employee123!'},
        ]

        for u_data in users_to_create:
            if not User.objects.filter(email=u_data['email']).exists():
                User.objects.create_user(
                    email=u_data['email'],
                    password=u_data['password'],
                    company=company,
                    first_name=u_data['first_name'],
                    last_name=u_data['last_name'],
                    role=u_data['role']
                )
                self.stdout.write(f"Created user: {u_data['email']} ({u_data['role']})")

        # 3. Create Sample Workflow: Expense Approval
        workflow, created = Workflow.objects.get_or_create(
            name='Expense Approval',
            company=company,
            defaults={
                'version': 1,
                'is_active': True,
                'input_schema': {
                    'fields': [
                        {'name': 'amount', 'type': 'number', 'required': True},
                        {'name': 'description', 'type': 'string', 'required': True},
                        {'name': 'department', 'type': 'string', 'required': True, 'allowed_values': ['HR', 'IT', 'Sales']},
                        {'name': 'urgent', 'type': 'boolean', 'required': False}
                    ]
                }
            }
        )
        if created:
            self.stdout.write(f'Created workflow: {workflow.name}')

            # 4. Create Steps
            # Step 1: Manager Review
            step1 = Step.objects.create(
                workflow=workflow,
                name='Manager Review',
                step_type='approval',
                order=1,
                metadata={
                    'assignee_email': 'manager@tcs.com',
                    'instructions': 'Verify the expense claim details.'
                }
            )

            # Step 2: Finance Review
            step2 = Step.objects.create(
                workflow=workflow,
                name='Finance Review',
                step_type='approval',
                order=2,
                metadata={
                    'assignee_email': 'finance@tcs.com',
                    'instructions': 'Release the funds for approved expense.'
                }
            )

            # Step 3: Notification
            step3 = Step.objects.create(
                workflow=workflow,
                name='Final Notification',
                step_type='notification',
                order=3,
                metadata={
                    'notification_channel': 'email',
                    'template': 'Your expense of {amount} has been fully approved.',
                    'recipients': ['employee@tcs.com']
                }
            )

            # Set start step
            workflow.start_step_id = step1.id
            workflow.save()

            # 5. Create Rules
            # Step 1 Rules
            Rule.objects.create(
                step=step1,
                condition='amount <= 1000',
                next_step_id=step3.id, # Small amounts skip finance
                priority=1
            )
            Rule.objects.create(
                step=step1,
                condition='DEFAULT',
                next_step_id=step2.id, # Large amounts to finance
                priority=2
            )

            # Step 2 Rules
            Rule.objects.create(
                step=step2,
                condition='DEFAULT',
                next_step_id=step3.id,
                priority=1
            )

            # Step 3 Rules (Auto-completion)
            Rule.objects.create(
                step=step3,
                condition='DEFAULT',
                next_step_id=None, # END
                priority=1
            )

            self.stdout.write('Successfully seeded Expense Approval steps and rules.')

        # 6. Create Sample Workflow: Leave Request
        leave_workflow, created = Workflow.objects.get_or_create(
            name='Leave Request',
            company=company,
            defaults={
                'version': 1,
                'is_active': True,
                'input_schema': {
                    'fields': [
                        {'name': 'leave_type', 'type': 'string', 'required': True, 'allowed_values': ['Sick', 'Vacation', 'Personal']},
                        {'name': 'start_date', 'type': 'string', 'required': True},
                        {'name': 'end_date', 'type': 'string', 'required': True},
                        {'name': 'reason', 'type': 'string', 'required': True}
                    ]
                }
            }
        )
        if created:
            self.stdout.write(f'Created workflow: {leave_workflow.name}')

            # Steps
            ls1 = Step.objects.create(
                workflow=leave_workflow,
                name='Manager Approval',
                step_type='approval',
                order=1,
                metadata={'assignee_email': 'manager@tcs.com', 'instructions': 'Review leave request.'}
            )
            ls2 = Step.objects.create(
                workflow=leave_workflow,
                name='HR Processing',
                step_type='approval',
                order=2,
                metadata={'assignee_email': 'hr@tcs.com', 'instructions': 'Update leave balance.'}
            )
            ls3 = Step.objects.create(
                workflow=leave_workflow,
                name='Final Sync',
                step_type='notification',
                order=3,
                metadata={'notification_channel': 'email', 'template': 'Your leave has been approved.'}
            )

            leave_workflow.start_step_id = ls1.id
            leave_workflow.save()

            # Rules
            # Step 1: Manager -> HR (Default)
            Rule.objects.create(step=ls1, condition='DEFAULT', next_step_id=ls2.id, priority=1)
            # Step 2: HR -> Final
            Rule.objects.create(step=ls2, condition='DEFAULT', next_step_id=ls3.id, priority=1)
            # Step 3: Final -> End
            Rule.objects.create(step=ls3, condition='DEFAULT', next_step_id=None, priority=1)

            self.stdout.write('Successfully seeded Leave Request steps and rules.')

        self.stdout.write(self.style.SUCCESS('Demo data seeding complete.'))
