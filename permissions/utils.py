"""
Utility functions for the permissions app.
"""
from django.urls import get_resolver
from django.contrib.auth.models import Permission
import inspect


def get_superuser_required_permissions():
    """
    Automatically detect which permissions require superuser status by
    scanning URL patterns for views that use SuperUserRequiredMixin.
    
    Returns:
        set: A set of permission codenames that require superuser status
    """
    # Import SuperUserRequiredMixin - adjust import path if it's defined elsewhere
    try:
        from finance.vault_and_methods.views import SuperUserRequiredMixin
    except ImportError:
        # If the mixin isn't available, return empty set
        return set()
    
    superuser_required_codenames = set()
    
    # Get the root URL resolver
    resolver = get_resolver()
    
    # Recursively scan all URL patterns
    def scan_patterns(url_patterns, prefix=''):
        for pattern in url_patterns:
            # Check if this is a URL pattern with a view
            if hasattr(pattern, 'callback') and pattern.callback:
                view = pattern.callback
                
                # Handle class-based views
                if hasattr(view, 'view_class'):
                    view_class = view.view_class
                elif hasattr(view, 'cls'):
                    view_class = view.cls
                else:
                    # Try to get the class from the view function
                    view_class = getattr(view, '__self__', None)
                    if view_class:
                        view_class = view_class.__class__
                
                # Check if the view uses SuperUserRequiredMixin
                if view_class and inspect.isclass(view_class):
                    # Check if SuperUserRequiredMixin is in the MRO
                    if issubclass(view_class, SuperUserRequiredMixin):
                        # Try to determine the permission required
                        # This is a simplified approach - you may need to enhance this
                        # based on how your views define permissions
                        
                        # For now, we'll mark specific known views
                        view_name = view_class.__name__
                        
                        # Map known views to their permissions
                        view_permission_map = {
                            'VaultBalanceAPIView': 'view_businessaccount',
                            'AccountMovementListView': 'view_accountmovement',
                        }
                        
                        if view_name in view_permission_map:
                            superuser_required_codenames.add(view_permission_map[view_name])
            
            # Recursively scan nested URL patterns
            if hasattr(pattern, 'url_patterns'):
                scan_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
    
    # Start scanning from root
    try:
        scan_patterns(resolver.url_patterns)
    except Exception as e:
        # If scanning fails, log the error and return empty set
        print(f"Error scanning URL patterns for superuser permissions: {e}")
        return set()
    
    return superuser_required_codenames


# Cache the result to avoid re-scanning on every request
_cached_superuser_perms = None

def get_cached_superuser_required_permissions():
    """
    Get cached superuser-required permissions.
    The cache is cleared on server restart.
    """
    global _cached_superuser_perms
    if _cached_superuser_perms is None:
        _cached_superuser_perms = get_superuser_required_permissions()
    return _cached_superuser_perms
