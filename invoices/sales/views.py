from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import SalesInvoice, ReturnInvoice
from .serializers import InvoiceSerializer, ReturnInvoiceSerializer
from common.views import AbstractInvoiceDetailView, AbstractInvoiceListCreateView
from common.utilities import adjust_stock
from rest_framework.decorators import api_view
from django.db import transaction


from common.utilities import ValidateItemsStock
from items.models import Items

from rest_framework import mixins, generics


@api_view(['POST'])
def toggle_repository_permit(request, *args, **kwargs):
	"""
		View to toggle the repository_permit field of an invoice.
	"""
	invoice = get_object_or_404(SalesInvoice, id=kwargs['pk'])

	with transaction.atomic():
		adjust_stock(invoice.s_invoice_items.all(), 1 if invoice.repository_permit else -1)
		invoice.repository_permit = not invoice.repository_permit
		invoice.save()

	a = ValidateItemsStock()
	items_ids = [item.item.id for item in invoice.s_invoice_items.all()]
	a.validate_stock(items=Items.objects.filter(id__in=items_ids))

	return JsonResponse({
		"success": True,
		"repository_permit": invoice.repository_permit
	})

class ListCreateView(AbstractInvoiceListCreateView):
	queryset = SalesInvoice.objects.all()
	serializer_class = InvoiceSerializer
	adjust_stock_sign = -1
	items_relation_name = 's_invoice_items'


class DetailView(AbstractInvoiceDetailView):
	queryset = SalesInvoice.objects.all()
	serializer_class = InvoiceSerializer
	adjust_stock_sign = -1
	items_relation_name = 's_invoice_items'


class ReturnListCreateView(AbstractInvoiceListCreateView):
	queryset = ReturnInvoice.objects.all()
	serializer_class = ReturnInvoiceSerializer
	adjust_stock_sign = 1
	items_relation_name = 's_invoice_items'


class RefundDetailView(
	mixins.RetrieveModelMixin,
	generics.GenericAPIView
):
    queryset = ReturnInvoice.objects.all()
    serializer_class = ReturnInvoiceSerializer
    

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
	