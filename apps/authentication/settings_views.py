from rest_framework import views, status
from rest_framework.response import Response
from apps.authentication.permissions import IsCompanyAdmin
from apps.authentication.models import Company
from apps.authentication.serializers import CompanySerializer
from django.core.cache import cache

class CompanySettingsView(views.APIView):
    permission_classes = [IsCompanyAdmin]

    def get(self, request):
        company = request.user.company
        serializer = CompanySerializer(company)
        data = serializer.data
        data['timezone'] = cache.get(f'company_{company.id}_timezone', 'UTC')
        return Response(data)

    def put(self, request):
        company = request.user.company
        company.name = request.data.get('name', company.name)
        company.save()
        
        timezone = request.data.get('timezone')
        if timezone:
            cache.set(f'company_{company.id}_timezone', timezone)
            
        serializer = CompanySerializer(company)
        data = serializer.data
        data['timezone'] = cache.get(f'company_{company.id}_timezone', 'UTC')
        return Response(data)

class EmailSettingsView(views.APIView):
    permission_classes = [IsCompanyAdmin]

    def get(self, request):
        company_id = request.user.company.id
        settings = cache.get(f'company_{company_id}_email_settings', {
            'smtp_host': '',
            'smtp_port': 587,
            'smtp_user': '',
            'smtp_password': '',
            'from_email': '',
            'email_enabled': False
        })
        return Response(settings)

    def put(self, request):
        company_id = request.user.company.id
        settings = {
            'smtp_host': request.data.get('smtp_host', ''),
            'smtp_port': request.data.get('smtp_port', 587),
            'smtp_user': request.data.get('smtp_user', ''),
            'smtp_password': request.data.get('smtp_password', ''),
            'from_email': request.data.get('from_email', ''),
            'email_enabled': request.data.get('email_enabled', False)
        }
        cache.set(f'company_{company_id}_email_settings', settings)
        return Response(settings)

class NotificationSettingsView(views.APIView):
    permission_classes = [IsCompanyAdmin]

    def get(self, request):
        company_id = request.user.company.id
        settings = cache.get(f'company_{company_id}_notif_settings', {
            'approval_reminder_hours': 24,
            'timeout_notifications': True,
            'completion_notifications': True
        })
        return Response(settings)

    def put(self, request):
        company_id = request.user.company.id
        settings = {
            'approval_reminder_hours': request.data.get('approval_reminder_hours', 24),
            'timeout_notifications': request.data.get('timeout_notifications', True),
            'completion_notifications': request.data.get('completion_notifications', True)
        }
        cache.set(f'company_{company_id}_notif_settings', settings)
        return Response(settings)
