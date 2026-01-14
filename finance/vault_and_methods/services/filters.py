from django_filters import rest_framework as filters
from finance.vault_and_methods.models import BusinessAccount



class AccountsFilter(filters.FilterSet):
	account_name = filters.CharFilter(lookup_expr='icontains')
	account_type__name = filters.CharFilter(lookup_expr='icontains')
	phone_number = filters.CharFilter(lookup_expr='icontains')
	bank_name = filters.CharFilter(lookup_expr='icontains')



	class Meta:
		model = BusinessAccount
		fields = [
			'account_name',
			'account_type__name',
			'phone_number',
			'bank_name',
			'is_active',
		]
