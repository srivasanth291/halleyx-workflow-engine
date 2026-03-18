from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.steps.models import Step
from apps.steps.serializers import StepSerializer, StepCreateUpdateSerializer
from apps.authentication.permissions import IsCompanyAdmin
from apps.workflows.models import Workflow
from django.db import transaction

class StepViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCompanyAdmin]
    
    def get_queryset(self):
        return Step.objects.filter(workflow__company=self.request.user.company)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StepCreateUpdateSerializer
        return StepSerializer

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        workflow_id = request.data.get('workflow_id')
        step_orders = request.data.get('step_orders', [])
        
        if not workflow_id or not step_orders:
            return Response({"error": "workflow_id and step_orders are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workflow = Workflow.objects.get(id=workflow_id, company=self.request.user.company)
        except Workflow.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            for item in step_orders:
                Step.objects.filter(id=item['step_id'], workflow=workflow).update(order=item['order'])

        return Response({"status": "reordered"})
