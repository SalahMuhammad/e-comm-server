from rest_framework import generics, mixins, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from common.services.customeConfigurationHandler import customeFilters
from items.services.validate_items_stock import ValidateItemsStock
from metadata.base import CompositeMetadata

from .models import Maintenance
from .serializers import MaintenanceSerializer
from .services.filters import MaintenanceFilter
from common.encoder import MixedRadixEncoder
from django.http import Http404

from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction



class MaintenanceView(mixins.CreateModelMixin, mixins.ListModelMixin, generics.GenericAPIView):
	queryset = Maintenance.objects.select_related(
		'client', 'item', 'maintained_by', 'created_by', 'last_updated_by'
	).prefetch_related('parts')
	metadata_class = CompositeMetadata
	serializer_class = MaintenanceSerializer
	# filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	# filterset_fields = ['status', 'client', 'item', 'date_in']
	# search_fields = ['serial_number', 'client__name', 'item__name']
	# ordering_fields = ['date_in', 'created_at']
	# ordering = ['-date_in']
	filter_backends = [DjangoFilterBackend]
	filterset_class = MaintenanceFilter
	
	def get_queryset(self):
		return customeFilters(self, self.queryset, 'maintenance')

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user, last_updated_by=self.request.user)

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)

	@transaction.atomic
	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		
		# serializer.instance is your actual Django model object
		instance = serializer.instance 

		a = ValidateItemsStock()
		items_ids = [item.spare_part.id for item in instance.parts.all()]
		a.stock_validation(
			item_ids=items_ids, 
			log_mismatches=False, 
			raise_on_negative=True if instance.maintenance_date else False
		)

		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MaintenanceDetailView(
	mixins.RetrieveModelMixin,
	mixins.UpdateModelMixin,
	mixins.DestroyModelMixin,
	generics.GenericAPIView
):
	queryset = Maintenance.objects.select_related(
		'client', 'item', 'maintained_by', 'created_by', 'last_updated_by'
	).prefetch_related('parts')
	serializer_class = MaintenanceSerializer



	def get_object(self):
		encoded_pk = self.kwargs.get('pk')
		try:
			queryset = customeFilters(self, self.get_queryset(), 'maintenance')
			# Decode the encoded ID from URL parameter
			decoded_id = MixedRadixEncoder().decode(str(encoded_pk))
			# Use the decoded ID to get the object
			return queryset.get(id=decoded_id)
		except Exception as e:
			print(f"Invalid encoded ID: {self.kwargs['pk']}")
			raise Http404("Object not found")

	def perform_update(self, serializer):
		serializer.save(last_updated_by=self.request.user)

	def get(self, request, *args, **kwargs):
		return self.retrieve(request, *args, **kwargs)

	# def put(self, request, *args, **kwargs):
	# 	return self.update(request, *args, **kwargs)

	@transaction.atomic
	def patch(self, request, *args, **kwargs):
		instance = self.get_object()
		
		serializer = self.get_serializer(instance, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		self.perform_update(serializer)
		
		# 3. Refresh or use the updated instance directly
		instance.refresh_from_db()

		a = ValidateItemsStock()
		items_ids = [item.spare_part.id for item in instance.parts.all()]
		a.stock_validation(
			item_ids=items_ids, 
			log_mismatches=False, 
			raise_on_negative=True if instance.maintenance_date else False
		)

		return Response(serializer.data)

	def delete(self, request, *args, **kwargs):
		return self.destroy(request, *args, **kwargs)
