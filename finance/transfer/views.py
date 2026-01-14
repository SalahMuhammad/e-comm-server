from django.http import Http404
from common.encoder import MixedRadixEncoder
# django filters
from django_filters.rest_framework import DjangoFilterBackend
# 
from finance.transfer.serializers import TransferSerializer
from .services.filters import TransferFilter
# models
from finance.transfer.models import MoneyTransfer
# 
from rest_framework import mixins
from rest_framework.generics import GenericAPIView



class ListCreateView(
	mixins.ListModelMixin,
	mixins.CreateModelMixin,
	GenericAPIView,
):
	queryset = MoneyTransfer.objects.select_related(
		'created_by',
		'last_updated_by',
		'from_vault',
		'from_vault__account_type',
		'to_vault',
		'to_vault__account_type',
	).all()
	serializer_class = TransferSerializer
	# Adding filtering backends
	filter_backends = [DjangoFilterBackend]
	filterset_class = TransferFilter


	def get(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user, last_updated_by=self.request.user)



class DetailView(
	mixins.RetrieveModelMixin, 
	mixins.UpdateModelMixin,
	mixins.DestroyModelMixin,
	GenericAPIView
):
	queryset = MoneyTransfer.objects.select_related(
		'created_by',
		'last_updated_by',
		'from_vault',
		'from_vault__account_type',
		'to_vault',
		'to_vault__account_type',
	).all()
	serializer_class = TransferSerializer


	def get_object(self):
		encoded_pk = self.kwargs.get('pk')
		try:
			decoded_id = MixedRadixEncoder().decode(str(encoded_pk))
			return self.get_queryset().get(id=decoded_id)
		except Exception as e:
			print(f"Invalid encoded ID: {self.kwargs['pk']}")
			raise Http404("Object not found")

	def get(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)

	def patch(self, request,*args, **kwargs):
		instance = self.get_object()
		
		# Handle proof deletion
		# Use request.data instead of request.POST to handle both JSON and form-data
		keep_proof = request.data.get('keep_proof', 'true')
		proof_file = request.FILES.get('proof')
		
		# If keep_proof is 'false' and no new file uploaded, delete the existing image
		if keep_proof == 'false' and not proof_file and instance.proof:
			instance.proof = None
			instance.save()
		
		return super().partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		return super().destroy(request, *args, **kwargs)
	
	def perform_update(self, serializer):
		serializer.save(last_updated_by=self.request.user)
