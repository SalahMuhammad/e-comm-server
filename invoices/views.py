from .models import Invoice
from items.models import Stock
from .serializers import InvoiceSerializer
from rest_framework import mixins, generics
from rest_framework.response import Response
from rest_framework import status
from django.db.utils import IntegrityError
from .utilities import update_items_prices
from django.db import transaction
from django.contrib.contenttypes.models import ContentType


class InvoicesListView(mixins.ListModelMixin, 
               		generics.GenericAPIView):
	serializer_class = InvoiceSerializer
	# types = [0, 1]


	def get_serializer(self, *args, **kwargs):
		kwargs['fieldss'] = self.request.query_params.get('fields', None)
		return super().get_serializer(*args, **kwargs)

	def get_queryset(self):
		# types = self.request.GET.get('type', '').split(',')

		# with open(path, 'rb') as img_file:
		# 	django_file = File(img_file)
		# 	for i in range(0, 1000000):
		# 		start = time.time()
		# 		a = []
		# 		for j in range(1, 4):
		# 			b = Images.objects.create(img=django_file)
		# 			a.append(b)
		# 		item = Items.objects.create(name=f'.b, {i}', price1=1, price2=124, price3=1221, price4=5112, by=User.objects.get(pk=1))
		# 		for img in a:
		# 			item.images.add(img)
		# 		print(i)
		# 		# if i % 5000 == 0:
		# 		# 	print(i)
		# 		inv = Invoice.objects.create(repository_id=1, content_type_id=12, paid=23143, by_id=1)
		# 		for i in range(1, 5):
		# 			inv.items.add(InvoiceItem.objects.create(item_id=item.id, quantity=3, unit_price=432))
		# 		end = time.time()
		# 		print(start-end)
		# consider prefitch_related('items').all()
		return Invoice.objects.all()#.prefetch_related('items').all()

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)


class ListCreateView(InvoicesListView,
				   mixins.CreateModelMixin):
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
	serializer_class = InvoiceSerializer


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
