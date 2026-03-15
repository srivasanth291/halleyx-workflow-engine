"""
Execution serializers.
"""
from rest_framework import serializers
from .models import Execution


class ExecutionListSerializer(serializers.ModelSerializer):
    """Compact serializer for list/audit endpoints."""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    triggered_by_email = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Execution
        fields = [
            'id', 'workflow_name', 'workflow_version', 'status',
            'triggered_by_email', 'started_at', 'ended_at',
            'duration_seconds', 'retries', 'max_iterations', 'iteration_count',
        ]
        read_only_fields = fields

    def get_triggered_by_email(self, obj):
        return obj.triggered_by.email if obj.triggered_by else None

    def get_duration_seconds(self, obj):
        if obj.started_at and obj.ended_at:
            return int((obj.ended_at - obj.started_at).total_seconds())
        return None


class CurrentStepSerializer(serializers.Serializer):
    """Inline current step for execution detail."""
    id = serializers.UUIDField()
    name = serializers.CharField()
    step_type = serializers.CharField()
    assignee_email = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    notification_channel = serializers.SerializerMethodField()
    template = serializers.SerializerMethodField()
    recipients = serializers.SerializerMethodField()

    def get_assignee_email(self, obj):
        return obj.metadata.get('assignee_email') if obj.metadata else None

    def get_instructions(self, obj):
        return obj.metadata.get('instructions') if obj.metadata else None

    def get_notification_channel(self, obj):
        return obj.metadata.get('notification_channel') if obj.metadata else None

    def get_template(self, obj):
        return obj.metadata.get('template') if obj.metadata else None

    def get_recipients(self, obj):
        return obj.metadata.get('recipients') if obj.metadata else None


class ExecutionDetailSerializer(serializers.ModelSerializer):
    """Full execution detail with current step and logs."""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    workflow_id = serializers.UUIDField(source='workflow.id', read_only=True)
    triggered_by = serializers.SerializerMethodField()
    current_step = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Execution
        fields = [
            'id', 'workflow_id', 'workflow_name', 'workflow_version',
            'status', 'data', 'current_step', 'logs',
            'retries', 'max_iterations', 'iteration_count',
            'triggered_by', 'started_at', 'ended_at', 'duration_seconds',
        ]
        read_only_fields = fields

    def get_triggered_by(self, obj):
        return obj.triggered_by.email if obj.triggered_by else None

    def get_current_step(self, obj):
        if not obj.current_step_id:
            return None
        try:
            from apps.steps.models import Step
            step = Step.objects.get(id=obj.current_step_id)
            return CurrentStepSerializer(step).data
        except Exception:
            return None

    def get_duration_seconds(self, obj):
        if obj.started_at and obj.ended_at:
            return int((obj.ended_at - obj.started_at).total_seconds())
        return None


class ExecutionStartSerializer(serializers.Serializer):
    """For starting a workflow execution."""
    data = serializers.DictField(required=True)
    max_iterations = serializers.IntegerField(default=10, min_value=1, max_value=100)


class ApprovalActionSerializer(serializers.Serializer):
    """For approve/reject/return actions."""
    action = serializers.ChoiceField(choices=['approve', 'reject', 'return'])
    comment = serializers.CharField(required=False, default='', allow_blank=True)


class AuditLogSerializer(ExecutionListSerializer):
    """Same as ExecutionListSerializer — used in audit endpoint."""
    pass
