from django_filters import rest_framework as filters
from finance.debt_settlement.models import DebtSettlement


class DebtSettlementFilter(filters.FilterSet):
	owner__name = filters.CharFilter(lookup_expr='icontains')
	notes = filters.CharFilter(field_name='note', lookup_expr='icontains')
	date = filters.CharFilter(lookup_expr='icontains')
	# Alias for frontend compatibility
	owner = filters.CharFilter(field_name='owner__name', lookup_expr='icontains')


	class Meta:
		model = DebtSettlement
		fields = [
			'owner__name',
			'owner',
			'status',
			'notes',
			'date',
		]
