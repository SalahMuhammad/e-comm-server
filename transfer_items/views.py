from django.shortcuts import render
from rest_framework import mixins, status, generics, serializers
from rest_framework.response import Response
from .models import Transfer, TransferItem
from items.models import Stock, Items
from repositories.models import Repositories
from .serializers import TransferSerializer, ItemTransferSerializer
from django.db import transaction
from invoices.utilities import compare_items_2
# Create your views here.


class ListCreateView(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     generics.GenericAPIView):
	queryset = Transfer.objects.all()
	serializer_class = TransferSerializer


	def get_serializer(self, *args, **kwargs):
		# kwargs['fieldss'] = self.request.query_params.get('fields', None)
		return super().get_serializer(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)
    
	def post(self, request, *args, **kwargs):
		with transaction.atomic():
			# items_ids = [item['item'] for item in request.data['items']]
			# if len(items_ids) != len(set(items_ids)):
			# 	raise serializers.ValidationError({'detail': "Duplicate items are not allowed...😵"})

			res = self.create(request, *args, **kwargs)
			
			for item in request.data['items']:
				serializer = ItemTransferSerializer(data=item)
				serializer.is_valid(raise_exception=True)

				TransferItem.objects.create(
					item_id=item['item'], 
					transfer_id=res.data['id'], 
					quantity=item.get('quantity', 1)
				)

				stock_from, created = Stock.objects.get_or_create(
					repository_id=res.data['fromm'], 
					item_id=item['item']
				)
				
				stock_to, created = Stock.objects.get_or_create(
					repository_id=res.data['too'], 
					item_id=item['item']
				)

				stock_from.adjust_stock(-item.get('quantity', 1))
				stock_to.adjust_stock(item.get('quantity', 1))
		
			return res
        
    

class DetailView(mixins.RetrieveModelMixin,
				 mixins.UpdateModelMixin,
				 mixins.DestroyModelMixin,
				 generics.GenericAPIView):
	queryset = Transfer.objects.all()
	serializer_class = TransferSerializer


	def get_serializer(self, *args, **kwargs):
		# kwargs['fieldss'] = self.request.query_params.get('fields', None)
		return super().get_serializer(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		return self.retrieve(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		items = request.data.get('items', [])
		instance = self.get_object()

		with transaction.atomic():
			res = super().partial_update(request, *args, **kwargs)

			# items_ids = [item['item'] for item in request.data.get('items', [])]	
			# if len(items_ids) != len(set(items_ids)):
			# 	raise serializers.ValidationError({'detail': "Duplicate items are not allowed...😵"})

			for item in request.data['items']:
				serializer = ItemTransferSerializer(data=item)
				serializer.is_valid(raise_exception=True)
				print(1111111111111)
				print(request.data['fromm'])
				print(instance.fromm.id)
				print(res.data['fromm'])
				print(22222222222222222)

				instance_items = instance.items.filter(item=item_data['item'])

				# adjust stocks in repository if old and new repository are not identical
				if instance.fromm != request.data.get('fromm', instance.fromm):
					old_stock_from = Stock.objects.get(repository=instance.fromm, item=item['item'])
					quantity = 0
					for item in instance_items:
						quantity += item.quantity
					old_stock_from.adjust_stock(quantity)
					from_plus = old_qty

				if instance.too != request.data.get('too', instance.too):
					old_stock_to = Stock.objects.get(repository=instance.too, item=item['item'])
					quantity = 0
					for item in instance_items:
						quantity += item.quantity
					old_stock_to.adjust_stock(-old_qty)
					to_plus = old_qty


				match item.status:
					case "new":
						TransferItem.objects.create(
							item_id=item['item'], 
							transfer_id=res.data['id'], 
							quantity=item.get('quantity', 1)
						)

						stock_from, created = Stock.objects.get_or_create(
							repository_id=res.data['fromm'], 
							item_id=item['item']
						)

						stock_to, created = Stock.objects.get_or_create(
							repository_id=res.data['too'], 
							item_id=item['item']
						)

						stock_from.adjust_stock(-item.get('quantity', 1))
						stock_to.adjust_stock(item.get('quantity', 1))
				

			items_to_remove = compare_items_2(instance.items.all(), items)

			for item_id in items_to_remove:
				stock_from = Stock.objects.get(repository=instance.fromm, item=item_id)
				stock_to, created = Stock.objects.get_or_create(repository=instance.too, item=item_id)
				item = instance.items.get(item=item_id)
				stock_from.adjust_stock(item.quantity)
				stock_to.adjust_stock(-item.quantity)
				item.delete()
			
			for item_data in items:
				serializer = ItemTransferSerializer(data=item_data)
				serializer.is_valid(raise_exception=True)
				try:
					item = instance.items.get(item=item_data['item'])
				except Exception as e:
					item = instance.items.create(item_id=item_data['item'])
				fromm = request.data['fromm']
				too = request.data['too']
				quantity_diff = (item.quantity - item_data.get('quantity', 1)) * -1
				from_plus = 0
				to_plus = 0
				old_qty = item.quantity

				
				
				stock_from = Stock.objects.get(repository=fromm, item=item_data['item'])
				stock_to, created = Stock.objects.get_or_create(repository=too, item=item_data['item'])
				stock_from.adjust_stock(-(quantity_diff + from_plus))
				stock_to.adjust_stock(quantity_diff + to_plus)

				item.quantity = item_data.get('quantity', 1)
				item.save()
			return res
  
	def delete(self, request, *args, **kwargs):
		instance = self.get_object()

		with transaction.atomic():
			for item in instance.items.all():
				stock_from = Stock.objects.get(repository=instance.fromm, item=item.item)
				stock_to = Stock.objects.get(repository=instance.too, item=item.item)
				stock_from.adjust_stock(item.quantity)
				stock_to.adjust_stock(-item.quantity)

			instance.delete()
			
		return Response(status=status.HTTP_204_NO_CONTENT)

