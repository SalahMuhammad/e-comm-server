from rest_framework import viewsets, permissions as drf_permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import Permission, Group
from .serializers import (
    PermissionSerializer,
    GroupSerializer,
    GroupCreateUpdateSerializer
)
from .filters import PermissionFilter, GroupFilter


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for listing available permissions.
    Requires 'view' permission on auth.Permission model.
    Supports filtering by app_label, codename, name, and search.
    """
    queryset = Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'codename')
    serializer_class = PermissionSerializer
    permission_classes = [drf_permissions.DjangoModelPermissions]
    pagination_class = None  # Disable pagination to show all permissions
    filter_backends = [DjangoFilterBackend]
    filterset_class = PermissionFilter


class GroupViewSet(viewsets.ModelViewSet):
    """
    Full CRUD viewset for groups.
    Requires appropriate model permissions (add_group, change_group, delete_group, view_group).
    Supports filtering by name.
    """
    queryset = Group.objects.all().prefetch_related('permissions')
    permission_classes = [drf_permissions.DjangoModelPermissions]
    pagination_class = None  # Disable pagination to show all groups
    filter_backends = [DjangoFilterBackend]
    filterset_class = GroupFilter
    
    def get_serializer_class(self):
        """Use different serializers for read vs write operations"""
        if self.action in ['create', 'update', 'partial_update']:
            return GroupCreateUpdateSerializer
        return GroupSerializer
        
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """Get all permissions for a specific group"""
        group = self.get_object()
        permissions = group.permissions.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)
