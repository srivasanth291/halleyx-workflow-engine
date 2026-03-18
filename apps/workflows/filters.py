import django_filters
from apps.workflows.models import Workflow

class WorkflowFilter(django_filters.FilterSet):
    class Meta:
        model = Workflow
        fields = ['is_active']
