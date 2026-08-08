from rest_framework import generics, mixins, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from common.services.customeConfigurationHandler import customeFilters
# 
from .models import Items, Images, Types
from .serializers import ItemsSerializer, TypesSerializer, DamagedItemsSerializer
# 
from .services.item_fluctuation import get_item_fluctuation
from .services.validate_items_stock import ValidateItemsStock
# 
from auth._permissions.CustomeViewsPermission import ConfigurationBasedCustomeViewsPermission
# 
from operator import and_
from functools import reduce
# 
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.db import transaction
# django filters
from django_filters.rest_framework import DjangoFilterBackend
# 
from datetime import datetime
import os, json
from metadata.base import CompositeMetadata



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
	result = a.stock_validation()

	return Response(result, status=status.HTTP_200_OK)

@api_view(['get'])
def quantity_errors_list_view(request, *args, **kwargs):
	# Get the list of files in the directory
	directory = 'media/quantity-errors'
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
	metadata_class = CompositeMetadata
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
		
		queryset = customeFilters(self, queryset, 'items')
		
		type = self.request.query_params.get('type')
		if type:
			queryset = queryset.filter(type__name__icontains=type)

		id = self.request.query_params.get('id')
		if id:
			queryset = queryset.filter(id__icontains=id)

		name = self.request.query_params.get('name')
		manipulated_params = [p for p in (name.split(' ') if name else []) if p]
		if manipulated_params:
			q_objects = [Q(name__icontains=value) for value in manipulated_params]
			combined_q_object = reduce(and_, q_objects)
			queryset =  queryset.filter(combined_q_object)

		barcode = self.request.query_params.get('barcode')
		if barcode:
			queryset = queryset.filter(barcodes__barcode__icontains=barcode)
			
		place = self.request.query_params.get('place')
		if place:
			queryset = queryset.filter(place__icontains=place)
			
		origin = self.request.query_params.get('origin')
		if origin:
			queryset = queryset.filter(origin__icontains=origin)

		return queryset

	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)

	def perform_create(self, serializer):
		serializer.save(by=self.request.user)



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
		queryset = customeFilters(self, queryset, 'items')
		# Return all items for any authenticated user.
		# List view (ItemsList) handles type-based filtering for the listing.
		# Detail view should be accessible to anyone with view_items permission.
		return queryset

	def get(self, request, *args, **kwargs):
		return self.retrieve(request, *args, **kwargs)

	def patch(self, request,*args, **kwargs):
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
	permission_classes = (ConfigurationBasedCustomeViewsPermission, )
	def get(self, request, pk, **kwargs):
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
