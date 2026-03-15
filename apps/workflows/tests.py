"""
Workflow tests.
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.authentication.models import Company, User
from apps.workflows.models import Workflow


class WorkflowAPITest(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Corp')
        self.admin = User.objects.create_user(
            email='admin@testcorp.com', password='Admin123!',
            company=self.company, first_name='Admin', last_name='User', role='admin',
        )
        self.client.force_authenticate(user=self.admin)

    def test_create_workflow(self):
        url = '/api/workflows/'
        data = {
            'name': 'Test Workflow',
            'input_schema': {
                'fields': [
                    {'name': 'amount', 'type': 'number', 'required': True, 'allowed_values': []},
                ]
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Workflow')
        self.assertEqual(response.data['version'], 1)

    def test_list_workflows_filtered_by_company(self):
        Workflow.objects.create(company=self.company, name='WF 1', version=1, input_schema={'fields': []})
        other_company = Company.objects.create(name='Other Corp')
        Workflow.objects.create(company=other_company, name='WF Other', version=1, input_schema={'fields': []})

        response = self.client.get('/api/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [w['name'] for w in response.data['results']]
        self.assertIn('WF 1', names)
        self.assertNotIn('WF Other', names)

    def test_update_creates_new_version(self):
        wf = Workflow.objects.create(
            company=self.company, name='Versioned WF',
            version=1, is_active=True, input_schema={'fields': []}
        )
        response = self.client.put(
            f'/api/workflows/{wf.id}/',
            {'name': 'Versioned WF', 'input_schema': {'fields': []}},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version'], 2)
        # Old version should be locked
        wf.refresh_from_db()
        self.assertFalse(wf.is_active)

    def test_soft_delete(self):
        wf = Workflow.objects.create(
            company=self.company, name='To Delete',
            version=1, is_active=True, input_schema={'fields': []}
        )
        response = self.client.delete(f'/api/workflows/{wf.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wf.refresh_from_db()
        self.assertFalse(wf.is_active)
