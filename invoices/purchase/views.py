from django.http import JsonResponse
from django.shortcuts import get_object_or_404
# models
from .models import PurchaseInvoices
from django.db import transaction
# 
from .serializers import InvoiceSerializer
from items.services.validate_items_stock import ValidateItemsStock
from common.views.CommonInvoiceViews import AbstractInvoiceDetailView, AbstractInvoiceListCreateView
# 
from rest_framework.decorators import api_view
# django filters
from django_filters.rest_framework import DjangoFilterBackend
from .services.filters import PurchaseInvoiceFilter



@api_view(['POST'])
def toggle_repository_permit(request, *args, **kwargs):
	"""
		View to toggle the repository_permit field of an invoice.
	"""
	invoice = get_object_or_404(PurchaseInvoices, id=kwargs['pk'])

	with transaction.atomic():
		# adjust_stock(invoice.p_invoice_items.all(), -1 if invoice.repository_permit else 1)
		invoice.repository_permit = not invoice.repository_permit
		invoice.save()

		a = ValidateItemsStock()
		items_ids = [item.item.id for item in invoice.p_invoice_items.all()]
		a.stock_validation(item_ids=items_ids, log_mismatches=False, raise_on_negative=True)

	return JsonResponse({
		"success": True,
		"repository_permit": invoice.repository_permit
	})

class ListCreateView(AbstractInvoiceListCreateView):
	CUSTOME_QUERYSET_MANAGER_CONFIG = {
        "model": 					PurchaseInvoices,
        "select_related_fields": 	('by', 'owner', ),
        "prefetch_related_fields":	('p_invoice_items__item', 'p_invoice_items__repository', ),
    }

	serializer_class = InvoiceSerializer
	adjust_stock_sign = 1
	items_relation_name = 'p_invoice_items'
	# Adding filtering backends
	filter_backends = [DjangoFilterBackend]
	filterset_class = PurchaseInvoiceFilter


class DetailView(AbstractInvoiceDetailView):
	CUSTOME_QUERYSET_MANAGER_CONFIG = {
        "model": 					PurchaseInvoices,
        "select_related_fields": 	('by', 'owner', ),
        "prefetch_related_fields":	('p_invoice_items__item', 'p_invoice_items__repository', ),
    }

	serializer_class = InvoiceSerializer
	adjust_stock_sign = 1
	items_relation_name = 'p_invoice_items'
