"""
Execution views.
"""
import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.authentication.permissions import IsCompanyAdmin, IsCompanyMember, IsApprover
from apps.workflows.models import Workflow
from apps.engine.executor import ExecutionEngine
from .models import Execution
from .serializers import (
    ExecutionDetailSerializer, ExecutionListSerializer,
    ExecutionStartSerializer, ApprovalActionSerializer, AuditLogSerializer,
)

logger = logging.getLogger(__name__)
engine = ExecutionEngine()


class ExecuteWorkflowView(APIView):
    """
    POST /api/workflows/{workflow_id}/execute/
    Start a new workflow execution.
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]

    @swagger_auto_schema(
        operation_summary='Start workflow execution',
        request_body=ExecutionStartSerializer,
        responses={201: ExecutionDetailSerializer},
        tags=['Executions'],
    )
    def post(self, request, workflow_id):
        serializer = ExecutionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            execution = engine.start_execution(
                workflow_id=str(workflow_id),
                input_data=serializer.validated_data['data'],
                user=request.user,
                max_iterations=serializer.validated_data.get('max_iterations', 10),
            )
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ExecutionDetailSerializer(execution).data,
            status=status.HTTP_201_CREATED,
        )


class ExecutionDetailView(generics.RetrieveAPIView):
    """
    GET /api/executions/{id}/
    Full execution status with logs.
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    serializer_class = ExecutionDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.company:
            return Execution.objects.none()
        return Execution.objects.filter(workflow__company=user.company)

    @swagger_auto_schema(
        operation_summary='Get execution detail with full logs',
        responses={200: ExecutionDetailSerializer},
        tags=['Executions'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExecutionListView(generics.ListAPIView):
    """
    GET /api/executions/
    List executions for company with filtering.
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    serializer_class = ExecutionListSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.company:
            return Execution.objects.none()

        qs = Execution.objects.filter(workflow__company=user.company)

        # Apply filters from query params
        workflow_id = self.request.query_params.get('workflow_id')
        exec_status = self.request.query_params.get('status')
        triggered_by = self.request.query_params.get('triggered_by')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        if exec_status:
            qs = qs.filter(status=exec_status)
        if triggered_by:
            qs = qs.filter(triggered_by__email=triggered_by)
        if date_from:
            qs = qs.filter(started_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(started_at__date__lte=date_to)

        return qs

    @swagger_auto_schema(
        operation_summary='List executions (company-filtered)',
        manual_parameters=[
            openapi.Parameter('workflow_id', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              enum=['pending', 'in_progress', 'completed', 'failed', 'canceled']),
            openapi.Parameter('triggered_by', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('date_from', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
        tags=['Executions'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExecutionApproveView(APIView):
    """
    POST /api/executions/{id}/approve/
    POST /api/executions/{id}/reject/
    POST /api/executions/{id}/return/
    """
    permission_classes = [IsAuthenticated]

    def _get_execution(self, pk, user):
        try:
            return Execution.objects.get(pk=pk, workflow__company=user.company)
        except Execution.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary='Approve current approval step',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['approve']),
                'comment': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        tags=['Executions'],
    )
    def post(self, request, pk, action_type='approve'):
        execution = self._get_execution(pk, request.user)
        if not execution:
            return Response({'detail': 'Execution not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check permission — must be approver or admin
        if request.user.role not in ('super_admin', 'admin'):
            if execution.current_step_id:
                try:
                    from apps.steps.models import Step
                    step = Step.objects.get(id=execution.current_step_id)
                    assignee = step.metadata.get('assignee_email', '')
                    if request.user.email != assignee:
                        return Response(
                            {'detail': f'Only {assignee} or admin can act on this step.'},
                            status=status.HTTP_403_FORBIDDEN,
                        )
                except Exception:
                    pass

        serializer = ApprovalActionSerializer(data={
            'action': action_type,
            'comment': request.data.get('comment', ''),
        })
        serializer.is_valid(raise_exception=True)

        try:
            updated = engine.handle_approval_action(
                execution_id=str(execution.id),
                step_id=str(execution.current_step_id),
                user=request.user,
                action=action_type,
                comment=serializer.validated_data.get('comment', ''),
            )
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ExecutionDetailSerializer(updated).data)


class ExecutionActionView(ExecutionApproveView):
    """Handles approve/reject/return with the action_type from URL."""
    pass


class ExecutionCancelView(APIView):
    """
    POST /api/executions/{id}/cancel/
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]

    @swagger_auto_schema(
        operation_summary='Cancel a running execution',
        tags=['Executions'],
    )
    def post(self, request, pk):
        try:
            updated = engine.cancel_execution(str(pk), request.user)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExecutionDetailSerializer(updated).data)


class ExecutionRetryView(APIView):
    """
    POST /api/executions/{id}/retry/
    Retry the FAILED STEP ONLY — not entire workflow.
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    @swagger_auto_schema(
        operation_summary='Retry failed step only (not entire workflow)',
        tags=['Executions'],
    )
    def post(self, request, pk):
        try:
            updated = engine.retry_execution(str(pk), request.user)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExecutionDetailSerializer(updated).data)


class AuditLogView(generics.ListAPIView):
    """
    GET /api/audit/
    Executions list with aggregate statistics.
    ADMIN ONLY.
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.company:
            return Execution.objects.none()

        qs = Execution.objects.filter(workflow__company=user.company)
        workflow_id = self.request.query_params.get('workflow_id')
        exec_status = self.request.query_params.get('status')
        triggered_by = self.request.query_params.get('triggered_by')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        if exec_status:
            qs = qs.filter(status=exec_status)
        if triggered_by:
            qs = qs.filter(triggered_by__email=triggered_by)
        if date_from:
            qs = qs.filter(started_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(started_at__date__lte=date_to)

        return qs

    @swagger_auto_schema(
        operation_summary='Audit log with statistics (admin only)',
        manual_parameters=[
            openapi.Parameter('workflow_id', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('date_from', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
        tags=['Audit'],
    )
    def get(self, request, *args, **kwargs):
        # Build aggregate stats first
        from django.db.models import Count
        qs = self.get_queryset()
        stats = {}
        counts = qs.values('status').annotate(count=Count('id'))
        status_map = {
            'pending': 0, 'in_progress': 0,
            'completed': 0, 'failed': 0, 'canceled': 0,
        }
        for row in counts:
            status_map[row['status']] = row['count']
        stats['total'] = qs.count()
        stats.update(status_map)

        # Get paginated results
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['stats'] = stats
            return response

        serializer = self.get_serializer(qs, many=True)
        return Response({'stats': stats, 'results': serializer.data})
