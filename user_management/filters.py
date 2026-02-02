from django_filters import rest_framework as filters
from users.models import User


class UserFilter(filters.FilterSet):
    """
    FilterSet for User model with support for:
    - username search (case-insensitive contains)
    - is_active exact match
    - is_superuser exact match
    - is_staff exact match
    """
    username = filters.CharFilter(lookup_expr='icontains')
    s = filters.CharFilter(field_name='username', lookup_expr='icontains')  # Backward compatibility
    is_active = filters.BooleanFilter()
    is_superuser = filters.BooleanFilter()
    is_staff = filters.BooleanFilter()
    
    class Meta:
        model = User
        fields = ['username', 's', 'is_active', 'is_superuser', 'is_staff']
