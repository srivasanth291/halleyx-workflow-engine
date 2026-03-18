from rest_framework import serializers
from apps.steps.models import Step
from apps.rules.serializers import RuleSerializer

class StepSerializer(serializers.ModelSerializer):
    rules = RuleSerializer(many=True, read_only=True)

    class Meta:
        model = Step
        fields = ['id', 'workflow', 'name', 'step_type', 'order', 'metadata', 'created_at', 'updated_at', 'rules']
        read_only_fields = ['id', 'created_at', 'updated_at']

class StepCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ['id', 'workflow', 'name', 'step_type', 'order', 'metadata', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
