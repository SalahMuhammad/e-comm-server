from rest_framework import mixins, status, generics
from rest_framework.response import Response
from .models import Transfer, TransferItem
from items.models import Stock
from .serializers import TransferSerializer, ItemTransferSerializer
from django.db import transaction


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
		instance 			= self.get_object()
		instance_from_repo	= instance.fromm.id
		instance_too_repo	= instance.too.id
		request_fromm_repo 	= request.data.get('fromm', instance_from_repo)
		request_too_repo 	= request.data.get('too', instance_too_repo)

		with transaction.atomic():
			res = super().partial_update(request, *args, **kwargs)

        	# Adjust stock for items in the old repository
			if instance_from_repo != request_fromm_repo:
				for item in instance.items.all():
					old_repository_fromm_stock = Stock.objects.get(
						repository_id=instance_from_repo, 
						item=item.item
					)
					old_repository_fromm_stock.adjust_stock(item.quantity)

			# Adjust stock for items in the new repository
			if instance_too_repo != request_too_repo:
				for item in instance.items.all():
					old_repository_too_stock = Stock.objects.get(
						repository_id=instance_too_repo, 
						item=item.item
					)
					old_repository_too_stock.adjust_stock(-item.quantity)
				
			# Handle items in the request
			for item_data in request.data['items']:
				serializer = ItemTransferSerializer(data=item_data)
				serializer.is_valid(raise_exception=True)

				try:
					item = instance.items.get(item=item_data['item'])
					quantity_diff = item_data.get('quantity', 1) - item.quantity
				except TransferItem.DoesNotExist:
					item = TransferItem(
						item_id=item_data['item'],
						transfer_id=instance.id,
						quantity=item_data.get('quantity', 1)
					)
					quantity_diff = item.quantity

				stock_from, created = Stock.objects.get_or_create(
					repository_id=request_fromm_repo,
					item_id=item_data['item']
				)
				stock_to, created = Stock.objects.get_or_create(
					repository_id=request_too_repo,
					item_id=item_data['item']
				)

				stock_from.adjust_stock(-quantity_diff)
				stock_to.adjust_stock(quantity_diff)
				
				item.quantity = item_data.get('quantity', 1)
				item.save()

			# Remove items that are no longer in the request
			request_item_ids = [item['item'] for item in request.data['items']]
			items_to_remove = instance.items.exclude(item_id__in=request_item_ids)

			for item in items_to_remove:
				stock_from = Stock.objects.get(repository=instance.fromm, item=item.item)
				stock_to = Stock.objects.get(repository=instance.too, item=item.item)
				stock_from.adjust_stock(item.quantity)
				stock_to.adjust_stock(-item.quantity)
				item.delete()



			# old_repository_too_stock = Stock.objects.get(
			# 	repository_id=instance_too_repo, 
			# 	item_id=item['item']
			# ) if instance_too_repo != request_too_repo else None
			
			# quantity = 0
			# if old_repository_fromm_stock or old_repository_too_stock:
			# 	instance_items = instance.items.filter(item_id=item['item'])
			# 	for item in instance_items:
			# 		quantity += item.quantity


			# for item in request.data['items']:
			# 	serializer = ItemTransferSerializer(data=item)
			# 	serializer.is_valid(raise_exception=True)
			# 	print(1111111111111)
			# 	print(request.data['fromm'])
			# 	print(instance.fromm.id)
			# 	print(res.data['fromm'])
			# 	print(22222222222222222)

			# 	# adjust stocks in repository if old and new repository are not identical
			# 	if old_repository_fromm_stock:
			# 		old_repository_fromm_stock.adjust_stock(quantity)
			# 		# from_plus = old_qty
				
			# 	if old_repository_too_stock:
			# 		old_repository_too_stock.adjust_stock(-quantity)
			# 		# to_plus = old_qty

			# [item for item in instance.items.all()]
			# items_to_remove = compare_items_2(instance.items.all(), items)


			# for item_id in items_to_remove:
			# 	stock_from = Stock.objects.get(repository=instance.fromm, item=item_id)
			# 	stock_to, created = Stock.objects.get_or_create(repository=instance.too, item=item_id)
			# 	item = instance.items.get(item=item_id)
			# 	stock_from.adjust_stock(item.quantity)
			# 	stock_to.adjust_stock(-item.quantity)
			# 	item.delete()
			
			# for item_data in items:
			# 	serializer = ItemTransferSerializer(data=item_data)
			# 	serializer.is_valid(raise_exception=True)
			# 	try:
			# 		item = instance.items.get(item=item_data['item'])
			# 	except Exception as e:
			# 		item = instance.items.create(item_id=item_data['item'])
			# 	fromm = request.data['fromm']
			# 	too = request.data['too']
			# 	quantity_diff = (item.quantity - item_data.get('quantity', 1)) * -1
			# 	from_plus = 0
			# 	to_plus = 0
			# 	old_qty = item.quantity

				
				
			# 	stock_from = Stock.objects.get(repository=fromm, item=item_data['item'])
			# 	stock_to, created = Stock.objects.get_or_create(repository=too, item=item_data['item'])
			# 	stock_from.adjust_stock(-(quantity_diff + from_plus))
			# 	stock_to.adjust_stock(quantity_diff + to_plus)

			# 	item.quantity = item_data.get('quantity', 1)
			# 	item.save()
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

