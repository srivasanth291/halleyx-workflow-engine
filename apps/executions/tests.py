"""
Execution tests.
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.authentication.models import Company, User
from apps.workflows.models import Workflow
from apps.steps.models import Step
from apps.rules.models import Rule
from apps.executions.models import Execution


class ExecutionModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Corp')
        self.user = User.objects.create_user(
            email='user@test.com', password='Pass123!',
            company=self.company, first_name='Test', last_name='User',
        )

    def test_execution_status_choices(self):
        wf = Workflow.objects.create(
            company=self.company, name='Test WF', version=1,
            is_active=True, input_schema={'fields': []}
        )
        ex = Execution.objects.create(
            workflow=wf, workflow_version=1,
            status='pending', data={}, triggered_by=self.user,
        )
        self.assertEqual(ex.status, 'pending')
        self.assertEqual(ex.max_iterations, 10)
        self.assertEqual(ex.iteration_count, 0)


class ExecutionEngineTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Corp')
        self.user = User.objects.create_user(
            email='admin@test.com', password='Admin123!',
            company=self.company, first_name='Admin', last_name='User', role='admin',
        )
        self.workflow = Workflow.objects.create(
            company=self.company, name='Simple WF', version=1,
            is_active=True,
            input_schema={'fields': [
                {'name': 'amount', 'type': 'number', 'required': True, 'allowed_values': []},
            ]},
        )
        self.step = Step.objects.create(
            workflow=self.workflow, name='Task Step', step_type='task', order=1,
            metadata={'instructions': 'Do the thing'},
        )
        Rule.objects.create(
            step=self.step, condition='DEFAULT', next_step_id=None, priority=1,
        )
        self.workflow.start_step_id = self.step.id
        self.workflow.save()

    def test_start_execution_completes_task_workflow(self):
        from apps.engine.executor import ExecutionEngine
        engine = ExecutionEngine()
        execution = engine.start_execution(
            workflow_id=str(self.workflow.id),
            input_data={'amount': 500},
            user=self.user,
        )
        self.assertIn(execution.status, ('completed', 'in_progress'))

    def test_cancel_execution(self):
        wf = self.workflow
        ex = Execution.objects.create(
            workflow=wf, workflow_version=1,
            status='in_progress', data={}, triggered_by=self.user,
        )
        from apps.engine.executor import ExecutionEngine
        engine = ExecutionEngine()
        updated = engine.cancel_execution(str(ex.id), self.user)
        self.assertEqual(updated.status, 'canceled')
        self.assertIsNotNone(updated.ended_at)
