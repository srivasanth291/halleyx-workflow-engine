"""
Management command to create sample data for Halleyx Workflow backend.
Run: python manage.py create_sample_data
"""
import uuid
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Create sample data: company, users, workflows, steps, rules, executions'

    def handle(self, *args, **options):
        from apps.authentication.models import Company, User
        from apps.workflows.models import Workflow
        from apps.steps.models import Step
        from apps.rules.models import Rule
        from apps.executions.models import Execution

        self.stdout.write('Creating sample data...')

        # ── 1. COMPANY ──────────────────────────────────────
        company, _ = Company.objects.get_or_create(
            slug='tcs-india',
            defaults={'name': 'TCS India', 'plan': 'pro'},
        )
        self.stdout.write(f'✅ Company: {company.name}')

        # ── 2. USERS ─────────────────────────────────────────
        users = {}
        user_data = [
            ('admin@tcs.com', 'Admin123!', 'Admin', 'User', 'admin'),
            ('manager@tcs.com', 'Manager123!', 'Manager', 'User', 'employee'),
            ('employee@tcs.com', 'Employee123!', 'Employee', 'User', 'employee'),
            ('director@tcs.com', 'Director123!', 'Director', 'User', 'employee'),
        ]
        for email, password, first, last, role in user_data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'company': company,
                    'first_name': first,
                    'last_name': last,
                    'role': role,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            users[email] = user
            self.stdout.write(f'✅ User: {email} ({role})')

        # ── 3. WORKFLOW 1: EXPENSE APPROVAL ─────────────────
        wf1_name = 'Expense Approval'
        Workflow.objects.filter(company=company, name=wf1_name).update(is_active=False)
        wf1 = Workflow.objects.create(
            company=company,
            name=wf1_name,
            version=1,
            is_active=True,
            input_schema={
                'fields': [
                    {'name': 'amount', 'type': 'number', 'required': True, 'allowed_values': []},
                    {'name': 'country', 'type': 'string', 'required': True, 'allowed_values': ['US', 'UK', 'IN']},
                    {'name': 'priority', 'type': 'string', 'required': True, 'allowed_values': ['High', 'Medium', 'Low']},
                ]
            },
        )
        self.stdout.write(f'✅ Workflow: {wf1}')

        # Step 1: Manager Approval
        s1 = Step.objects.create(
            workflow=wf1, name='Manager Approval', step_type='approval', order=1,
            metadata={
                'assignee_email': 'manager@tcs.com',
                'instructions': 'Review expense carefully',
                'timeout_hours': 24,
                'on_timeout': 'escalate',
                'escalate_to': 'director@tcs.com',
            },
        )
        # Step 2: CEO Approval
        s2 = Step.objects.create(
            workflow=wf1, name='CEO Approval', step_type='approval', order=2,
            metadata={
                'assignee_email': 'director@tcs.com',
                'timeout_hours': 48,
                'on_timeout': 'auto_approve',
            },
        )
        # Step 3: Finance Notify
        s3 = Step.objects.create(
            workflow=wf1, name='Finance Notify', step_type='notification', order=3,
            metadata={
                'notification_channel': 'email',
                'template': 'Expense of {amount} from {country} has been approved!',
                'recipients': ['finance@tcs.com'],
            },
        )
        # Step 4: Task Rejection
        s4 = Step.objects.create(
            workflow=wf1, name='Task Rejection', step_type='task', order=4,
            metadata={'instructions': 'Mark expense as rejected in system'},
        )

        # Rules for Step 1: Manager Approval
        Rule.objects.create(step=s1, condition="amount > 100 && country == 'US' && priority == 'High'", next_step_id=s2.id, priority=1)
        Rule.objects.create(step=s1, condition='amount <= 100', next_step_id=None, priority=2)
        Rule.objects.create(step=s1, condition='DEFAULT', next_step_id=s4.id, priority=3)

        # Rules for Step 2: CEO Approval
        Rule.objects.create(step=s2, condition='approved == true', next_step_id=s3.id, priority=1)
        Rule.objects.create(step=s2, condition='DEFAULT', next_step_id=s4.id, priority=2)

        # Rules for Step 3: Finance Notify
        Rule.objects.create(step=s3, condition='DEFAULT', next_step_id=None, priority=1)

        # Rules for Step 4: Task Rejection
        Rule.objects.create(step=s4, condition='DEFAULT', next_step_id=None, priority=1)

        # Set start step
        wf1.start_step_id = s1.id
        wf1.save(update_fields=['start_step_id'])
        self.stdout.write(f'✅ Steps and rules created for {wf1}')

        # ── 4. WORKFLOW 2: EMPLOYEE ONBOARDING ──────────────
        wf2_name = 'Employee Onboarding'
        Workflow.objects.filter(company=company, name=wf2_name).update(is_active=False)
        wf2 = Workflow.objects.create(
            company=company,
            name=wf2_name,
            version=1,
            is_active=True,
            input_schema={
                'fields': [
                    {'name': 'employee_name', 'type': 'string', 'required': True, 'allowed_values': []},
                    {'name': 'department', 'type': 'string', 'required': True, 'allowed_values': ['Engineering', 'HR', 'Finance', 'Sales']},
                    {'name': 'joining_date', 'type': 'string', 'required': True, 'allowed_values': []},
                ]
            },
        )

        # Onboarding Steps
        ob1 = Step.objects.create(
            workflow=wf2, name='HR Verification', step_type='approval', order=1,
            metadata={
                'assignee_email': 'admin@tcs.com',
                'instructions': 'Verify documents',
                'timeout_hours': 24,
                'on_timeout': 'escalate',
                'escalate_to': 'admin@tcs.com',
            },
        )
        ob2 = Step.objects.create(
            workflow=wf2, name='IT Setup', step_type='task', order=2,
            metadata={'instructions': 'Create accounts and assign equipment'},
        )
        ob3 = Step.objects.create(
            workflow=wf2, name='Welcome Notification', step_type='notification', order=3,
            metadata={
                'notification_channel': 'email',
                'template': 'Welcome {employee_name} to {department} team!',
                'recipients': ['admin@tcs.com'],
            },
        )

        # Onboarding Rules
        Rule.objects.create(step=ob1, condition="department == 'Engineering'", next_step_id=ob2.id, priority=1)
        Rule.objects.create(step=ob1, condition='DEFAULT', next_step_id=ob3.id, priority=2)
        Rule.objects.create(step=ob2, condition='DEFAULT', next_step_id=ob3.id, priority=1)
        Rule.objects.create(step=ob3, condition='DEFAULT', next_step_id=None, priority=1)

        wf2.start_step_id = ob1.id
        wf2.save(update_fields=['start_step_id'])
        self.stdout.write(f'✅ Steps and rules created for {wf2}')

        # ── 5. SAMPLE EXECUTIONS ─────────────────────────────
        # Execution 1: Expense Approval - FAILED (timeout)
        ex1_logs = [
            {
                'step_id': str(s1.id),
                'step_name': 'Manager Approval',
                'step_type': 'approval',
                'status': 'pending_approval',
                'started_at': '2026-02-18T10:15:23Z',
                'action_by': None,
                'action_at': None,
                'comment': 'Waiting for approval from manager@tcs.com',
                'rule_matched': None,
                'next_step_id': None,
                'next_step_name': None,
                'duration_seconds': None,
                'rule_evaluation_log': [],
            },
            {
                'type': 'timeout_failure',
                'step_id': str(s1.id),
                'step_name': 'Manager Approval',
                'error': 'Timeout: No action taken within 24 hours.',
                'timestamp': '2026-02-19T10:15:23Z',
            },
        ]
        ex1 = Execution.objects.create(
            workflow=wf1,
            workflow_version=1,
            status='failed',
            data={'amount': 5000, 'country': 'US', 'priority': 'High'},
            triggered_by=users['employee@tcs.com'],
            current_step_id=s1.id,
            logs=ex1_logs,
            max_iterations=10,
            iteration_count=1,
            ended_at=datetime(2026, 2, 19, 10, 15, 23, tzinfo=timezone.utc),
        )
        self.stdout.write(f'✅ Execution 1 (failed): {ex1.id}')

        # Execution 2: Employee Onboarding - COMPLETED
        ex2_logs = [
            {
                'step_id': str(ob1.id),
                'step_name': 'HR Verification',
                'step_type': 'approval',
                'status': 'approve',
                'started_at': '2026-02-18T11:00:00Z',
                'action_by': 'admin@tcs.com',
                'action_at': '2026-02-18T11:02:00Z',
                'comment': 'Documents verified',
                'rule_matched': "department == 'Engineering'",
                'next_step_id': str(ob2.id),
                'next_step_name': 'IT Setup',
                'duration_seconds': 120,
                'rule_evaluation_log': [
                    {'rule_id': 'placeholder', 'priority': 1, 'condition': "department == 'Engineering'", 'result': True, 'error': None},
                ],
            },
            {
                'step_id': str(ob2.id),
                'step_name': 'IT Setup',
                'step_type': 'task',
                'status': 'completed',
                'started_at': '2026-02-18T11:02:00Z',
                'action_by': 'system',
                'action_at': '2026-02-18T11:02:05Z',
                'comment': None,
                'rule_matched': 'DEFAULT',
                'next_step_id': str(ob3.id),
                'next_step_name': 'Welcome Notification',
                'duration_seconds': 5,
                'rule_evaluation_log': [
                    {'priority': 1, 'condition': 'DEFAULT', 'result': True, 'error': None},
                ],
            },
            {
                'step_id': str(ob3.id),
                'step_name': 'Welcome Notification',
                'step_type': 'notification',
                'status': 'completed',
                'started_at': '2026-02-18T11:02:05Z',
                'action_by': 'system',
                'action_at': '2026-02-18T11:02:10Z',
                'comment': None,
                'rule_matched': 'DEFAULT',
                'next_step_id': None,
                'next_step_name': None,
                'duration_seconds': 5,
                'rule_evaluation_log': [
                    {'priority': 1, 'condition': 'DEFAULT', 'result': True, 'error': None},
                ],
            },
        ]
        ex2 = Execution.objects.create(
            workflow=wf2,
            workflow_version=1,
            status='completed',
            data={'employee_name': 'Priya Kumar', 'department': 'Engineering', 'joining_date': '2026-02-18'},
            triggered_by=users['admin@tcs.com'],
            current_step_id=None,
            logs=ex2_logs,
            max_iterations=10,
            iteration_count=3,
            ended_at=datetime(2026, 2, 18, 11, 5, 0, tzinfo=timezone.utc),
        )
        self.stdout.write(f'✅ Execution 2 (completed): {ex2.id}')

        self.stdout.write(self.style.SUCCESS('\n🎉 Sample data created successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin:    admin@tcs.com    / Admin123!')
        self.stdout.write('  Manager:  manager@tcs.com  / Manager123!')
        self.stdout.write('  Employee: employee@tcs.com / Employee123!')
        self.stdout.write('  Director: director@tcs.com / Director123!')
