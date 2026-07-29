from rest_framework.permissions import BasePermission
from common.services.customeConfigurationHandler import customeViewsUserPermissionHandler



class ConfigurationBasedCustomeViewsPermission(BasePermission):
    """DRF permission class that dynamically determines permissions based on the view."""
    
    def has_permission(self, request, view):        
        # This will now successfully return "buyerSupplier_creditBalanceList"
        ___view_id = view.kwargs.get('___view_id', None)
        return customeViewsUserPermissionHandler(request.user, ___view_id)
