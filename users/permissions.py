from rest_framework.permissions import BasePermission


class RequirePasswordChangePermission(BasePermission):
    """
    Custom permission to block users who need to change their password.
    Users with password_change_required=True can only access:
    - /api/users/change-password/
    - /api/users/logout/
    - /api/users/ (GET only - to fetch user info)
    """
    
    def has_permission(self, request, view):
        # Allow unauthenticated requests
        if not request.user or not request.user.is_authenticated:
            return True
        
        # Check if password change is required
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
            
            # Block all other endpoints
            return False
        
        return True
    
    def get_message(self):
        return {
            'detail': 'Password change required. Please change your password before accessing other resources.',
            'detail_ar': 'يجب تغيير كلمة المرور. يرجى تغيير كلمة المرور قبل الوصول إلى الموارد الأخرى.'
        }
