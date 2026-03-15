"""
Root URL configuration for Halleyx Workflow API.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ════════════════════════════════════════
# SWAGGER / REDOC SCHEMA
# ════════════════════════════════════════
api_info = openapi.Info(
    title='Halleyx Workflow API',
    default_version='v1',
    description="""
# Halleyx Workflow Management System API

## Overview
A complete workflow management system with rule-based execution engine.

## Authentication
All endpoints (except login/register) require a **Bearer JWT token**:
```
Authorization: Bearer <access_token>
```

## Multi-Tenancy
Data is automatically filtered by company from the JWT token.
Users only see data belonging to their own company.

## Workflow Versioning
Editing a workflow creates a new version. Old versions are locked forever.

## Rule Engine
Conditions use a custom safe parser (never eval). Supported:
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `&&` (AND), `||` (OR)
- String: `contains(field, 'value')`, `startsWith(...)`, `endsWith(...)`
- Special: `DEFAULT` (always matches, used as fallback)

## Loop Prevention
Every execution tracks `iteration_count` vs `max_iterations` (default 10).
""",
    terms_of_service='https://halleyx.com/terms/',
    contact=openapi.Contact(email='support@halleyx.com'),
    license=openapi.License(name='Proprietary'),
)

schema_view = get_schema_view(
    api_info,
    public=True,
    permission_classes=[permissions.AllowAny],
)

# ════════════════════════════════════════
# URL PATTERNS
# ════════════════════════════════════════
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Swagger docs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # API routes
    path('api/auth/', include('apps.authentication.urls')),
    path('api/', include('apps.workflows.urls')),
    path('api/', include('apps.steps.urls')),
    path('api/', include('apps.rules.urls')),
    path('api/', include('apps.executions.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
