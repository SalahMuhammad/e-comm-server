from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget
from finance.reverse_payment.models import ReversePayment2



class ReversePaymentFilter(filters.FilterSet):
	notes = filters.CharFilter(lookup_expr='icontains')
	owner__name = filters.CharFilter(lookup_expr='icontains')
	business_account__account_name = filters.CharFilter(lookup_expr='icontains')
	date = filters.CharFilter(lookup_expr='icontains')
	date_range = filters.DateFromToRangeFilter(field_name='date', widget=RangeWidget(attrs={'type': 'date'}))
	owner = filters.CharFilter(field_name='owner__name', lookup_expr='icontains')
	no = filters.CharFilter(field_name='payment_ref', lookup_expr='icontains')



	class Meta:
		model = ReversePayment2
		fields = [
			'business_account__account_name', 
			'owner__name',
			'date',
			'date_range', 
			'status', 
			'notes',
			'owner',
			'no'
		]
