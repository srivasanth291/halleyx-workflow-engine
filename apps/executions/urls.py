from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.executions.views import ExecutionViewSet, AuditLogView, NotificationViewSet, ActionTokenView

router = DefaultRouter()
router.register(r'executions', ExecutionViewSet, basename='execution')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('audit/', AuditLogView.as_view(), name='audit_log'),
    path('action-token/<uuid:token_id>/', ActionTokenView.as_view(), name='action_token'),
    path('', include(router.urls)),
]
