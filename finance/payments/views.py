from common.utilities import get_pagination_class
from invoices.purchase.models import PurchaseInvoices
from invoices.sales.models import SalesInvoice, ReturnInvoice
from .models import Payment
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.generics import GenericAPIView
from .models import Payment
from .serializers import PaymentSerializer
from invoices.buyer_supplier_party.models import InitialCreditBalance
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q




# Create your views here.

def calculate_client_credit_balance(client_id):
    p_invs = PurchaseInvoices.objects.filter(owner_id=client_id)
    s_invs = SalesInvoice.objects.filter(owner_id=client_id)
    payments = Payment.objects.filter(~Q(payment_type__icontains='refund'), owner_id=client_id, paid=True)
    refund_payments = Payment.objects.filter(Q(payment_type__icontains='refund'), owner_id=client_id, paid=True)
    return_sales_invs = ReturnInvoice.objects.filter(owner_id=client_id)
    a = InitialCreditBalance.objects.filter(party_id=client_id).aggregate(
        total=Sum('amount'),
    )['total'] or 0
    
    p_inv_credit = 0
    for inv in p_invs:
        amount = 0
        for item in inv.p_invoice_items.all():
            amount   = item.quantity
            amount   *= item.unit_price
            amount   += item.tax_rate
            amount   -= item.discount
            p_inv_credit += amount
    
    s_inv_credit = 0
    for inv in s_invs:
        amount = 0
        for item in inv.s_invoice_items.all():
            amount   = item.quantity
            amount   *= item.unit_price
            amount   += item.tax_rate
            amount   -= item.discount
            s_inv_credit += amount
    
    payments_total = 0
    for payment in payments:
        payments_total += payment.amount

    refund_payments_total = 0
    for payment in refund_payments:
        refund_payments_total += payment.amount

    sales_refund = return_sales_invs.aggregate(
        total=Sum('total_amount'),
    )['total'] or 0

    total = p_inv_credit - s_inv_credit - a + payments_total + sales_refund - refund_payments_total
    return total


class ListCreateView(
    ListModelMixin,
    CreateModelMixin,
    GenericAPIView
):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


    def get_queryset(self):
        queryset = self.queryset
        self.pagination_class = get_pagination_class(self)
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        name_param = self.request.query_params.get('ownerid')
        if name_param:
            queryset = queryset.filter(owner_id=name_param)

        if from_date and to_date:
            queryset = queryset.filter(date__range=[from_date, to_date])

        return queryset

    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
