from rest_framework import serializers
from apps.executions.models import Execution, EmailNotification

class ExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    triggered_by_email = serializers.CharField(source='triggered_by.email', read_only=True)

    class Meta:
        model = Execution
        fields = '__all__'
        read_only_fields = ['id', 'company', 'status', 'logs', 'current_step_id', 'retries', 'iteration_count', 'started_at', 'ended_at']

class EmailNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailNotification
        fields = '__all__'
