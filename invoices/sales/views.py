from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404

from common.encoder import MixedRadixEncoder
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
	queryset = SalesInvoice.objects.select_related(
		'by', 
		'owner'
	).prefetch_related(
		's_invoice_items__item', 
		's_invoice_items__repository'
	)
	serializer_class = InvoiceSerializer
	adjust_stock_sign = -1
	items_relation_name = 's_invoice_items'


class DetailView(AbstractInvoiceDetailView):
	queryset = SalesInvoice.objects.select_related(
		'by', 
		'owner'
	).prefetch_related(
		's_invoice_items__item', 
		's_invoice_items__repository'
	)
	serializer_class = InvoiceSerializer
	adjust_stock_sign = -1
	items_relation_name = 's_invoice_items'


class ReturnListCreateView(AbstractInvoiceListCreateView):
	queryset = ReturnInvoice.objects.select_related(
		'by', 
		'owner', 
		'original_invoice'
	).prefetch_related(
		's_invoice_items__item', 
		's_invoice_items__repository'
	)
	serializer_class = ReturnInvoiceSerializer
	adjust_stock_sign = 1
	items_relation_name = 's_invoice_items'


class RefundDetailView(
	mixins.RetrieveModelMixin,
	generics.GenericAPIView
):
    queryset = ReturnInvoice.objects.select_related(
		'by', 
		'owner', 
		'original_invoice'
	).all()
    serializer_class = ReturnInvoiceSerializer

    def get_object(self):
        encoded_pk = self.kwargs.get('pk')
        try:
            # Decode the encoded ID from URL parameter
            decoded_id = MixedRadixEncoder().decode(str(encoded_pk))
            # Use the decoded ID to get the object
            return self.get_queryset().get(id=decoded_id)
        except Exception as e:
            print(f"Invalid encoded ID: {self.kwargs['pk']}")
            raise Http404("Object not found")    

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
	