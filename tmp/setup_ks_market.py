import os
import django
import uuid
import sys
from django.utils import timezone

# Add the project root to sys.path
sys.path.append('/app')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.authentication.models import Company, Role, User
from apps.workflows.models import Workflow
from apps.steps.models import Step
from apps.rules.models import Rule

def setup_ks_market():
    print("Setting up KS Super Market data...")
    
    # Create Company
    company, _ = Company.objects.get_or_create(
        name="KS Super Market",
        defaults={'plan': 'enterprise'}
    )
    
    # Create Roles
    admin_role, _ = Role.objects.get_or_create(
        company=company,
        name='Admin',
        defaults={'is_admin': True}
    )
    
    employee_role, _ = Role.objects.get_or_create(
        company=company,
        name='Staff',
        defaults={'is_admin': False}
    )
    
    # Create User
    email = 'ks_admin@ksmarket.com'
    password = 'KSAdmin123!'
    
    User.objects.filter(email=email).delete()
    user = User.objects.create_user(
        email=email,
        password=password,
        role=admin_role,
        company=company,
        first_name="KS",
        last_name="Admin"
    )
    
    # Create a Workflow for KS Super Market
    wf, _ = Workflow.objects.get_or_create(
        name="Inventory Restock",
        company=company,
        defaults={
            'version': 1,
            'input_schema': {
                "fields": [
                    {"name": "item_name", "type": "string", "required": True},
                    {"name": "quantity", "type": "number", "required": True},
                    {"name": "supplier", "type": "string", "required": True}
                ]
            }
        }
    )
    
    print(f"Successfully created KS Super Market with user: {email} / {password}")

if __name__ == "__main__":
    setup_ks_market()
