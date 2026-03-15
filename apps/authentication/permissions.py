"""
Authentication permissions.
"""
from rest_framework.permissions import BasePermission


class IsCompanyAdmin(BasePermission):
    """
    Allow only super_admin or admin roles.
    Used for: create/edit/delete workflows, steps, rules.
    """
    message = 'You must be a company admin to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('super_admin', 'admin')
        )


class IsCompanyMember(BasePermission):
    """
    Allow any authenticated user whose company matches the resource.
    Used for: view workflows, execute workflows, view executions.
    """
    message = 'You must be a member of this company to access this resource.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.company is not None
        )

    def has_object_permission(self, request, view, obj):
        # Object must belong to same company
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        if hasattr(obj, 'workflow') and hasattr(obj.workflow, 'company'):
            return obj.workflow.company == request.user.company
        return False


class IsApprover(BasePermission):
    """
    Allow: user.email == step.metadata.assignee_email
           OR user.role in [super_admin, admin]
    Used for: approve/reject/return approval steps.
    """
    message = 'You are not the designated approver for this step.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Admins can always override
        if user.role in ('super_admin', 'admin'):
            return True
        # Check if user is the assignee for current step
        if obj.current_step_id:
            try:
                from apps.steps.models import Step
                step = Step.objects.get(id=obj.current_step_id)
                assignee_email = step.metadata.get('assignee_email', '')
                return user.email == assignee_email
            except Exception:
                return False
        return False


class IsSuperAdmin(BasePermission):
    """Allow only super_admin role."""
    message = 'Only super admins can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'super_admin'
        )
