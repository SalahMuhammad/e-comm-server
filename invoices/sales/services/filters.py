from django_filters import rest_framework as filters
from invoices.sales.models import SalesInvoice
from common.encoder import MixedRadixEncoder


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
	pass


class SalesInvoiceFilter(filters.FilterSet):
	"""
	FilterSet for SalesInvoice model to enable filtering by:
	- owner: Numeric ID (exact match)
	- owner__name: Owner name search (case-insensitive contains)
	- status: Invoice status code (comma-separated values supported)
	- no: Invoice number search (decoded from hashed ID)
	"""
	owner = filters.NumberFilter(field_name='owner_id')
	owner__name = filters.CharFilter(field_name='owner__name', lookup_expr='icontains')
	status = NumberInFilter(field_name='status', lookup_expr='in')
	no = filters.CharFilter(method='filter_by_invoice_number')

	class Meta:
		model = SalesInvoice
		fields = [
			'owner',
			'owner__name',
			'status',
			'no'
		]

	def filter_by_invoice_number(self, queryset, name, value):
		"""
		Custom filter method to search invoices by their number.
		Supports:
		1. Partial numeric ID (e.g., "1000" finds IDs containing 1000 anywhere)
		2. Partial encoded/hashed ID (case-insensitive, e.g., "0fm" finds all encoded IDs containing "0fm")
		Results are sorted by issue_date descending (newest first).
		"""
		if not value:
			return queryset
		
		# Try numeric ID first (supports partial match anywhere in the ID)
		if value.isdigit():
			# Use __contains to allow partial ID search anywhere in the ID
			# Convert ID to string for comparison
			from django.db.models.functions import Cast
			from django.db.models import CharField
			return queryset.annotate(
				id_str=Cast('id', CharField())
			).filter(id_str__contains=value).order_by('-issue_date', '-created_at')
		
		# For non-numeric values (encoded IDs), support partial matching
		# This requires encoding each ID and checking if the search value appears anywhere
		encoder = MixedRadixEncoder()
		matching_ids = []
		
		# Convert search value to lowercase for case-insensitive comparison
		search_value_lower = value.lower()
		
		# Note: This iterates through the queryset, which is fine if other filters 
		# (owner, status) are applied first to reduce the dataset
		for invoice in queryset:
			try:
				encoded_id = encoder.encode(invoice.id)
				# Check if search value appears anywhere in the encoded ID (case-insensitive)
				if search_value_lower in encoded_id.lower():
					matching_ids.append(invoice.id)
			except Exception:
				continue
		
		# Filter to only matching IDs and sort by issue_date descending (newest first)
		if matching_ids:
			return queryset.filter(pk__in=matching_ids).order_by('-issue_date', '-created_at')
		else:
			return queryset.none()
