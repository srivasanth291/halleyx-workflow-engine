from rest_framework import viewsets, status, views, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from apps.executions.models import Execution, EmailNotification, ActionToken
from django.http import HttpResponse
from apps.executions.serializers import ExecutionSerializer, EmailNotificationSerializer
from apps.authentication.permissions import IsCompanyMember, IsCompanyAdmin
from apps.engine.executor import ExecutionEngine

class ExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExecutionSerializer
    permission_classes = [IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['workflow_id', 'status', 'assigned_to']
    search_fields = ['assigned_to', 'workflow__name']

    def get_queryset(self):
        return Execution.objects.filter(company=self.request.user.company)

    @action(detail=False, methods=['get'], url_path='pending-tasks')
    def pending_tasks(self, request):
        # Tasks assigned to current user
        tasks = Execution.objects.filter(
            company=self.request.user.company,
            assigned_to=self.request.user.email,
            status='in_progress'
        )
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        execution = self.get_object()
        comment = request.data.get('comment', 'Approved')
        engine = ExecutionEngine()
        updated_execution = engine.handle_approval_action(execution.id, execution.current_step_id, request.user, 'approve', comment)
        return Response(ExecutionSerializer(updated_execution).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        execution = self.get_object()
        comment = request.data.get('comment', 'Rejected')
        engine = ExecutionEngine()
        updated_execution = engine.handle_approval_action(execution.id, execution.current_step_id, request.user, 'reject', comment)
        return Response(ExecutionSerializer(updated_execution).data)

    @action(detail=True, methods=['post'])
    def return_step(self, request, pk=None):
        execution = self.get_object()
        comment = request.data.get('comment', 'Returned')
        engine = ExecutionEngine()
        updated_execution = engine.handle_approval_action(execution.id, execution.current_step_id, request.user, 'return', comment)
        return Response(ExecutionSerializer(updated_execution).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        engine = ExecutionEngine()
        updated_execution = engine.cancel_execution(self.get_object().id, request.user)
        return Response(ExecutionSerializer(updated_execution).data)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        engine = ExecutionEngine()
        updated_execution = engine.retry_execution(self.get_object().id, request.user)
        return Response(ExecutionSerializer(updated_execution).data)

class AuditLogView(views.APIView):
    permission_classes = [IsCompanyAdmin]

    def get(self, request):
        company = request.user.company
        executions = Execution.objects.filter(company=company)
        
        stats = {
            "total": executions.count(),
            "completed": executions.filter(status='completed').count(),
            "failed": executions.filter(status='failed').count(),
            "pending": executions.filter(status='pending').count(),
            "canceled": executions.filter(status='canceled').count(),
            "in_progress": executions.filter(status='in_progress').count()
        }
        
        page = int(request.query_params.get('page', 1))
        page_size = 20
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_executions = executions[start:end]
        serializer = ExecutionSerializer(paginated_executions, many=True)
        
        return Response({
            "stats": stats,
            "count": stats["total"],
            "next": page + 1 if end < stats["total"] else None,
            "previous": page - 1 if page > 1 else None,
            "results": serializer.data
        })

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmailNotificationSerializer
    permission_classes = [IsCompanyMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'channel']

    def get_queryset(self):
        return EmailNotification.objects.filter(company=self.request.user.company)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({
            "total_sent": qs.filter(status='sent').count(),
            "total_failed": qs.filter(status='failed').count(),
            "total_pending": qs.filter(status='pending').count(),
            "channels": {
                "email": qs.filter(channel='email').count(),
                "slack": qs.filter(channel='slack').count(),
                "ui_message": qs.filter(channel='ui_message').count(),
            }
        })

    @action(detail=False, methods=['post'], url_path='test-email')
    def test_email(self, request):
        recipient = request.data.get('recipient')
        if not recipient:
            return Response({"success": False, "message": "Recipient required"}, status=400)
            
        from django.core.mail import send_mail
        from django.conf import settings
        
        try:
            send_mail(
                subject="Test Email from FlowEngine",
                message="This is a test email to verify your SMTP configuration.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            return Response({"success": True, "message": "Test email sent!"})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=400)

class ActionTokenView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token_id):
        try:
            token = ActionToken.objects.get(id=token_id)
            if not token.is_valid():
                return HttpResponse("This link has expired or already been used.", status=400)
            
            engine = ExecutionEngine()
            # We pass None for user because this is an anonymous action via secure token
            engine.handle_approval_action(token.execution.id, token.step_id, None, token.action, f"Action via email link ({token.action})")
            
            token.is_used = True
            token.save()
            
            return HttpResponse(f"Successfully {token.action}ed the request. You can close this window.")
        except ActionToken.DoesNotExist:
            return HttpResponse("Invalid link.", status=404)
        except Exception as e:
            return HttpResponse(f"Error processing action: {str(e)}", status=500)
