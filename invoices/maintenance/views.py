from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from metadata.base import CompositeMetadata

from .models import Maintenance, TransactionSpareParts
from .serializers import MaintenanceSerializer, TransactionSparePartsSerializer
from common.encoder import MixedRadixEncoder
from django.http import Http404


class MaintenanceView(mixins.CreateModelMixin, mixins.ListModelMixin, generics.GenericAPIView):
	queryset = Maintenance.objects.select_related(
		'client', 'item', 'by', 'created_by', 'last_updated_by'
	).prefetch_related('parts')
	metadata_class = CompositeMetadata
	serializer_class = MaintenanceSerializer
	permission_classes = [IsAuthenticated]
	filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	filterset_fields = ['status', 'client', 'item', 'date_in']
	search_fields = ['serial_number', 'client__name', 'item__name']
	ordering_fields = ['date_in', 'created_at']
	ordering = ['-date_in']

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user, last_updated_by=self.request.user)

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)


class MaintenanceDetailView(
	mixins.RetrieveModelMixin,
	mixins.UpdateModelMixin,
	mixins.DestroyModelMixin,
	generics.GenericAPIView
):
	queryset = Maintenance.objects.select_related(
		'client', 'item', 'by', 'created_by', 'last_updated_by'
	).prefetch_related('parts')
	serializer_class = MaintenanceSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		encoded_pk = self.kwargs.get('pk')
		try:
			# Decode the encoded ID from URL parameter
			decoded_id = MixedRadixEncoder().decode(str(encoded_pk))
			# Use the decoded ID to get the object
			return self.get_queryset().get(id=decoded_id)
		except Exception as e:
			print(f"Invalid encoded ID: {self.kwargs['pk']}")
			raise Http404("Object not found")

	def perform_update(self, serializer):
		serializer.save(last_updated_by=self.request.user)

	def get(self, request, *args, **kwargs):
		return self.retrieve(request, *args, **kwargs)

	def put(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		return self.partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		return self.destroy(request, *args, **kwargs)
