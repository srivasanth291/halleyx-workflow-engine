"""
Rule URL patterns.
"""
from django.urls import path
from .views import RuleListCreateView, RuleDetailView, RuleValidateView, RuleReorderView

urlpatterns = [
    path('steps/<uuid:step_id>/rules/', RuleListCreateView.as_view(), name='rule-list-create'),
    path('rules/<uuid:pk>/', RuleDetailView.as_view(), name='rule-detail'),
    path('rules/validate/', RuleValidateView.as_view(), name='rule-validate'),
    path('steps/<uuid:step_id>/rules/reorder/', RuleReorderView.as_view(), name='rule-reorder'),
]
