from rest_framework import generics, mixins
from .models import Items
from .serializers import ItemsSerializer
# 
from operator import and_
from functools import reduce
# 
from django.db.models import Q
# 
from rest_framework.response import Response
# 
from rest_framework import status
# 
from django.db import IntegrityError
# 
from django.db.models.deletion import ProtectedError
from django.db import transaction
# 
from .models import Images, Barcode
# 
from rest_framework.decorators import api_view
# image reader dependencies
# from pyzbar import pyzbar
# from PIL import Image
# 
from django.db.models import Sum
# 
import os
from django.core.files import File
import tempfile
import shutil
from .delete_unsed_images import delete_unused_imagesss
from django.db.utils import IntegrityError



# def read_barcode111(image):
# 	barcodes = pyzbar.decode(Image.open(image))
	
# 	for barcode in barcodes:
# 		# Extract the barcode data
# 		barcode_data = barcode.data.decode('utf-8')
# 		barcode_type = barcode.type
# 		return barcode_data

# 		# print(f"111Found {barcode_type} barcode: {barcode_data}")
# 	return None



# @api_view(['POST'])
# def handle_barcode_image(request, *args, **kwargs):
# 	image = request.FILES.get('img')

# 	barcode = read_barcode111(image)

# 	if not barcode:
# 		return Response({'detail': "لم يتم التعرف على الباركود... 😢"}, status=status.HTTP_404_NOT_FOUND)

# 	try:
# 		item = Items.objects.get(barcodes__barcode=barcode)
# 		serializer = ItemsSerializer(item)

# 		return Response(serializer.data, status=status.HTTP_200_OK)
# 	except Items.DoesNotExist:
# 		return Response({'detail': f"لم يتم العثور على العنصر المطابق للباركود {barcode}... 😰"}, status=status.HTTP_404_NOT_FOUND)



class ItemsList(mixins.ListModelMixin, 
               mixins.CreateModelMixin,
               generics.GenericAPIView):
	queryset = Items.objects.all()
	serializer_class = ItemsSerializer

	def get_serializer(self, *args, **kwargs):
		kwargs['fieldss'] = self.request.query_params.get('fields', None)
		return super().get_serializer(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)

	def get_queryset(self):
		name_param = self.request.query_params.get('s')

		if name_param:
			q = Items.objects.filter(name__contains=name_param)
			if q:
				return q

			manipulated_params = name_param.split(' ')
			manipulated_params.pop() if manipulated_params[-1] == '' else None

			q_objects = [Q(name__contains=value) for value in manipulated_params]

			# Combine all Q objects using the logical AND operator '&'
			combined_q_object = reduce(and_, q_objects)

			return Items.objects.filter(combined_q_object)

		return super().get_queryset()

	def post(self, request, *args, **kwargs):
		try:
			return self.create(request, *args, **kwargs)
		except IntegrityError as e:
			return Response({'name': 'هذا الصنف موجود بالفعل...'}, status=status.HTTP_400_BAD_REQUEST)
	# def perform_create(self, serializer):
	# 	serializer.save(by=self.request.user)

