from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget
from finance.expenses.models import Expense, Category



class ExpensesFilter(filters.FilterSet):
	business_account__account_name = filters.CharFilter(lookup_expr='icontains')
	category__name = filters.CharFilter(lookup_expr='icontains')
	date_range = filters.DateFromToRangeFilter(field_name='date', widget=RangeWidget(attrs={'type': 'date'}))
	notes = filters.CharFilter(lookup_expr='icontains')
	date = filters.CharFilter(lookup_expr='icontains')



	class Meta:
		model = Expense
		fields = [
			'business_account__account_name', 
			'category__name',
			'date_range', 
			'status', 
			'notes',
			'date',
		]


class CategoryFilter(filters.FilterSet):
	name = filters.CharFilter(lookup_expr='icontains')
	description = filters.CharFilter(lookup_expr='icontains')

	class Meta:
		model = Category
		fields = ['name', 'description']
