from django_filters import rest_framework as filters
from employees.models import Employee



class EmployeeFilter(filters.FilterSet):
	first_name = filters.CharFilter(lookup_expr='icontains')
	last_name = filters.CharFilter(lookup_expr='icontains')
	email = filters.CharFilter(lookup_expr='icontains')
	phone_number = filters.CharFilter(lookup_expr='icontains')


	class Meta:
		model = Employee
		fields = [
			'first_name', 
			'last_name',
			'email',
			'phone_number', 
		]
