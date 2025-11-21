from django.http import Http404, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from common.encoder import MixedRadixEncoder
from common.utilities import get_pagination_class
# 
from finance.payment.serializers import PaymentSerializer
from finance.vault_and_methods.services import calculate_owner_credit_balance
# 
from finance.payment.models import Payment2
from invoices.sales.models import SalesInvoice
# 
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response



@staff_member_required
def get_sales_for_owner(request):
    owner_id = request.GET.get('owner_id')
    sales = SalesInvoice.objects.filter(owner_id=owner_id).values('id', 'reference', 'total_amount')
    return JsonResponse(list(sales), safe=False)


class ListCreateView(
    ListModelMixin,
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


    def get_queryset(self):
        queryset = self.queryset
        self.pagination_class = get_pagination_class(self)
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        owner = self.request.query_params.get('owner')
        if owner:
            queryset = queryset.filter(owner_id__name__icontains=owner)

        Payment_no = self.request.query_params.get('no')
        id = -1
        if Payment_no:
            try:
                id = MixedRadixEncoder().decode(Payment_no)  # Validate the encoded ID
            except:
                print(f"Invalid encoded ID: {Payment_no}")
				
            queryset = queryset.filter(pk=id)

        if from_date and to_date:
            queryset = queryset.filter(date__range=[from_date, to_date])

            if self.request.query_params.get('sum'):
                # expences = expences.aggregate(
                #     total=Sum('amount'),
                # )['total'] or 0
                pass
                # queryset = queryset.aggregate(total=Sum('amount'),)['total'] or 0

        return queryset

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



class DetailView(
    RetrieveModelMixin,
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

    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
