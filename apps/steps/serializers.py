"""
Step serializers.
"""
from rest_framework import serializers
from .models import Step


class RuleSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    condition = serializers.CharField()
    next_step_id = serializers.UUIDField(allow_null=True)
    priority = serializers.IntegerField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class StepSerializer(serializers.ModelSerializer):
    """Full step serializer with nested rules."""
    rules = RuleSerializer(many=True, read_only=True)
    workflow_id = serializers.UUIDField(source='workflow.id', read_only=True)

    class Meta:
        model = Step
        fields = [
            'id', 'workflow_id', 'name', 'step_type', 'order', 'metadata',
            'rules', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'workflow_id', 'rules', 'created_at', 'updated_at']

    def validate(self, attrs):
        step_type = attrs.get('step_type', getattr(self.instance, 'step_type', None))
        metadata = attrs.get('metadata', getattr(self.instance, 'metadata', {}))

        if step_type == 'approval':
            if not metadata.get('assignee_email'):
                raise serializers.ValidationError({'metadata': 'assignee_email is required for approval steps.'})
        elif step_type == 'notification':
            if not metadata.get('notification_channel'):
                raise serializers.ValidationError({'metadata': 'notification_channel is required for notification steps.'})
            if not metadata.get('template'):
                raise serializers.ValidationError({'metadata': 'template is required for notification steps.'})
        return attrs


class StepCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating steps (writes no rules)."""

    class Meta:
        model = Step
        fields = ['id', 'name', 'step_type', 'order', 'metadata', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        step_type = attrs.get('step_type')
        metadata = attrs.get('metadata', {})
        if step_type == 'approval' and not metadata.get('assignee_email'):
            raise serializers.ValidationError({'metadata': 'assignee_email is required for approval steps.'})
        if step_type == 'notification':
            if not metadata.get('notification_channel'):
                raise serializers.ValidationError({'metadata': 'notification_channel is required for notification steps.'})
            if not metadata.get('template'):
                raise serializers.ValidationError({'metadata': 'template is required for notification steps.'})
        return attrs


class StepReorderSerializer(serializers.Serializer):
    """For bulk reorder request."""
    workflow_id = serializers.UUIDField()
    step_orders = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_step_orders(self, value):
        for item in value:
            if 'step_id' not in item or 'order' not in item:
                raise serializers.ValidationError('Each item must have step_id and order.')
        return value
