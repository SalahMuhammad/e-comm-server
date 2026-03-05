from django_filters import rest_framework as filters
from django.db.models import Q
from users.models import User


class UserFilter(filters.FilterSet):
    """
    FilterSet for User model with support for:
    - name search: case-insensitive contains across first_name and last_name
    - username search (case-insensitive contains)
    - is_active exact match
    - is_superuser exact match
    - is_staff exact match
    """
    name = filters.CharFilter(method='filter_by_name', label='Name')
    username = filters.CharFilter(lookup_expr='icontains')
    s = filters.CharFilter(field_name='username', lookup_expr='icontains')  # Backward compatibility
    is_active = filters.BooleanFilter()
    is_superuser = filters.BooleanFilter()
    is_staff = filters.BooleanFilter()

    def filter_by_name(self, queryset, name, value):
        """Filter users by first_name or last_name (case-insensitive contains)."""
        return queryset.filter(
            Q(first_name__icontains=value) | Q(last_name__icontains=value)
        )

    class Meta:
        model = User
        fields = ['name', 'username', 's', 'is_active', 'is_superuser', 'is_staff']
