from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from apps.authentication.settings_views import CompanySettingsView, EmailSettingsView, NotificationSettingsView

schema_view = get_schema_view(
   openapi.Info(
      title="FlowEngine API",
      default_version='v1',
      description="API documentation for Halleyx Workflow Engine",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/workflows/', include('apps.workflows.urls')),
    path('api/steps/', include('apps.steps.urls')),
    path('api/rules/', include('apps.rules.urls')),
    path('api/', include('apps.executions.urls')),
    # Settings endpoints
    path('api/settings/company/', CompanySettingsView.as_view(), name='settings-company'),
    path('api/settings/email/', EmailSettingsView.as_view(), name='settings-email'),
    path('api/settings/notifications/', NotificationSettingsView.as_view(), name='settings-notifications'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
