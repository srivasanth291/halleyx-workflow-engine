import os
import django
import sys

# Add the project root to sys.path
sys.path.append('/app')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.authentication.models import User, Company

def list_all_logins():
    print(f"{'EMAIL':<30} | {'COMPANY':<20} | {'ROLE':<15}")
    print("-" * 70)
    
    users = User.objects.all().select_related('company', 'role')
    for user in users:
        company_name = user.company.name if user.company else "N/A"
        role_name = user.role.name if user.role else "N/A"
        print(f"{user.email:<30} | {company_name:<20} | {role_name:<15}")

if __name__ == "__main__":
    list_all_logins()
