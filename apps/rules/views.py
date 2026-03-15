"""
Rule views.
"""
import logging
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.authentication.permissions import IsCompanyAdmin, IsCompanyMember
from apps.steps.models import Step
from apps.engine.rule_engine import RuleEngine
from .models import Rule
from .serializers import RuleSerializer, RuleCreateSerializer, RuleReorderSerializer, RuleValidateSerializer

logger = logging.getLogger(__name__)
rule_engine = RuleEngine()


class RuleListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/steps/{step_id}/rules/ — List rules ordered by priority
    POST /api/steps/{step_id}/rules/ — Create rule (validates condition)
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCompanyAdmin()]
        return [IsAuthenticated(), IsCompanyMember()]

    def get_serializer_class(self):
        return RuleCreateSerializer

    def get_queryset(self):
        step_id = self.kwargs.get('step_id')
        user = self.request.user
        try:
            step = Step.objects.get(id=step_id, workflow__company=user.company)
        except Step.DoesNotExist:
            return Rule.objects.none()
        return Rule.objects.filter(step=step).order_by('priority')

    @swagger_auto_schema(operation_summary='List rules for step', tags=['Rules'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Create rule for step (validates condition syntax)',
        request_body=RuleCreateSerializer,
        tags=['Rules'],
    )
    def post(self, request, *args, **kwargs):
        step_id = self.kwargs.get('step_id')
        user = request.user
        try:
            step = Step.objects.get(id=step_id, workflow__company=user.company)
        except Step.DoesNotExist:
            return Response({'detail': 'Step not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rule = Rule.objects.create(
            step=step,
            condition=serializer.validated_data['condition'],
            next_step_id=serializer.validated_data.get('next_step_id'),
            priority=serializer.validated_data['priority'],
        )
        return Response(RuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class RuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/rules/{id}/
    PUT    /api/rules/{id}/
    DELETE /api/rules/{id}/
    """

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAuthenticated(), IsCompanyAdmin()]
        return [IsAuthenticated(), IsCompanyMember()]

    def get_serializer_class(self):
        return RuleCreateSerializer

    def get_queryset(self):
        user = self.request.user
        return Rule.objects.filter(step__workflow__company=user.company)

    @swagger_auto_schema(operation_summary='Get rule detail', tags=['Rules'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Update rule (re-validates condition syntax)',
        tags=['Rules'],
    )
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Delete rule', tags=['Rules'])
    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class RuleValidateView(APIView):
    """
    POST /api/rules/validate/
    Validate a condition string without saving.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Validate condition syntax',
        request_body=RuleValidateSerializer,
        responses={
            200: openapi.Response('Validation result', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'error': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                }
            )),
        },
        tags=['Rules'],
    )
    def post(self, request):
        serializer = RuleValidateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        condition = serializer.validated_data['condition']
        result = rule_engine.validate_condition(condition)
        return Response(result, status=status.HTTP_200_OK)


class RuleReorderView(APIView):
    """
    POST /api/steps/{step_id}/rules/reorder/
    Bulk update rule priorities.
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    @swagger_auto_schema(
        operation_summary='Reorder rules (bulk priority update)',
        request_body=RuleReorderSerializer,
        tags=['Rules'],
    )
    def post(self, request, step_id):
        user = request.user
        try:
            step = Step.objects.get(id=step_id, workflow__company=user.company)
        except Step.DoesNotExist:
            return Response({'detail': 'Step not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RuleReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rule_priorities = serializer.validated_data['rule_priorities']

        with transaction.atomic():
            for item in rule_priorities:
                Rule.objects.filter(
                    id=item['rule_id'],
                    step=step,
                ).update(priority=item['priority'])

        return Response({'detail': 'Rules reordered successfully.'}, status=status.HTTP_200_OK)
