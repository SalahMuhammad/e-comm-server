from rest_framework import viewsets, permissions as drf_permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import ProtectedError
from users.models import User
from .serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer
)
from .filters import UserFilter


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    CRUD viewset for user management.
    Only accessible to superusers.
    Sets password_change_required=True on user creation.
    Supports filtering by username, is_active, is_superuser, is_staff.
    """
    queryset = User.objects.all().prefetch_related('groups', 'user_permissions')
    permission_classes = [drf_permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    
    def get_queryset(self):
        """Only allow superusers to access"""
        if not self.request.user.is_superuser:
            return User.objects.none()
        return super().get_queryset()
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        else:  # retrieve
            return UserDetailSerializer
            
    def update(self, request, *args, **kwargs):
        """Prevent users from editing their own account"""
        instance = self.get_object()
        if instance.id == request.user.id:
            return Response(
                {'detail': 'You cannot edit your own account.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Create user - password_change_required is set in serializer"""
        serializer.save()
        
    def destroy(self, request, *args, **kwargs):
        """Prevent deleting the last superuser or self. Handle ProtectedError by deactivating."""
        user = self.get_object()
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response(
                {'detail': 'You cannot delete your own account.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.is_superuser:
            superuser_count = User.objects.filter(is_superuser=True).count()
            if superuser_count <= 1:
                return Response(
                    {'detail': 'Cannot delete the last superuser account.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:        
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            user.is_active = False
            user.save()
            return Response(
                {'warning': 'User cannot be deleted due to existing relationships. User has been deactivated instead.'},
                status=status.HTTP_200_OK
            )
