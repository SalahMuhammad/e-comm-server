from django_filters import rest_framework as filters
from invoices.purchase.models import PurchaseInvoices
from common.encoder import MixedRadixEncoder


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
	pass


class PurchaseInvoiceFilter(filters.FilterSet):
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
		model = PurchaseInvoices
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
		# Get all invoice IDs from the queryset (not slicing first to avoid missing matches)
		encoder = MixedRadixEncoder()
		matching_ids = []
		
		# Convert search value to lowercase for case-insensitive comparison
		search_value_lower = value.lower()
		
		# Get all IDs from the queryset (just IDs, not full objects for performance)
		# Order by most recent first for better user experience
		all_ids = queryset.order_by('-issue_date', '-created_at').values_list('id', flat=True)
		
		# Iterate through all IDs and check encoded values
		# Note: This may be slow for very large datasets, but ensures all matches are found
		for invoice_id in all_ids:
			try:
				encoded_id = encoder.encode(invoice_id)
				# Check if search value appears anywhere in the encoded ID (case-insensitive)
				if search_value_lower in encoded_id.lower():
					matching_ids.append(invoice_id)
			except Exception:
				continue
		
		# Filter to only matching IDs and sort by issue_date descending (newest first)
		if matching_ids:
			return queryset.filter(pk__in=matching_ids).distinct().order_by('-issue_date', '-created_at')
		else:
			return queryset.none()
