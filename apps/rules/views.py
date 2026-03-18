from rest_framework import viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.rules.models import Rule
from apps.rules.serializers import RuleSerializer
from apps.authentication.permissions import IsCompanyAdmin
from django.db import transaction
from apps.engine.rule_engine import RuleEngine

class RuleViewSet(viewsets.ModelViewSet):
    serializer_class = RuleSerializer
    permission_classes = [IsCompanyAdmin]

    def get_queryset(self):
        return Rule.objects.filter(step__workflow__company=self.request.user.company)

    def perform_create(self, serializer):
        condition = self.request.data.get('condition')
        
        if condition:
            engine = RuleEngine()
            valid_res = engine.validate_condition(condition)
            if not valid_res['valid']:
                raise serializers.ValidationError({"condition": valid_res['error']})
            
        serializer.save()

    def perform_update(self, serializer):
        condition = self.request.data.get('condition', serializer.instance.condition)
        if condition:
            engine = RuleEngine()
            valid_res = engine.validate_condition(condition)
            if not valid_res['valid']:
                raise serializers.ValidationError({"condition": valid_res['error']})
            
        serializer.save()

    @action(detail=False, methods=['post'])
    def validate_syntax(self, request):
        condition = request.data.get('condition')
        engine = RuleEngine()
        return Response(engine.validate_condition(condition))

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        rule_priorities = request.data.get('rule_priorities', [])
        with transaction.atomic():
            for item in rule_priorities:
                Rule.objects.filter(
                    id=item['rule_id'], 
                    step__workflow__company=self.request.user.company
                ).update(priority=item['priority'])
        return Response({"status": "reordered"})
