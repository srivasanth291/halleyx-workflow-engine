from django.core.management.base import BaseCommand
from apps.authentication.models import Company, User
from django.db import transaction

class Command(BaseCommand):
    help = 'Seeds 4 organizations with varied user levels and creation orders'

    def handle(self, *args, **options):
        companies_data = [
            {
                'name': 'Quantum Cybernetics',
                'plan': 'enterprise',
                'users': [
                    {'email': 'cto@quantum.io', 'role': 'admin', 'first_name': 'Aleksei', 'last_name': 'Romanov'},
                    {'email': 'staff.one@quantum.io', 'role': 'employee', 'first_name': 'Elena', 'last_name': 'Belova'},
                    {'email': 'lead.dev@quantum.io', 'role': 'employee', 'first_name': 'Nikolai', 'last_name': 'Volkov'},
                    {'email': 'intern.a@quantum.io', 'role': 'employee', 'first_name': 'Sasha', 'last_name': 'Ivanov'},
                ]
            },
            {
                'name': 'Nebula Marketing',
                'plan': 'pro',
                'users': [
                    {'email': 'creative.director@nebula.com', 'role': 'admin', 'first_name': 'Sophia', 'last_name': 'Loren'},
                    {'email': 'copywriter@nebula.com', 'role': 'employee', 'first_name': 'Marco', 'last_name': 'Rossi'},
                    {'email': 'designer.one@nebula.com', 'role': 'employee', 'first_name': 'Lucia', 'last_name': 'Bianchi'},
                ]
            },
            {
                'name': 'Titan Manufacturing',
                'plan': 'enterprise',
                'users': [
                    {'email': 'plant.manager@titan.com', 'role': 'admin', 'first_name': 'Hans', 'last_name': 'Mueller'},
                    {'email': 'floor.lead@titan.com', 'role': 'employee', 'first_name': 'Greta', 'last_name': 'Schmidt'},
                    {'email': 'safety.officer@titan.com', 'role': 'employee', 'first_name': 'Otto', 'last_name': 'Wagner'},
                    {'email': 'logistics.head@titan.com', 'role': 'employee', 'first_name': 'Klaus', 'last_name': 'Fischer'},
                ]
            },
            {
                'name': 'Solaris Energy',
                'plan': 'basic',
                'users': [
                    {'email': 'founder@solaris.co', 'role': 'admin', 'first_name': 'Zoe', 'last_name': 'Sun'},
                    {'email': 'field.tech@solaris.co', 'role': 'employee', 'first_name': 'Ray', 'last_name': 'Cloud'},
                ]
            }
        ]

        with transaction.atomic():
            for c_data in companies_data:
                company, created = Company.objects.get_or_create(
                    name=c_data['name'],
                    defaults={'plan': c_data['plan']}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created Company: {company.name}"))
                
                # Vary the order by alternating roles in the creation loop if desired, 
                # but following the list order provides a controlled variety.
                for u_data in c_data['users']:
                    if not User.objects.filter(email=u_data['email']).exists():
                        user = User.objects.create_user(
                            email=u_data['email'],
                            password='Password123!',
                            company=company,
                            role=u_data['role'],
                            first_name=u_data['first_name'],
                            last_name=u_data['last_name']
                        )
                        self.stdout.write(self.style.SUCCESS(f"  Created User: {user.email} ({user.role})"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  User {u_data['email']} already exists"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded refined dynamic data!'))
