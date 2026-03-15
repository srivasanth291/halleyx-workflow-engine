"""
Execution URL patterns.
"""
from django.urls import path
from .views import (
    ExecuteWorkflowView, ExecutionDetailView, ExecutionListView,
    ExecutionApproveView, ExecutionCancelView, ExecutionRetryView,
    AuditLogView,
)

urlpatterns = [
    # Execute workflow
    path('workflows/<uuid:workflow_id>/execute/', ExecuteWorkflowView.as_view(), name='workflow-execute'),

    # Execution CRUD
    path('executions/', ExecutionListView.as_view(), name='execution-list'),
    path('executions/<uuid:pk>/', ExecutionDetailView.as_view(), name='execution-detail'),

    # Approval actions
    path('executions/<uuid:pk>/approve/', ExecutionApproveView.as_view(), {'action_type': 'approve'}, name='execution-approve'),
    path('executions/<uuid:pk>/reject/', ExecutionApproveView.as_view(), {'action_type': 'reject'}, name='execution-reject'),
    path('executions/<uuid:pk>/return/', ExecutionApproveView.as_view(), {'action_type': 'return'}, name='execution-return'),

    # Cancel and retry
    path('executions/<uuid:pk>/cancel/', ExecutionCancelView.as_view(), name='execution-cancel'),
    path('executions/<uuid:pk>/retry/', ExecutionRetryView.as_view(), name='execution-retry'),

    # Audit log with stats
    path('audit/', AuditLogView.as_view(), name='audit-log'),
]
