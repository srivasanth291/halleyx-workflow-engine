"""
Company isolation middleware.
Injects user's company into every authenticated request,
ensuring automatic multi-tenant data isolation.
"""
import logging
from django.utils.functional import SimpleLazyObject

logger = logging.getLogger(__name__)


def get_user_company(request):
    """Retrieve the company from the authenticated user."""
    if not hasattr(request, '_cached_user_company'):
        user = request.user
        if user and user.is_authenticated:
            request._cached_user_company = getattr(user, 'company', None)
        else:
            request._cached_user_company = None
    return request._cached_user_company


class CompanyMiddleware:
    """
    Middleware that injects the authenticated user's company
    into the request object for automatic data isolation.

    Usage in views:
        request.user_company  → Company object or None
        request.company_id    → UUID or None
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Inject company lazily (only accessed if needed)
        request.user_company = SimpleLazyObject(lambda: get_user_company(request))

        response = self.get_response(request)
        return response


class CompanyQuerysetMixin:
    """
    Mixin for ViewSets that automatically filters querysets
    to the authenticated user's company.

    Usage:
        class MyViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            # queryset is automatically filtered by company
    """

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and hasattr(user, 'company') and user.company:
            return qs.filter(company=user.company)
        return qs.none()
