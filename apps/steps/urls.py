from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.steps.views import StepViewSet

router = DefaultRouter()
router.register(r'', StepViewSet, basename='step')

urlpatterns = [
    path('', include(router.urls)),
]
