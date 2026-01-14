from django.http import Http404
from common.encoder import MixedRadixEncoder
# django filters
from django_filters.rest_framework import DjangoFilterBackend
#
from finance.vault_and_methods.services import calculate_owner_credit_balance
from .serializers import ReversePaymentSerializer
from .services.filters import ReversePaymentFilter
# models
from .models import ReversePayment2
# 
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response



class ListCreateView(
	mixins.ListModelMixin,
	mixins.CreateModelMixin,
	GenericAPIView,
):
	queryset = ReversePayment2.objects.select_related(
		'owner',
		'created_by',
		'last_updated_by',
		'business_account',
		'business_account__account_type',
		'purchase'
	).all()
	serializer_class = ReversePaymentSerializer
	# Adding filtering backends
	filter_backends = [DjangoFilterBackend]
	filterset_class = ReversePaymentFilter


	def get(self, request, *args, **kwargs):
		# ?owner-id=1000015&date=2025-04-20&credit-balance=1
		credit_balance = request.GET.get('credit-balance')
		date = request.GET.get('date')
		owner_id = request.GET.get('owner-id')
		if credit_balance and date and owner_id:
			credit = calculate_owner_credit_balance(owner_id, date)
			return Response({
				'credit': credit
			})
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
	queryset = ReversePayment2.objects.select_related(
		'owner',
		'created_by',
		'last_updated_by',
		'business_account',
		'business_account__account_type',
		'purchase'
	).all()
	serializer_class = ReversePaymentSerializer


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
		
		# Handle payment_proof deletion
		# Use request.data instead of request.POST to handle both JSON and form-data
		keep_payment_proof = request.data.get('keep_payment_proof', 'true')
		payment_proof_file = request.FILES.get('payment_proof')
		
		# If keep_payment_proof is 'false' and no new file uploaded, delete the existing image
		if keep_payment_proof == 'false' and not payment_proof_file and instance.payment_proof:
			instance.payment_proof = None
			instance.save() 
		
		return super().partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		return super().destroy(request, *args, **kwargs)
	
	def perform_update(self, serializer):
		serializer.save(last_updated_by=self.request.user)

