"""
Step URL patterns.
"""
from django.urls import path
from .views import StepListCreateView, StepDetailView, StepReorderView

urlpatterns = [
    path('workflows/<uuid:workflow_id>/steps/', StepListCreateView.as_view(), name='step-list-create'),
    path('steps/<uuid:pk>/', StepDetailView.as_view(), name='step-detail'),
    path('steps/reorder/', StepReorderView.as_view(), name='step-reorder'),
]
