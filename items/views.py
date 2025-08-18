from rest_framework import generics, mixins
from .models import Items, Images, ItemPriceLog, Types
from .serializers import ItemsSerializer, TypesSerializer
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
import os
from django.db.utils import IntegrityError
from decimal import Decimal, ROUND_HALF_UP



from rest_framework import serializers
from .models import InitialStock
class InitialStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = InitialStock
        fields = ['item', 'quantity', "repository", "by"]  # Only allow updating the quantity field

from rest_framework.generics import UpdateAPIView
from common.utilities import ValidateItemsStock
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import authentication_classes, permission_classes

from rest_framework.permissions import AllowAny
@api_view(['POST'])

@authentication_classes([])  # Disable authentication (CSRF check is tied to authentication)
@permission_classes([AllowAny])  # Allow any user
def aaaa(request, *args, **kwargs):
	# request.POST._mutable = True
	item_id = kwargs['pk']
	request.data['item'] = item_id
	request.data['repository'] = 10000
	request.data['by'] = 10000
	a = Items.objects.get(pk=item_id).initial_stock.all()
	if a.exists():
		b = a[0]
		b.quantity = request.data['quantity']
		b.save()
		ValidateItemsStock().validate_stock(Items.objects.filter(pk=item_id))
		return Response(status=status.HTTP_202_ACCEPTED)
	serializer = InitialStockSerializer(data=request.data)
	if serializer.is_valid():
		serializer.save()
		ValidateItemsStock().validate_stock(Items.objects.filter(pk=item_id))
		return Response(serializer.data, status=status.HTTP_200_OK)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

from common.utilities import ValidateItemsStock
@api_view(['get'])
def quantity_errors_corrector_view(request, *args, **kwargs):
	a = ValidateItemsStock()
	a.validate_stock(items=Items.objects.all())
	return Response(status=status.HTTP_200_OK)

@api_view(['get'])
def quantity_errors_list_view(request, *args, **kwargs):
	# Get the list of files in the directory
	directory = 'quantity-errors'
	files = os.listdir(directory)

	# Create a list to store the file paths
	errors_list = []
	# Iterate through the files and create their full paths
	for file in files:
		file_path = os.path.join(directory, file)

		if file.__contains__('json'):
			with open(file_path, 'r') as file:
				errors_list.append({file.name: json.load(file)})
	
	errors_list.sort(key=lambda d: datetime.strptime(list(d.values())[0]['date'], "%Y-%m-%d %H:%M:%S"), reverse=True)

	return Response(errors_list, status=status.HTTP_200_OK)

# from rest_framework.parsers import MultiPartParser, FormParser
class ItemsList(mixins.ListModelMixin, 
	mixins.CreateModelMixin,
	generics.GenericAPIView,
):
	queryset = Items.objects.all()
	serializer_class = ItemsSerializer
	# parser_classes = (MultiPartParser, FormParser)
	

	def get_serializer(self, *args, **kwargs):
		kwargs['fieldss'] = self.request.query_params.get('fields', None)
		return super().get_serializer(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)

	def get_queryset(self):
		queryset = self.queryset
		
		type_param = Q()
		if not self.request.user.is_superuser:
			permissions = self.request.user.groups.values_list('permissions__codename', flat=True)
			type_param = Q(type__name__in=permissions)

			queryset = queryset.filter(type_param)

		name_param = self.request.query_params.get('s')
		aa = Q(name__icontains=name_param) | Q(barcodes__barcode__icontains=name_param) | Q(id__icontains=name_param) | Q(origin__icontains=name_param) | Q(place__icontains=name_param) if name_param else Q()
		if name_param:
			q = queryset.filter(aa)
			if q:
				return q

			manipulated_params = name_param.split(' ')
			manipulated_params.pop() if manipulated_params[-1] == '' else None

			q_objects = [Q(name__icontains=value) for value in manipulated_params]

			# Combine all Q objects using the logical AND operator '&'
			combined_q_object = reduce(and_, q_objects)

			return queryset.filter(combined_q_object)
		
		return queryset

	def post(self, request, *args, **kwargs):
		with transaction.atomic():
			try:
				res = self.create(request, *args, **kwargs)

				if not float(res.data['price1']) <= 0:
					ItemPriceLog.objects.create(
						item_id=res.data['id'], 
						price=res.data['price1'], 
						by_id=request.data['by']
					)

				return res
			except IntegrityError as e:
				return Response({'name': 'هذا الصنف موجود بالفعل...'}, status=status.HTTP_400_BAD_REQUEST)
	# def perform_create(self, serializer):
	# 	serializer.save(by=self.request.user)

class ItemDetail(
	mixins.RetrieveModelMixin, 
	mixins.UpdateModelMixin,
	mixins.DestroyModelMixin,
	generics.GenericAPIView
):
	queryset = Items.objects.all()
	serializer_class = ItemsSerializer

	def get_serializer(self, *args, **kwargs):
		kwargs['fieldss'] = self.request.query_params.get('fields', None)
		return super().get_serializer(*args, **kwargs)

	def get_queryset(self):
		queryset = self.queryset

		if not self.request.user.is_superuser:
			a = self.request.user.groups.values_list('permissions__codename', flat=True)
			return queryset.filter(type__name__in=a)
		
		return queryset

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

			if instance.price1 != Decimal(str(request.data.get('price1', instance.price1))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):
				ItemPriceLog.objects.create(
					item_id=instance.id, 
					price=request.data.get('price1', instance.price1), 
					by_id=request.data['by']
				)

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


class TypesList(mixins.ListModelMixin,
	mixins.CreateModelMixin,
	generics.GenericAPIView
):
	queryset = Types.objects.all()
	serializer_class = TypesSerializer

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)


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
					





from django.db.models import Count

def delete_orphan_items_from_invoice_items():
    # Find InvoiceItem objects with no associated Invoice
    orphan_items = InvoiceItem.objects.annotate(invoice_count=Count('invoices')).filter(invoice_count=0)

    # Delete these orphan items
    deleted_count = orphan_items.delete()[0]

    print(f"Deleted {deleted_count} orphan InvoiceItem objects.")