class ItemDetail(mixins.RetrieveModelMixin, 
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 generics.GenericAPIView):
	queryset = Items.objects.all()
	serializer_class = ItemsSerializer

	def get_serializer(self, *args, **kwargs):
		kwargs['fieldss'] = self.request.query_params.get('fields', None)
		return super().get_serializer(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		return self.retrieve(request, *args, **kwargs)

	def put(self, request,*args, **kwargs):
		instance = self.get_object()
		with transaction.atomic():
			barcodes_data = request.data.get('barcodes', None)
			barcodes = instance.barcodes.all()
			if barcodes_data:
				for b in barcodes_data:
					if b.get('id', None):
						i = barcodes.get(pk=b['id'])
						i.barcode = b['barcode']
						i.save()
						barcodes = barcodes.exclude(id=b['id'])
					else:
						try:
							i = instance.barcodes.create(barcode=b['barcode'])
							barcodes = barcodes.exclude(id=i.id)
						except IntegrityError as e:
							return Response({'detail': f'باركود مكرر \"{b.get("barcode")}\"'}, status=status.HTTP_400_BAD_REQUEST)
				for barcode in barcodes:
					barcode.delete()
			request.data.pop('barcodes', None)
			return super().partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		instance = self.get_object()
		try:
			with transaction.atomic():
				super().destroy(request, *args, **kwargs)
				for img in Images.objects.filter(item__isnull=True):
					img.delete()
				instance.barcodes.all().delete()

		except ProtectedError as e:
			return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
		return Response(status=status.HTTP_204_NO_CONTENT)
  


# from invoices.models import Invoice, InvoiceItem
from transfer_items.models import Transfer
from repositories.models import Repositories
from .models import Stock
from datetime import datetime
import json

def validate_stock(items=Items.objects.all()):
	repositories = Repositories.objects.all()

	for item_data in items:
		for repo in repositories:
			purchase_invoices_item_qty = get_invoices_quantities(True, [item_data.id], repo.id)
			sales_invoices_item_qty = get_invoices_quantities(False, [item_data.id], repo.id)

			transfer_from = get_transfer_quantities(item_ids=[item_data.id], from_id=repo.id)
			transfer_to = get_transfer_quantities(item_ids=[item_data.id], to_id=repo.id)

			purchase_invoices_item_qty = purchase_invoices_item_qty[0] if purchase_invoices_item_qty else [0,0]
			sales_invoices_item_qty = sales_invoices_item_qty[0] if sales_invoices_item_qty else [0,0]
			transfer_from = transfer_from[0] if transfer_from else [0,0]
			transfer_to = transfer_to[0] if transfer_to else [0,0]

			diff = purchase_invoices_item_qty[1] - sales_invoices_item_qty[1] - transfer_from[1] + transfer_to[1]

			stock = Stock.objects.get(repository=repo, item=item_data)
	
			if stock.quantity != diff:
				directory = 'quantity-errors'
				os.makedirs(directory, exist_ok=True)

				filename = f"{item_data.name}_{repo.name}_{datetime.now()}.json"
				file_path = os.path.join(directory, filename)

				data = {
					'item_id': item_data.id,
					'item_name': item_data.name,
					'repo_id': repo.id,
					'repo_name': repo.name,
					'stock': stock.quantity,
					'accurate_stock': diff
				}

				with open(file_path, 'w', encoding='utf-8') as f:
					json.dump(data, f, indent=4)
					stock.quantity = diff
					stock.save()
					# stock
					



def get_invoices_quantities(is_purchase_invoice, item_ids, repository_id):
    return Invoice.objects.filter(
        is_purchase_invoice=is_purchase_invoice,
        items__item_id__in=item_ids,
		repository_id=repository_id
    ).values(
        'items__item_id'
    ).annotate(
        total_quantity=Sum('items__quantity')
    ).values_list('items__item_id', 'total_quantity')

def get_transfer_quantities(item_ids, from_id=False, to_id=False):
	q = Q(fromm_id=from_id) if from_id else Q(too_id=to_id)
	return Transfer.objects.filter(
		q,
		Q(items__item_id__in=item_ids)
	).values(
		'items__item_id'
	).annotate(
		total_quantity=Sum('items__quantity')
	).values_list('items__item_id', 'total_quantity')


from django.db.models import Count

def delete_orphan_items_from_invoice_items():
    # Find InvoiceItem objects with no associated Invoice
    orphan_items = InvoiceItem.objects.annotate(invoice_count=Count('invoices')).filter(invoice_count=0)

    # Delete these orphan items
    deleted_count = orphan_items.delete()[0]

    print(f"Deleted {deleted_count} orphan InvoiceItem objects.")