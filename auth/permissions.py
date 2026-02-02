from rest_framework.permissions import BasePermission
from django.contrib.auth.mixins import PermissionRequiredMixin
from requests_logs.models import RequestLog
from auth.utilities import JWTUtilities
from django.contrib.sessions.models import Session
from users.models import User


class IsLoggedIn(BasePermission):
    def has_permission(self, request, view):
        permissions = request.auth
        return permissions.get('is_logged_in', False)
    

class DynamicPermission(PermissionRequiredMixin):
    """A mixin that dynamically determines the required permissions based on the view and model."""
    
    def has_permission(self, request, view):
        """
        Override this method to dynamically determine the permissions required.
        Returns a list of permission strings.
        """
        # First check if password change is required
        if hasattr(request.user, 'password_change_required') and request.user.password_change_required:
            # Allow these specific endpoints
            allowed_paths = [
                '/api/users/change-password/',
                '/api/users/logout/',
            ]
            
            # Also allow GET requests to /api/users/ to fetch user info
            if request.path == '/api/users/' and request.method == 'GET':
                return True
            
            # Check if current path is in allowed list - return True to allow
            if request.path in allowed_paths:
                return True
            
            # Block all other endpoints when password change is required
            return False
        
        # Continue with normal permission checks
        if request.user.is_superuser:
            return True

        view_level = view.level if hasattr(view, 'level') else None
        try:
            model = view.queryset.model
            app_label = model._meta.app_label
            model_name = model._meta.model_name
        except:
            try: 
                session = Session.objects.get(session_key=request.COOKIES.get('sessionid'))
                
                session_data = session.get_decoded()
                
                id = session_data.get('_auth_user_id')
                if User.objects.get(pk=id).is_superuser:
                    return True
            except:
                pass
        
        if view_level and request.user.user_permissions.filter(codename=view_level).exists():
            return True

        if request.method == 'GET':
            action = 'view'
        elif request.method == 'POST':
            action = 'add'
        elif request.method in ['PUT', 'PATCH']:
            action = 'change'
        elif request.method == 'DELETE':
            action = 'delete'
        else:
            action = 'view'

        # Construct the permission string: app_label.action_modelname
        # permission = f"{app_label}.{action}_{model_name}"
        try:
            permission = f"{action}_{model_name}"
            
            # Check direct user permissions
            if request.user.user_permissions.filter(codename=permission).exists():
                return True
                
            # Check group permissions
            user_groups = request.user.groups.values_list('permissions__codename', flat=True)
            return permission in user_groups
        except Exception as e:
            return False
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request=request, view=view)


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
    

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