"""
Workflow views — CRUD + versioning + rollback.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.authentication.permissions import IsCompanyAdmin, IsCompanyMember
from .models import Workflow
from .serializers import (
    WorkflowListSerializer, WorkflowDetailSerializer,
    WorkflowCreateUpdateSerializer, WorkflowVersionSerializer,
)

logger = logging.getLogger(__name__)


def _copy_workflow(source: Workflow, new_version: int, company, overrides: dict = None) -> Workflow:
    """
    Create a new workflow version by copying source.
    Copies all steps and their rules.
    """
    overrides = overrides or {}

    new_workflow = Workflow.objects.create(
        company=company,
        name=overrides.get('name', source.name),
        version=new_version,
        is_active=True,
        input_schema=overrides.get('input_schema', source.input_schema),
        start_step_id=None,  # will be updated after copying steps
    )

    # Map old step IDs to new step IDs
    from apps.steps.models import Step
    from apps.rules.models import Rule

    step_id_map = {}
    for old_step in source.steps.all().order_by('order'):
        new_step = Step.objects.create(
            workflow=new_workflow,
            name=old_step.name,
            step_type=old_step.step_type,
            order=old_step.order,
            metadata=old_step.metadata,
        )
        step_id_map[str(old_step.id)] = str(new_step.id)

        # Copy rules for this step
        for old_rule in old_step.rules.all().order_by('priority'):
            next_sid = str(old_rule.next_step_id) if old_rule.next_step_id else None
            Rule.objects.create(
                step=new_step,
                condition=old_rule.condition,
                next_step_id=None,  # will be remapped below
                priority=old_rule.priority,
            )

    # Remap next_step_ids in rules to new step IDs
    for old_step in source.steps.all().order_by('order'):
        new_step_id = step_id_map.get(str(old_step.id))
        if not new_step_id:
            continue
        new_step = Step.objects.get(id=new_step_id)
        for i, old_rule in enumerate(old_step.rules.all().order_by('priority')):
            new_rule = new_step.rules.all().order_by('priority')[i]
            if old_rule.next_step_id:
                mapped = step_id_map.get(str(old_rule.next_step_id))
                new_rule.next_step_id = mapped if mapped else old_rule.next_step_id
            else:
                new_rule.next_step_id = None
            new_rule.save(update_fields=['next_step_id'])

    # Update start_step_id
    if source.start_step_id:
        mapped_start = step_id_map.get(str(source.start_step_id))
        if mapped_start:
            new_workflow.start_step_id = mapped_start
            new_workflow.save(update_fields=['start_step_id'])

    return new_workflow


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on workflows.

    GET    /api/workflows/           → list (paginated)
    POST   /api/workflows/           → create
    GET    /api/workflows/{id}/      → detail (with steps+rules)
    PUT    /api/workflows/{id}/      → update (creates new version!)
    DELETE /api/workflows/{id}/      → soft delete
    GET    /api/workflows/{id}/versions/ → version history
    POST   /api/workflows/{id}/rollback/ → rollback to target version
    """
    filter_backends_classes = []
    search_fields = ['name']
    ordering_fields = ['created_at', 'name', 'version']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'rollback'):
            return [IsAuthenticated(), IsCompanyAdmin()]
        return [IsAuthenticated(), IsCompanyMember()]

    def get_queryset(self):
        user = self.request.user
        if not user.company:
            return Workflow.objects.none()
        qs = Workflow.objects.filter(company=user.company)
        is_active = self.request.query_params.get('is_active')
        search = self.request.query_params.get('search')
        ordering = self.request.query_params.get('ordering', '-created_at')
        if is_active is not None:
            active = is_active.lower() in ('true', '1', 'yes')
            qs = qs.filter(is_active=active)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs.order_by(ordering)

    def get_serializer_class(self):
        if self.action == 'list':
            return WorkflowListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return WorkflowCreateUpdateSerializer
        return WorkflowDetailSerializer

    @swagger_auto_schema(
        operation_summary='List workflows (company-filtered, paginated)',
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('ordering', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
        tags=['Workflows'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Create new workflow',
        tags=['Workflows'],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workflow = Workflow.objects.create(
            company=request.user.company,
            name=serializer.validated_data['name'],
            input_schema=serializer.validated_data.get('input_schema', {'fields': []}),
            version=1,
            is_active=True,
        )
        return Response(WorkflowDetailSerializer(workflow).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='Get workflow detail with nested steps and rules',
        tags=['Workflows'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Update workflow — creates a new locked version',
        operation_description='Editing a workflow ALWAYS creates a new version. The old version is locked forever.',
        tags=['Workflows'],
    )
    def update(self, request, *args, **kwargs):
        """
        PUT /api/workflows/{id}/
        Auto version creation logic:
        1. Get current active workflow
        2. Lock it (is_active = False)
        3. Create new workflow with version+1
        4. Copy all steps and their rules
        5. Apply changes from request
        """
        instance = self.get_object()

        serializer = WorkflowCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Lock current version
        instance.is_active = False
        instance.save(update_fields=['is_active'])

        # Determine new version number
        max_version = Workflow.objects.filter(
            company=instance.company,
            name=instance.name,
        ).order_by('-version').values_list('version', flat=True).first() or instance.version

        new_workflow = _copy_workflow(
            source=instance,
            new_version=max_version + 1,
            company=instance.company,
            overrides=serializer.validated_data,
        )

        return Response(WorkflowDetailSerializer(new_workflow).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='Soft delete workflow (sets is_active=False)',
        tags=['Workflows'],
    )
    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/workflows/{id}/
        Soft delete only — never removes from database.
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response({'detail': 'Workflow deactivated successfully.'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='List all versions of this workflow',
        tags=['Workflows'],
    )
    @action(detail=True, methods=['get'], url_path='versions')
    def versions(self, request, pk=None):
        """
        GET /api/workflows/{id}/versions/
        Returns all versions with same workflow name for the company.
        """
        instance = self.get_object()
        all_versions = Workflow.objects.filter(
            company=instance.company,
            name=instance.name,
        ).order_by('-version')
        serializer = WorkflowVersionSerializer(all_versions, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary='Rollback to a previous workflow version',
        operation_description='Creates a new version copying the target version\'s steps and rules.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'target_version': openapi.Schema(type=openapi.TYPE_INTEGER)},
            required=['target_version'],
        ),
        tags=['Workflows'],
    )
    @action(detail=True, methods=['post'], url_path='rollback',
            permission_classes=[IsAuthenticated, IsCompanyAdmin])
    def rollback(self, request, pk=None):
        """
        POST /api/workflows/{id}/rollback/
        Rollback logic:
        1. Find target version row
        2. Set current active → is_active=False
        3. Copy target version as new row with version = current_max + 1
        4. Copy all steps + rules from target
        """
        current = self.get_object()
        target_version = request.data.get('target_version')

        if not target_version:
            return Response({'detail': 'target_version is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_workflow = Workflow.objects.get(
                company=current.company,
                name=current.name,
                version=int(target_version),
            )
        except Workflow.DoesNotExist:
            return Response(
                {'detail': f'Version {target_version} not found for workflow "{current.name}".'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Lock current active version
        active_version = Workflow.objects.filter(
            company=current.company,
            name=current.name,
            is_active=True,
        ).first()
        if active_version:
            active_version.is_active = False
            active_version.save(update_fields=['is_active'])

        # Compute new version number
        max_version = Workflow.objects.filter(
            company=current.company,
            name=current.name,
        ).order_by('-version').values_list('version', flat=True).first() or 0

        new_workflow = _copy_workflow(
            source=target_workflow,
            new_version=max_version + 1,
            company=current.company,
        )

        return Response(WorkflowDetailSerializer(new_workflow).data, status=status.HTTP_201_CREATED)
