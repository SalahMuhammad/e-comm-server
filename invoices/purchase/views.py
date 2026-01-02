from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from items.models import Items
from .models import PurchaseInvoices
from .serializers import InvoiceSerializer
from common.views import AbstractInvoiceDetailView, AbstractInvoiceListCreateView
from common.utilities import adjust_stock
from items.services.validate_items_stock import ValidateItemsStock
from rest_framework.decorators import api_view
from django.db import transaction


@api_view(['POST'])
def toggle_repository_permit(request, *args, **kwargs):
	"""
		View to toggle the repository_permit field of an invoice.
	"""
	invoice = get_object_or_404(PurchaseInvoices, id=kwargs['pk'])

	with transaction.atomic():
		adjust_stock(invoice.p_invoice_items.all(), -1 if invoice.repository_permit else 1)
		invoice.repository_permit = not invoice.repository_permit
		invoice.save()

	a = ValidateItemsStock()
	items_ids = [item.item.id for item in invoice.p_invoice_items.all()]
	a.validate_stock(items=Items.objects.filter(id__in=items_ids))

	return JsonResponse({
		"success": True,
		"repository_permit": invoice.repository_permit
	})

class ListCreateView(AbstractInvoiceListCreateView):
	queryset = PurchaseInvoices.objects.select_related(
		'by', 
		'owner', 
	).prefetch_related(
		'p_invoice_items__item', 
		'p_invoice_items__repository'
	)
	serializer_class = InvoiceSerializer
	adjust_stock_sign = 1
	items_relation_name = 'p_invoice_items'


class DetailView(AbstractInvoiceDetailView):
	queryset = PurchaseInvoices.objects.select_related(
		'by', 
		'owner', 
	).prefetch_related(
		'p_invoice_items__item', 
		'p_invoice_items__repository'
	)
	serializer_class = InvoiceSerializer
	adjust_stock_sign = 1
	items_relation_name = 'p_invoice_items'

