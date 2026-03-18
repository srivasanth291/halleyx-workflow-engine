from django.core.management.base import BaseCommand
from apps.authentication.models import Company, Role
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create specific sample data for KTS Supermarket'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating KTS Supermarket sample data...")

        company, created = Company.objects.get_or_create(
            name="KTS Supermarket",
            defaults={'plan': 'pro'}
        )
        if created:
            self.stdout.write(f"Created company: {company.name}")
        else:
            self.stdout.write(f"Using existing company: {company.name}")

        password = "KtsPass123!"

        # Ensure roles exist for this company
        admin_role, _ = Role.objects.get_or_create(
            company=company,
            name='Admin',
            defaults={'is_admin': True}
        )
        employee_role, _ = Role.objects.get_or_create(
            company=company,
            name='Employee',
            defaults={'is_admin': False}
        )

        role_map = {
            'admin': admin_role,
            'employee': employee_role
        }

        # Owner -> admin
        # Manager -> admin
        # Supervisor -> employee
        # Worker -> employee

        users_to_create = [
            {'email': 'kts.owner@example.com', 'role': 'admin', 'first_name': 'KTS', 'last_name': 'Owner'},
            {'email': 'kts.admin@example.com', 'role': 'admin', 'first_name': 'KTS', 'last_name': 'Admin'},
            {'email': 'kts.manager@example.com', 'role': 'admin', 'first_name': 'KTS', 'last_name': 'Manager'},
            {'email': 'kts.supervisor1@example.com', 'role': 'employee', 'first_name': 'KTS', 'last_name': 'Supervisor 1'},
            {'email': 'kts.supervisor2@example.com', 'role': 'employee', 'first_name': 'KTS', 'last_name': 'Supervisor 2'},
        ]

        # Adding 25 workers
        for i in range(1, 26):
            users_to_create.append({
                'email': f'kts.worker{i}@example.com',
                'role': 'employee',
                'first_name': 'KTS',
                'last_name': f'Worker {i}'
            })

        count = 0
        for u_data in users_to_create:
            # Delete if exists to fix potential data mismatch from old schema
            User.objects.filter(email=u_data['email']).delete()
            
            User.objects.create_user(
                email=u_data['email'],
                password=password,
                role=role_map[u_data['role']],
                company=company,
                first_name=u_data['first_name'],
                last_name=u_data['last_name']
            )
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} users for KTS Supermarket."))
