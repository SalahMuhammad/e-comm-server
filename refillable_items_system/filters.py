from django_filters import rest_framework as filters
from .models import RefundedRefillableItem, RefilledItem


class RefundedRefillableItemFilter(filters.FilterSet):
    """
    FilterSet for RefundedRefillableItem:
    - client: case-insensitive match against owner (Party) name
    - item: case-insensitive match against item name
    - repo: case-insensitive match against repository name
    - notes: case-insensitive contains
    - date_after: date >= value
    - date_before: date <= value
    """
    client = filters.CharFilter(field_name='owner__name', lookup_expr='icontains', label='Client name')
    item = filters.CharFilter(field_name='item__name', lookup_expr='icontains', label='Item name')
    repo = filters.CharFilter(field_name='repository__name', lookup_expr='icontains', label='Repository name')
    notes = filters.CharFilter(field_name='notes', lookup_expr='icontains', label='Notes')
    date_after = filters.DateFilter(field_name='date', lookup_expr='gte', label='Date from')
    date_before = filters.DateFilter(field_name='date', lookup_expr='lte', label='Date to')

    class Meta:
        model = RefundedRefillableItem
        fields = ['client', 'item', 'repo', 'notes', 'date_after', 'date_before']


class RefilledItemFilter(filters.FilterSet):
    """
    FilterSet for RefilledItem:
    - ritem: case-insensitive match against refilled item name
    - uitem: case-insensitive match against used (ore) item name
    - note: case-insensitive contains on notes
    - repo: case-insensitive match against repository name
    - employee_name: case-insensitive match against employee name
    - date_after: date >= value
    - date_before: date <= value
    """
    ritem = filters.CharFilter(field_name='refilled_item__name', lookup_expr='icontains', label='Refilled item')
    uitem = filters.CharFilter(field_name='used_item__item__name', lookup_expr='icontains', label='Used item')
    note = filters.CharFilter(field_name='notes', lookup_expr='icontains', label='Notes')
    repo = filters.CharFilter(field_name='repository__name', lookup_expr='icontains', label='Repository name')
    employee_name = filters.CharFilter(field_name='employee__name', lookup_expr='icontains', label='Employee name')
    date_after = filters.DateFilter(field_name='date', lookup_expr='gte', label='Date from')
    date_before = filters.DateFilter(field_name='date', lookup_expr='lte', label='Date to')

    class Meta:
        model = RefilledItem
        fields = ['ritem', 'uitem', 'note', 'repo', 'employee_name', 'date_after', 'date_before']
