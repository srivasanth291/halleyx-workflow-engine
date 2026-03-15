"""
Step views.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.authentication.permissions import IsCompanyAdmin, IsCompanyMember
from apps.workflows.models import Workflow
from .models import Step
from .serializers import StepSerializer, StepCreateSerializer, StepReorderSerializer

logger = logging.getLogger(__name__)


class StepListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/workflows/{workflow_id}/steps/ — List steps with nested rules
    POST /api/workflows/{workflow_id}/steps/ — Create a new step
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCompanyAdmin()]
        return [IsAuthenticated(), IsCompanyMember()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StepCreateSerializer
        return StepSerializer

    def get_queryset(self):
        workflow_id = self.kwargs.get('workflow_id')
        user = self.request.user
        if not user.company:
            return Step.objects.none()
        try:
            workflow = Workflow.objects.get(id=workflow_id, company=user.company)
        except Workflow.DoesNotExist:
            return Step.objects.none()
        return Step.objects.filter(workflow=workflow).order_by('order')

    @swagger_auto_schema(
        operation_summary='List all steps in workflow',
        tags=['Steps'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Create step in workflow',
        request_body=StepCreateSerializer,
        tags=['Steps'],
    )
    def post(self, request, *args, **kwargs):
        workflow_id = self.kwargs.get('workflow_id')
        user = request.user
        try:
            workflow = Workflow.objects.get(id=workflow_id, company=user.company, is_active=True)
        except Workflow.DoesNotExist:
            return Response({'detail': 'Active workflow not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StepCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        step = Step.objects.create(
            workflow=workflow,
            name=serializer.validated_data['name'],
            step_type=serializer.validated_data['step_type'],
            order=serializer.validated_data['order'],
            metadata=serializer.validated_data.get('metadata', {}),
        )

        # Auto-set start_step_id if this is the first step (order=1) or the lowest order
        if serializer.validated_data['order'] == 1 or not workflow.start_step_id:
            # Check if there's any step with lower order
            lowest_order_step = Step.objects.filter(workflow=workflow).order_by('order').first()
            if lowest_order_step and str(lowest_order_step.id) == str(step.id):
                workflow.start_step_id = step.id
                workflow.save(update_fields=['start_step_id'])

        return Response(StepSerializer(step).data, status=status.HTTP_201_CREATED)


class StepDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/steps/{id}/
    PUT    /api/steps/{id}/
    DELETE /api/steps/{id}/
    """

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAuthenticated(), IsCompanyAdmin()]
        return [IsAuthenticated(), IsCompanyMember()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return StepCreateSerializer
        return StepSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.company:
            return Step.objects.none()
        return Step.objects.filter(workflow__company=user.company)

    @swagger_auto_schema(operation_summary='Get step detail', tags=['Steps'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Update step', tags=['Steps'])
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Delete step and its rules', tags=['Steps'])
    def delete(self, request, *args, **kwargs):
        """Delete step AND all its rules."""
        instance = self.get_object()
        from apps.rules.models import Rule
        Rule.objects.filter(step=instance).delete()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StepReorderView(APIView):
    """
    POST /api/steps/reorder/
    Atomically bulk-update step orders.
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    @swagger_auto_schema(
        operation_summary='Reorder steps (drag-and-drop)',
        request_body=StepReorderSerializer,
        tags=['Steps'],
    )
    def post(self, request):
        serializer = StepReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workflow_id = serializer.validated_data['workflow_id']
        step_orders = serializer.validated_data['step_orders']

        user = request.user
        try:
            workflow = Workflow.objects.get(id=workflow_id, company=user.company)
        except Workflow.DoesNotExist:
            return Response({'detail': 'Workflow not found.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            for item in step_orders:
                Step.objects.filter(
                    id=item['step_id'],
                    workflow=workflow,
                ).update(order=item['order'])

            # Update start_step_id to the step with lowest order
            first_step = Step.objects.filter(workflow=workflow).order_by('order').first()
            if first_step:
                workflow.start_step_id = first_step.id
                workflow.save(update_fields=['start_step_id'])

        return Response({'detail': 'Steps reordered successfully.'}, status=status.HTTP_200_OK)
