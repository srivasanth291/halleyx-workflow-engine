import jwt
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model

class CompanyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user_company = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                if user_id:
                    User = get_user_model()
                    user = User.objects.get(id=user_id)
                    request.user_company = user.company
            except Exception:
                pass

class CompanyQuerysetMixin:
    def get_queryset(self):
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            return super().get_queryset().filter(company=self.request.user.company)
        return super().get_queryset().none()
