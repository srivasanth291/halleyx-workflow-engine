"""
Rule serializers.
"""
from rest_framework import serializers
from apps.engine.rule_engine import RuleEngine
from .models import Rule

rule_engine = RuleEngine()


class RuleSerializer(serializers.ModelSerializer):
    """Full rule serializer with condition validation."""

    class Meta:
        model = Rule
        fields = ['id', 'step', 'condition', 'next_step_id', 'priority', 'created_at', 'updated_at']
        read_only_fields = ['id', 'step', 'created_at', 'updated_at']

    def validate_condition(self, value):
        result = rule_engine.validate_condition(value)
        if not result['valid']:
            raise serializers.ValidationError(
                f'Invalid condition syntax: {result["error"]}'
            )
        return value


class RuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating rules."""

    class Meta:
        model = Rule
        fields = ['id', 'condition', 'next_step_id', 'priority', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_condition(self, value):
        result = rule_engine.validate_condition(value)
        if not result['valid']:
            raise serializers.ValidationError(
                f'Invalid condition syntax: {result["error"]}'
            )
        return value


class RuleReorderSerializer(serializers.Serializer):
    """For bulk rule priority update."""
    rule_priorities = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_rule_priorities(self, value):
        for item in value:
            if 'rule_id' not in item or 'priority' not in item:
                raise serializers.ValidationError('Each item must have rule_id and priority.')
        return value


class RuleValidateSerializer(serializers.Serializer):
    """For validating a condition without saving."""
    condition = serializers.CharField()
