from django_filters import rest_framework as filters
from django.contrib.auth.models import Permission, Group


class PermissionFilter(filters.FilterSet):
    """
    FilterSet for Permission model with support for:
    - app_label exact match
    - codename search (case-insensitive contains)
    - name search (case-insensitive contains)
    - search parameter for both codename and name
    """
    app_label = filters.CharFilter(field_name='content_type__app_label')
    codename = filters.CharFilter(lookup_expr='icontains')
    name = filters.CharFilter(lookup_expr='icontains')
    search = filters.CharFilter(method='search_filter')
    
    class Meta:
        model = Permission
        fields = ['app_label', 'codename', 'name', 'search']
    
    def search_filter(self, queryset, name, value):
        """Search in both codename and name fields"""
        from django.db.models import Q
        return queryset.filter(
            Q(codename__icontains=value) | Q(name__icontains=value)
        )


class GroupFilter(filters.FilterSet):
    """
    FilterSet for Group model with support for:
    - name search (case-insensitive contains)
    """
    name = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Group
        fields = ['name']
