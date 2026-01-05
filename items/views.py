from rest_framework import generics, mixins, serializers, status, viewsets
# from rest_framework.generics import UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
# 
from .models import Items, Images, ItemPriceLog, Types, Barcode
from .serializers import ItemsSerializer, TypesSerializer, InitialStockSerializer, DamagedItemsSerializer
# 
from .services.item_fluctuation import get_item_fluctuation
from .services.handle_images_insertion import http_request_images_handler
from .services.handle_barcodes import http_request_barcodes_handler
# 
from .services.validate_items_stock import ValidateItemsStock
# 
from operator import and_
from functools import reduce
# 
from django.db.models.deletion import ProtectedError
from django.db.models import Q, Exists, OuterRef
from django.db.utils import IntegrityError
from django.db import IntegrityError, transaction
# 
from decimal import Decimal, ROUND_HALF_UP
# django filters
from django_filters.rest_framework import DjangoFilterBackend
# 
import os



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




# __________________________________ Items ___________________________________________________#




# from rest_framework.parsers import MultiPartParser, FormParser
class ItemsList(mixins.ListModelMixin, 
	mixins.CreateModelMixin,
	generics.GenericAPIView,
):
	queryset = Items.objects.select_related(
		'by', 
		'type'
	).prefetch_related(
		'images', 
		'barcodes', 
		'stock__repository'
	)
	# .only(
	# 	# 'by',
	# 	'by__username',
	# 	# 'type',
	# 	'type__name',
	# 	# 'images__img',
	# 	# 'barcodes', 
	# 	# 'barcodes__barcode', 
	# 	# 'stock__repository__name',
	#         "created_at",
	#         "updated_at",
	#         "name",
	#         "price1",
	#         "price2",
	#         "price3",
	#         "price4",
	#         "is_refillable",
	#         "origin",
	#         "place",
	#         "by",
	#         "type",
	# )
	serializer_class = ItemsSerializer
	# parser_classes = (MultiPartParser, FormParser)
	

	# def get_serializer(self, *args, **kwargs):
	# 	kwargs['fieldss'] = self.request.query_params.get('fields', None)
	# 	return super().get_serializer(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)

	def get_queryset(self):
		queryset = self.queryset
		
		
		type = self.request.query_params.get('type')
		if type:
			queryset = queryset.filter(type__name__icontains=type)

		id = self.request.query_params.get('id')
		if id:
			queryset = queryset.filter(id__icontains=id)

		name = self.request.query_params.get('name')
		if name:
			queryset = queryset.filter(name__icontains=name)		

		barcode = self.request.query_params.get('barcode')
		if barcode:
			queryset = queryset.filter(barcodes__barcode__icontains=barcode)
			
		place = self.request.query_params.get('place')
		if place:
			queryset = queryset.filter(place__icontains=place)
			
		origin = self.request.query_params.get('origin')
		if origin:
			queryset = queryset.filter(origin__icontains=origin)

		# Permission filtering
		if not self.request.user.is_superuser:
			permissions = self.request.user.groups.values_list('permissions__codename', flat=True)
			queryset = queryset.filter(type__name__in=permissions)

		return queryset

	# def post(self, request, *args, **kwargs):
	# 	with transaction.atomic():
	# 		try:
	# 			images = request.FILES.getlist('images')
	# 			barcodes_data = request.POST.get('barcodes', None)
	# 			request.data.pop('barcodes')

	# 			res = self.create(request, *args, **kwargs)

	# 			http_request_barcodes_handler(res.data['id'], barcodes_data)
	# 			http_request_images_handler(res.data['id'], images)

	# 			if not float(res.data['price1']) <= 0:
	# 				ItemPriceLog.objects.create(
	# 					item_id=res.data['id'], 
	# 					price=res.data['price1'], 
	# 					by_id=request.data['by']
	# 				)

	# 			return res
	# 		except IntegrityError as e:
	# 			return Response({'name': 'هذا الصنف موجود بالفعل...'}, status=status.HTTP_400_BAD_REQUEST)
	# def perform_create(self, serializer):
	# 	serializer.save(by=self.request.user)



class ItemDetail(
	mixins.RetrieveModelMixin, 
	mixins.UpdateModelMixin,
	mixins.DestroyModelMixin,
	generics.GenericAPIView
):
	queryset = Items.objects.select_related('by', 'type').prefetch_related('images', 'barcodes', 'stock__repository')
	serializer_class = ItemsSerializer

	# def get_serializer(self, *args, **kwargs):
	# 	kwargs['fieldss'] = self.request.query_params.get('fields', None)
	# 	return super().get_serializer(*args, **kwargs)

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
			barcodes_data = request.POST.get('barcodes', None)
			request.data.pop('barcodes', None)
			images = request.FILES.getlist('images')
			price1 = request.data.get('price1', instance.price1)
			# print(request.data)
			res = super().partial_update(request, *args, **kwargs)

			http_request_barcodes_handler(instance.id, barcodes_data)
			for img in instance.images.all():
					img.img.delete()
					img.delete()
			http_request_images_handler(instance.id, images)

# # Prepare images data for serializer
#     images_data = []
#     for img in images:
#         images_data.append({'img': img})
	
#     request.data['images'] = images_data
	
#     serializer = self.get_serializer(instance, data=request.data, partial=True)
#     serializer.is_valid(raise_exception=True)
#     self.perform_update(serializer)


			if instance.price1 != Decimal(str(price1)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):
				ItemPriceLog.objects.create(
					item_id=instance.id, 
					price=res.data['price1'], 
					by_id=res.data['by']
				)

			return res

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




# ______________________________________ Types _______________________________________________#




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




# ______________________________ Item Fluctuation _______________________________________________________#




class ItemFluctuation(APIView):
	def get(self, request, pk):
		data = get_item_fluctuation(pk)
		return Response(data, status=status.HTTP_200_OK)




# __________________________________ Damaged Items ___________________________________________________#




from django_filters import rest_framework as filters
from .models import DamagedItems

class DamagedItemsFilter(filters.FilterSet):
	# 'icontains' allows searching for a snippet of text in notes
	notes = filters.CharFilter(lookup_expr='icontains')
	item__name = filters.CharFilter(lookup_expr='icontains')
	owner__name = filters.CharFilter(lookup_expr='icontains')
	repository__name = filters.CharFilter(lookup_expr='icontains')


	class Meta:
		model = DamagedItems
		fields = ['item__name', 'owner__name', 'repository__name', 'notes']

class DamagedItemsViewSet(viewsets.ModelViewSet):
	queryset = DamagedItems.objects.select_related(
		'repository',
		'by',
		'owner',
		'item'
	).all()
	serializer_class = DamagedItemsSerializer
	
	# Adding filtering backends
	filter_backends = [DjangoFilterBackend]
	filterset_class = DamagedItemsFilter

	def perform_create(self, serializer):
		serializer.save(by=self.request.user)




# _____________________________________________________________________________________#




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

