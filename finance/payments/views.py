from common.utilities import get_pagination_class
from invoices.purchase.models import PurchaseInvoices
from invoices.sales.models import SalesInvoice, ReturnInvoice
from .models import Payment
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.generics import GenericAPIView
from .models import Payment, ExpensePayment
from .serializers import PaymentSerializer, ExpensePaymentSerializer
from invoices.buyer_supplier_party.models import InitialCreditBalance
from django.db.models import Sum
from django.db.models import Q



# Create your views here.

def calculate_client_credit_balance(client_id, date):
    datee = Q(date__lt=date) if date else Q(id__isnull=False)
    issue_date = Q(issue_date__lt=date) if date else Q(id__isnull=False)

    p_invs = PurchaseInvoices.objects.filter(issue_date, owner_id=client_id)
    s_invs = SalesInvoice.objects.filter(issue_date, owner_id=client_id)
    payments = Payment.objects.filter(datee, owner_id=client_id, paid=True)
    return_sales_invs = ReturnInvoice.objects.filter(issue_date, owner_id=client_id)
    expences = ExpensePayment.objects.filter(datee, owner_id=client_id, paid=True)
    initial_credit_balance = InitialCreditBalance.objects.filter(datee, party_id=client_id)
    
    initial_credit_balance = initial_credit_balance.aggregate(
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
    
    payments = payments.aggregate(
        total=Sum('amount'),
    )['total'] or 0

    sales_refund = return_sales_invs.aggregate(
        total=Sum('total_amount'),
    )['total'] or 0

    expences = expences.aggregate(
        total=Sum('amount'),
    )['total'] or 0

    total = 0
    total -= p_inv_credit 
    total += s_inv_credit 
    total += initial_credit_balance 
    total -= payments 
    total -= sales_refund 
    total += expences

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
        return self.create(request, *args, **kwargs)


class DetailPaymentView(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericAPIView
):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ListCreateExpensePaymentView(
    ListModelMixin,
    CreateModelMixin,
    GenericAPIView
):
    queryset = ExpensePayment.objects.all()
    serializer_class = ExpensePaymentSerializer


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
        return self.create(request, *args, **kwargs)


class DetailExpensePaymentView(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericAPIView
):
    queryset = ExpensePayment.objects.all()
    serializer_class = ExpensePaymentSerializer

    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)