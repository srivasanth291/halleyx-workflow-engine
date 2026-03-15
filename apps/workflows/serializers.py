"""
Workflow serializers.
"""
from rest_framework import serializers
from .models import Workflow


def validate_input_schema(schema):
    """Validate the workflow input_schema structure."""
    if not isinstance(schema, dict):
        raise serializers.ValidationError('input_schema must be a JSON object.')
    fields = schema.get('fields')
    if fields is None:
        raise serializers.ValidationError('input_schema must have a "fields" array.')
    if not isinstance(fields, list):
        raise serializers.ValidationError('"fields" must be an array.')
    valid_types = {'number', 'string', 'boolean', 'date'}
    for i, field in enumerate(fields):
        if not isinstance(field, dict):
            raise serializers.ValidationError(f'Field at index {i} must be an object.')
        if 'name' not in field:
            raise serializers.ValidationError(f'Field at index {i} is missing "name".')
        if 'type' not in field:
            raise serializers.ValidationError(f'Field at index {i} is missing "type".')
        if 'required' not in field:
            raise serializers.ValidationError(f'Field at index {i} is missing "required".')
        if field['type'] not in valid_types:
            raise serializers.ValidationError(
                f'Field "{field["name"]}" type must be one of {sorted(valid_types)}.'
            )
    return schema


class WorkflowListSerializer(serializers.ModelSerializer):
    """Compact serializer for list endpoints."""
    steps_count = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = ['id', 'name', 'version', 'is_active', 'steps_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']

    def get_steps_count(self, obj):
        return obj.steps.count()


class RuleInlineSerializer(serializers.Serializer):
    """Inline rule for nested detail serializer."""
    id = serializers.UUIDField()
    condition = serializers.CharField()
    next_step_id = serializers.UUIDField(allow_null=True)
    priority = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class StepDetailSerializer(serializers.Serializer):
    """Nested step with rules for detail endpoint."""
    id = serializers.UUIDField()
    name = serializers.CharField()
    step_type = serializers.CharField()
    order = serializers.IntegerField()
    metadata = serializers.JSONField()
    rules = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_rules(self, obj):
        return RuleInlineSerializer(obj.rules.all().order_by('priority'), many=True).data


class WorkflowDetailSerializer(serializers.ModelSerializer):
    """Full workflow with nested steps and rules."""
    steps = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'version', 'is_active', 'input_schema',
            'start_step_id', 'steps', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']

    def get_steps(self, obj):
        return StepDetailSerializer(obj.steps.all().order_by('order'), many=True).data


class WorkflowCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating or updating workflows."""

    class Meta:
        model = Workflow
        fields = ['name', 'input_schema']

    def validate_input_schema(self, value):
        return validate_input_schema(value)


class WorkflowVersionSerializer(serializers.ModelSerializer):
    """Serializer for version history list."""
    is_locked = serializers.SerializerMethodField()
    steps_count = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = ['id', 'version', 'is_active', 'is_locked', 'steps_count', 'created_at']

    def get_is_locked(self, obj):
        return not obj.is_active

    def get_steps_count(self, obj):
        return obj.steps.count()
