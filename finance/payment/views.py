from django.http import Http404, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from common.encoder import MixedRadixEncoder
# django filters
from django_filters.rest_framework import DjangoFilterBackend
# 
from finance.payment.serializers import PaymentSerializer
from finance.vault_and_methods.services import calculate_owner_credit_balance
from .services.filters import PaymentFilter
# models
from finance.payment.models import Payment2
from invoices.sales.models import SalesInvoice
# 
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response



@staff_member_required
def get_sales_for_owner(request):
	owner_id = request.GET.get('owner_id')
	sales = SalesInvoice.objects.filter(owner_id=owner_id).values('id', 'reference', 'total_amount')
	return JsonResponse(list(sales), safe=False)



class ListCreateView(
	mixins.ListModelMixin,
	mixins.CreateModelMixin,
	GenericAPIView,
):
	queryset = Payment2.objects.select_related(
		'owner',
		'created_by',
		'last_updated_by',
		'business_account',
		'business_account__account_type',
		'sale'
	).all()
	serializer_class = PaymentSerializer
	# Adding filtering backends
	filter_backends = [DjangoFilterBackend]
	filterset_class = PaymentFilter


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
	queryset = Payment2.objects.select_related(
		'owner',
		'created_by',
		'last_updated_by',
		'business_account',
		'business_account__account_type',
		'sale'
	).all()
	serializer_class = PaymentSerializer


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
		return super().partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		return super().destroy(request, *args, **kwargs)
	
	def perform_update(self, serializer):
		serializer.save(last_updated_by=self.request.user)
