from rest_framework.permissions import BasePermission

class IsStaff(BasePermission):
    def has_permission(self, request, view):
        permissions = request.auth
        return permissions['is_staff']
    

class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        permissions = request.auth
        return permissions['is_superuser']
    

class IsSuperuserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.auth['is_superuser']
    

class RepositoryPermission(BasePermission):
    def has_permission(self, request, view):
        # Map actions to required permissions
        permission_map = {
            'GET': 'repositories.view_repositories',
            'POST': 'repositories.add_repositories',
            'PUT': 'repositories.change_repositories',
            'PATCH': 'repositories.change_repositories',
            'DELETE': 'repositories.delete_repositories',
        }

        required_permission = permission_map.get(request.method)
        if required_permission:
            return required_permission in request.auth['user_permissions']
        return False


class OwnersPermission(BasePermission):
    def has_permission(self, request, view):
        # Map actions to required permissions
        permission_map = {
            'GET': 'owners.view_owner',
            'POST': 'owners.add_owner',
            'PUT': 'owners.change_owner',
            'PATCH': 'owners.change_owner',
            'DELETE': 'owners.delete_owner',
        }

        required_permission = permission_map.get(request.method)
        if required_permission:
            return required_permission in request.auth['user_permissions']
        return False