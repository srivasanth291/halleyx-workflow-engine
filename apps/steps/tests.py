"""
Step tests.
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.authentication.models import Company, User
from apps.workflows.models import Workflow
from apps.steps.models import Step


class StepAPITest(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Corp')
        self.admin = User.objects.create_user(
            email='admin@test.com', password='Admin123!',
            company=self.company, first_name='Admin', last_name='User', role='admin',
        )
        self.workflow = Workflow.objects.create(
            company=self.company, name='Test WF', version=1,
            is_active=True, input_schema={'fields': []}
        )
        self.client.force_authenticate(user=self.admin)

    def test_create_approval_step(self):
        response = self.client.post(
            f'/api/workflows/{self.workflow.id}/steps/',
            {
                'name': 'Manager Approval',
                'step_type': 'approval',
                'order': 1,
                'metadata': {
                    'assignee_email': 'manager@test.com',
                    'instructions': 'Review',
                    'timeout_hours': 24,
                    'on_timeout': 'escalate',
                    'escalate_to': 'director@test.com',
                },
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_approval_step_without_assignee_fails(self):
        response = self.client.post(
            f'/api/workflows/{self.workflow.id}/steps/',
            {'name': 'Bad Step', 'step_type': 'approval', 'order': 1, 'metadata': {}},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_notification_step(self):
        response = self.client.post(
            f'/api/workflows/{self.workflow.id}/steps/',
            {
                'name': 'Notify HR',
                'step_type': 'notification',
                'order': 2,
                'metadata': {
                    'notification_channel': 'email',
                    'template': 'Hello {name}',
                    'recipients': ['hr@test.com'],
                },
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
