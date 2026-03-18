from rest_framework import permissions

class IsCompanyAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role and 
            request.user.role.is_admin
        )

class IsCompanyMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.company is not None)

class IsApprover(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Specific step access will be checking object permission.
        # Implemented for executions and steps logic later
        pass
