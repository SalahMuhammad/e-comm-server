from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q

from common.encoder import MixedRadixEncoder
from .models import SalesInvoice, ReturnInvoice
from .serializers import InvoiceSerializer, ReturnInvoiceSerializer
from django_filters.rest_framework import DjangoFilterBackend
from .services.filters import SalesInvoiceFilter, ReturnInvoiceFilter
from common.views import AbstractInvoiceDetailView, AbstractInvoiceListCreateView
from common.utilities import adjust_stock
from rest_framework.decorators import api_view
from django.db import transaction

from .services.item_sales_and_refund_in_period import get_sold_and_items_totals_withen_period_as_http_response


from items.services.validate_items_stock import ValidateItemsStock
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

@api_view(['GET'])
def salesRefundTotals(request, *args, **kwargs):
    try:
        res = get_sold_and_items_totals_withen_period_as_http_response(
            request.GET.get('fromdate', ''), 
            request.GET.get('todate', '')
        )
        return res
    except Exception as e:
        raise Exception(f'salesRefundTotals() issue: {e}')

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
	# Adding filtering backends
	filter_backends = [DjangoFilterBackend]
	filterset_class = SalesInvoiceFilter


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
	# Adding filtering backends
	filter_backends = [DjangoFilterBackend]
	filterset_class = ReturnInvoiceFilter



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
	