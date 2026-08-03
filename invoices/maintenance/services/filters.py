from django_filters import rest_framework as filters
from invoices.maintenance.models import Maintenance



class MaintenanceFilter(filters.FilterSet):
	"""
	FilterSet for SalesInvoice model to enable filtering by:
	- owner: Numeric ID (exact match)
	- owner__name: Owner name search (case-insensitive contains)
	- status: Invoice status code (comma-separated values supported)
	- no: Invoice number search (decoded from hashed ID)
	- note: Notes field search (case-insensitive contains)
	- itemdesc: Item description search (case-insensitive contains)
	- itemname: Item name search (case-insensitive contains)
	"""
	client_name = filters.CharFilter(field_name='client__name', lookup_expr='icontains')
	status = filters.CharFilter(field_name='status', lookup_expr='icontains')
	
	serial_numbers = filters.CharFilter(field_name='serial_number', lookup_expr='icontains')
	serial_number = filters.CharFilter(field_name='serial_number', lookup_expr='exact')
	notes = filters.CharFilter(field_name='notes', lookup_expr='icontains')
	malfunctions = filters.CharFilter(field_name='malfunctions', lookup_expr='icontains')

	date_in = filters.CharFilter(lookup_expr='icontains')
	maintenance_date = filters.CharFilter(lookup_expr='icontains')
	date_out = filters.CharFilter(lookup_expr='icontains')
	
	maintained_by = filters.CharFilter(field_name='maintained_by__first_name', lookup_expr='icontains')


	class Meta:
		model = Maintenance
		fields = []
