from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget
from finance.transfer.models import MoneyTransfer



class TransferFilter(filters.FilterSet):
	from_vault__account_name = filters.CharFilter(lookup_expr='icontains')
	to_vault__account_name = filters.CharFilter(lookup_expr='icontains')
	date_range = filters.DateFromToRangeFilter(field_name='date', widget=RangeWidget(attrs={'type': 'date'}))
	notes = filters.CharFilter(lookup_expr='icontains')
	date = filters.CharFilter(lookup_expr='icontains')



	class Meta:
		model = MoneyTransfer
		fields = [
			'from_vault__account_name',
			'to_vault__account_name', 
			'date_range',
			'transfer_type',
			'notes',
			'date',
		]
