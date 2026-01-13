from django_filters import rest_framework as filters
from finance.vault_and_methods.models import BusinessAccount



class AccountsFilter(filters.FilterSet):
	account_name = filters.CharFilter(lookup_expr='icontains')



	class Meta:
		model = BusinessAccount
		fields = [
			'account_name',
			'is_active',
		]
