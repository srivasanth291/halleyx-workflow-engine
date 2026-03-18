from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from apps.workflows.models import Workflow
from apps.workflows.serializers import WorkflowSerializer, WorkflowDetailSerializer
from apps.authentication.permissions import IsCompanyAdmin, IsCompanyMember
from apps.steps.models import Step
from apps.rules.models import Rule
from django.db import transaction

class WorkflowViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']

    def get_queryset(self):
        return Workflow.objects.filter(company=self.request.user.company)

    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return WorkflowDetailSerializer
        return WorkflowSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'versions', 'execute']:
            permission_classes = [IsCompanyMember]
        else:
            permission_classes = [IsCompanyAdmin]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, version=1)

    def update(self, request, *args, **kwargs):
        current = self.get_object()
        
        with transaction.atomic():
            current.is_active = False
            current.save()
            
            new_workflow = Workflow.objects.create(
                company=current.company,
                name=request.data.get('name', current.name),
                version=current.version + 1,
                is_active=True,
                input_schema=request.data.get('input_schema', current.input_schema),
                start_step_id=None
            )

            old_steps = current.steps.all().order_by('order')
            step_mapping = {}
            for step in old_steps:
                new_step = Step.objects.create(
                    workflow=new_workflow,
                    name=step.name,
                    step_type=step.step_type,
                    order=step.order,
                    metadata=step.metadata
                )
                step_mapping[str(step.id)] = str(new_step.id)

            req_start_step = request.data.get('start_step_id')
            if req_start_step and str(req_start_step) in step_mapping:
                new_workflow.start_step_id = step_mapping[str(req_start_step)]
                new_workflow.save()
            elif current.start_step_id and str(current.start_step_id) in step_mapping:
                new_workflow.start_step_id = step_mapping[str(current.start_step_id)]
                new_workflow.save()

            for step in old_steps:
                new_step_id = step_mapping[str(step.id)]
                for rule in step.rules.all():
                    new_next_step_id = None
                    if rule.next_step_id and str(rule.next_step_id) in step_mapping:
                        new_next_step_id = step_mapping[str(rule.next_step_id)]
                    
                    Rule.objects.create(
                        step_id=new_step_id,
                        condition=rule.condition,
                        next_step_id=new_next_step_id,
                        priority=rule.priority
                    )

        return Response(WorkflowSerializer(new_workflow).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        instance = self.get_object()
        versions = Workflow.objects.filter(company=self.request.user.company, name=instance.name).order_by('-version')
        serializer = WorkflowSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        instance = self.get_object()
        target_version = request.data.get('target_version')
        if not target_version:
            return Response({"error": "target_version is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            target_workflow = Workflow.objects.get(company=self.request.user.company, name=instance.name, version=target_version)
        except Workflow.DoesNotExist:
            return Response({"error": "Version not found"}, status=status.HTTP_404_NOT_FOUND)

        current_max = Workflow.objects.filter(company=self.request.user.company, name=instance.name).order_by('-version').first()
        
        with transaction.atomic():
            new_workflow = Workflow.objects.create(
                company=target_workflow.company,
                name=target_workflow.name,
                version=current_max.version + 1,
                is_active=True,
                input_schema=target_workflow.input_schema,
                start_step_id=None
            )
            
            old_steps = target_workflow.steps.all().order_by('order')
            step_mapping = {}
            for step in old_steps:
                new_step = Step.objects.create(
                    workflow=new_workflow,
                    name=step.name,
                    step_type=step.step_type,
                    order=step.order,
                    metadata=step.metadata
                )
                step_mapping[str(step.id)] = str(new_step.id)

            if target_workflow.start_step_id and str(target_workflow.start_step_id) in step_mapping:
                new_workflow.start_step_id = step_mapping[str(target_workflow.start_step_id)]
                new_workflow.save()

            for step in old_steps:
                new_step_id = step_mapping[str(step.id)]
                for rule in step.rules.all():
                    new_next_step_id = None
                    if rule.next_step_id and str(rule.next_step_id) in step_mapping:
                        new_next_step_id = step_mapping[str(rule.next_step_id)]
                    Rule.objects.create(
                        step_id=new_step_id,
                        condition=rule.condition,
                        next_step_id=new_next_step_id,
                        priority=rule.priority
                    )
            
            Workflow.objects.filter(company=self.request.user.company, name=instance.name).exclude(id=new_workflow.id).update(is_active=False)

        return Response(WorkflowSerializer(new_workflow).data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        data = request.data.get('data', {})
        max_iterations = request.data.get('max_iterations', 10)
        from apps.engine.executor import ExecutionEngine
        from apps.executions.serializers import ExecutionSerializer
        engine = ExecutionEngine()
        execution = engine.start_execution(self.get_object().id, data, request.user, max_iterations=max_iterations)
        return Response(ExecutionSerializer(execution).data, status=status.HTTP_201_CREATED)
