from rest_framework import serializers
from apps.workflows.models import Workflow
from apps.steps.serializers import StepSerializer

class WorkflowSerializer(serializers.ModelSerializer):
    steps_count = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = ['id', 'company', 'name', 'version', 'is_active', 'input_schema', 'start_step_id', 'created_at', 'updated_at', 'steps_count']
        read_only_fields = ['id', 'company', 'version', 'is_active', 'created_at', 'updated_at']

    def get_steps_count(self, obj):
        return obj.steps.count() if hasattr(obj, 'steps') else 0

class WorkflowDetailSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True, read_only=True)

    class Meta:
        model = Workflow
        fields = ['id', 'company', 'name', 'version', 'is_active', 'input_schema', 'start_step_id', 'created_at', 'updated_at', 'steps']
        read_only_fields = ['id', 'company', 'version', 'is_active', 'created_at', 'updated_at']
