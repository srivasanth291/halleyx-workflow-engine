"""
Authentication tests.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.authentication.models import Company, User


class CompanyModelTest(TestCase):
    def test_company_slug_auto_generated(self):
        company = Company.objects.create(name='TCS India', plan='pro')
        self.assertEqual(company.slug, 'tcs-india')

    def test_company_str(self):
        company = Company.objects.create(name='TCS India', plan='basic')
        self.assertEqual(str(company), 'TCS India')


class UserModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Corp')

    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='Pass123!',
            company=self.company,
            first_name='Test',
            last_name='User',
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.full_name, 'Test User')
        self.assertTrue(user.check_password('Pass123!'))

    def test_user_full_name(self):
        user = User(first_name='John', last_name='Doe')
        self.assertEqual(user.full_name, 'John Doe')


class RegisterAPITest(APITestCase):
    def test_register_creates_company_and_user(self):
        url = reverse('auth-register')
        data = {
            'company_name': 'New Corp',
            'plan': 'basic',
            'email': 'admin@newcorp.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('company', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['role'], 'admin')


class LoginAPITest(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Corp')
        self.user = User.objects.create_user(
            email='test@testcorp.com',
            password='Pass123!',
            company=self.company,
            first_name='Test',
            last_name='User',
            role='admin',
        )

    def test_login_success(self):
        url = reverse('auth-login')
        response = self.client.post(url, {
            'email': 'test@testcorp.com',
            'password': 'Pass123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        url = reverse('auth-login')
        response = self.client.post(url, {
            'email': 'test@testcorp.com',
            'password': 'WrongPass!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
