"""
Workflow filters using django-filter.
"""
import django_filters
from .models import Workflow


class WorkflowFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Workflow
        fields = ['is_active', 'name']
