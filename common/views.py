# from rest_framework import status, mixins, generics
# from rest_framework.response import Response


# class AbstractInvoicesOwnersListCreateView(
#     mixins.ListModelMixin,
#     mixins.CreateModelMixin,
#     generics.GenericAPIView
# ):
#     def get_queryset(self):
#         name_param = self.request.query_params.get('s')

#         if name_param:
#             q = self.queryset.filter(name__contains=name_param)
#             return q

#         return self.queryset

#     def get(self, request, *args, **kwargs):
#         return self.list(request, *args, **kwargs)

#     def post(self, request, *args, **kwargs):
#         return self.create(request, *args, **kwargs)


# class AbstractInvoicesOwnersDetailView(
#     mixins.RetrieveModelMixin, 
#     mixins.UpdateModelMixin,
#     mixins.DestroyModelMixin,
#     generics.GenericAPIView
# ):
#     def get(self, request, *args, **kwargs):
#         return self.retrieve(request, *args, **kwargs)

#     def put(self, request,*args, **kwargs):
#         return super().partial_update(request, *args, **kwargs)

#     def delete(self, request, *args, **kwargs):
#         # try:
#         return super().destroy(request, *args, **kwargs)
#         # except ProtectedError as e:
#         #     return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
  

from items.models import Stock
from rest_framework import mixins, generics
from rest_framework.response import Response
from rest_framework import status
from invoices.purchase.utilities import update_items_prices
from common.utilities import set_request_items_totals, insert_invoice_items, adjust_stock
from django.db import transaction
from common.encoder import MixedRadixEncoder


class AbstractInvoiceListCreateView(
	mixins.ListModelMixin, 
	mixins.CreateModelMixin,
	generics.GenericAPIView
):
	# def get_serializer(self, *args, **kwargs):
	# 	kwargs['fieldss'] = self.request.query_params.get('fields', None)
	# 	return super().get_serializer(*args, **kwargs)

	def perform_create(self, serializer):
		""" Override this to get the created instance """
		instance = serializer.save()  # This is the actual instance
		return instance  # Returning the created object
	
	def get_queryset(self):
		queryset = self.queryset

		name_param = self.request.query_params.get('ownerid')
		if name_param:
			return queryset.filter(owner_id=name_param)
		
		name_param = self.request.query_params.get('no')
		id = -1
		if name_param:
			try:
				id = MixedRadixEncoder().decode(name_param)  # Validate the encoded ID
			except:
				print(f"Invalid encoded ID: {name_param}")
				
			return queryset.filter(pk=id)
		
		return queryset

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		with transaction.atomic():
			serializer = self.get_serializer(data=request.data)
			serializer.is_valid(raise_exception=True)
			invoice_instance = self.perform_create(serializer)

			if invoice_instance.repository_permit:
				adjust_stock(
					getattr(invoice_instance, self.items_relation_name).all(), 
					self.adjust_stock_sign
				)

			if self.items_relation_name == 'p_invoice_items':
				update_items_prices(request.data[self.items_relation_name], request.data['by'])

			return Response(serializer.data, status=status.HTTP_201_CREATED)

class AbstractInvoiceDetailView(
	mixins.RetrieveModelMixin,
	mixins.UpdateModelMixin,
	mixins.DestroyModelMixin,
	generics.GenericAPIView
):
	def get(self, request, *args, **kwargs):
		return self.retrieve(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		invoice_instance = self.get_object()

		if invoice_instance.repository_permit:
			return Response(
				{'detail': ['لا يمكن تعديل هذه الفاتورة بعد تصديرها (يجب ازاله الاذن المخزني اولا)...']}, 
				status=status.HTTP_400_BAD_REQUEST
			)

		with transaction.atomic():
			serializer = self.get_serializer(invoice_instance, data=request.data, partial=True)
			serializer.is_valid(raise_exception=True)
			self.perform_update(serializer)

			edited_items, sum_items_total = set_request_items_totals(request.data[self.items_relation_name])
			request.data[self.items_relation_name] = edited_items

			invoice_instance.total_amount = sum_items_total
			invoice_instance.save()

			# Get all existing items and their IDs
			existing_items = getattr(invoice_instance, self.items_relation_name).all()
			existing_item_ids = [item.id for item in existing_items]

			# Track which existing items have been updated
			updated_item_ids = set()

			# Handle items in the request
			for item_data in request.data[self.items_relation_name]:
				item_id = item_data['item']
				quantity = item_data.get('quantity', 1)

				# Try to find an existing item that hasn't been updated yet
				existing_item = None
				for item in existing_items:
					if item.item_id == item_id and item.id not in updated_item_ids:
						existing_item = item
						updated_item_ids.add(item.id)
						break

				if existing_item:
					existing_item.repository_id = item_data['repository']
					existing_item.quantity = quantity
					existing_item.description = item_data.get('description', '')
					existing_item.unit_price = item_data.get('unit_price', 0)
					existing_item.tax_rate = item_data.get('tax_rate', 0)
					existing_item.discount = item_data.get('discount', 0)
					existing_item.total = item_data.get('total', 0)
					existing_item.save()
				else:
					# Create new item
					insert_invoice_items(
						invoice_instance,
						self.items_relation_name,
						[item_data],
					)

			# Remove items that were not updated or added
			items_to_remove = getattr(invoice_instance, self.items_relation_name).filter(
				id__in=set(existing_item_ids) - updated_item_ids
			)
			
			for item in items_to_remove:
				item.delete()

			if self.items_relation_name == 'p_invoice_items':
				update_items_prices(request.data[self.items_relation_name], request.data['by'])

			return Response(serializer.data, status=status.HTTP_200_OK)
  
	def delete(self, request, *args, **kwargs):
		invoice_instance = self.get_object()

		if invoice_instance.repository_permit:
			return Response(
				{'detail': ['لا يمكن تعديل هذه الفاتورة بعد تصديرها (يجب ازاله الاذن المخزني اولا)...']}, 
				status=status.HTTP_400_BAD_REQUEST
			)
		try:
			res = super().destroy(request, *args, **kwargs)
		except Exception as e:
			return Response(
				{'detail': str(e)}, 
				status=status.HTTP_400_BAD_REQUEST
			)
		
		return res
