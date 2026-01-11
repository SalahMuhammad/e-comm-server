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
	- note: Notes field search (case-insensitive contains)
	- itemdesc: Item description search (case-insensitive contains)
	- itemname: Item name search (case-insensitive contains)
	"""
	owner = filters.NumberFilter(field_name='owner_id')
	owner__name = filters.CharFilter(field_name='owner__name', lookup_expr='icontains')
	status = NumberInFilter(field_name='status', lookup_expr='in')
	no = filters.CharFilter(method='filter_by_invoice_number')
	note = filters.CharFilter(field_name='notes', lookup_expr='icontains')
	itemdesc = filters.CharFilter(method='filter_by_item_description')
	itemname = filters.CharFilter(method='filter_by_item_name')

	class Meta:
		model = SalesInvoice
		fields = []

	def filter_by_item_description(self, queryset, name, value):
		"""
		Custom filter method for item description to apply distinct()
		and avoid duplicate results from JOIN operations.
		"""
		if not value:
			return queryset
		return queryset.filter(s_invoice_items__description__icontains=value).distinct()

	def filter_by_item_name(self, queryset, name, value):
		"""
		Custom filter method for item name to apply distinct()
		and avoid duplicate results from JOIN operations.
		"""
		if not value:
			return queryset
		return queryset.filter(s_invoice_items__item__name__icontains=value).distinct()

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
			).filter(id_str__contains=value).distinct().order_by('-issue_date', '-created_at')
		
		# For non-numeric values (encoded IDs), support partial matching
		# This requires encoding each ID and checking if the search value appears anywhere
		encoder = MixedRadixEncoder()
		matching_ids = []
		
		# Convert search value to lowercase for case-insensitive comparison
		search_value_lower = value.lower()
		
		# To optimize performance, limit the search to a reasonable number of records
		# Apply existing filters first, then check encoded IDs
		# Only iterate through up to 1000 records to prevent performance issues
		queryset_to_check = queryset.order_by('-issue_date', '-created_at')[:1000]
		
		for invoice in queryset_to_check:
			try:
				encoded_id = encoder.encode(invoice.id)
				# Check if search value appears anywhere in the encoded ID (case-insensitive)
				if search_value_lower in encoded_id.lower():
					matching_ids.append(invoice.id)
			except Exception:
				continue
		
		# Filter to only matching IDs and sort by issue_date descending (newest first)
		if matching_ids:
			return queryset.filter(pk__in=matching_ids).distinct().order_by('-issue_date', '-created_at')
		else:
			return queryset.none()
