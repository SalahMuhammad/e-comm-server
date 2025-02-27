from .models import PurchaseInvoices as Invoice
from items.models import Stock
from .serializers import InvoicesSerializer, InvoiceItemsSerializer
from rest_framework import mixins, generics
from rest_framework.response import Response
from rest_framework import status
from django.db.utils import IntegrityError
from .utilities import update_items_prices
from django.db import transaction


class ListCreateView(
	mixins.ListModelMixin, 
	mixins.CreateModelMixin,
	generics.GenericAPIView
):
	serializer_class = InvoicesSerializer


	# def get_serializer(self, *args, **kwargs):
	# 	kwargs['fieldss'] = self.request.query_params.get('fields', None)
	# 	return super().get_serializer(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		try:
			res =  self.create(request, *args, **kwargs)
			update_items_prices(request, res.status_code)
			return res
		except IntegrityError as e:
			return Response({'detail': str(e)+'fffffffffffff'}, status=status.HTTP_400_BAD_REQUEST)


class DetailView(mixins.RetrieveModelMixin,
						 mixins.UpdateModelMixin,
						 mixins.DestroyModelMixin,
						 generics.GenericAPIView):
	queryset = Invoice.objects.all()
	serializer_class = InvoicesSerializer


	def get_serializer(self, *args, **kwargs):
		kwargs['fieldss'] = self.request.query_params.get('fields', None)
		return super().get_serializer(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		return self.retrieve(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		res = super().partial_update(request, *args, **kwargs)
		update_items_prices(request, res.status_code)
		return res
  
	def delete(self, request, *args, **kwargs):
		invoice_instance = self.get_object()
		sign = -1 if invoice_instance.is_purchase_invoice else 1

		with transaction.atomic():
			for item in invoice_instance.items.all():
				stock = Stock.objects.get(repository=invoice_instance.repository, item=item.item)
				stock.adjust_stock(item.quantity * sign)
				item.delete()

			invoice_instance.delete()
			
		return Response(status=status.HTTP_204_NO_CONTENT)
