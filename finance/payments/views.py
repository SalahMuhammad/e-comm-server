from django.http import Http404
from common.encoder import MixedRadixEncoder
from common.utilities import get_pagination_class
from invoices.purchase.models import PurchaseInvoices
from invoices.sales.models import SalesInvoice, ReturnInvoice
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.generics import GenericAPIView
from .models import Payment, ExpensePayment
from finance.debt_settlement.models import DebtSettlement
from .serializers import PaymentSerializer, ExpensePaymentSerializer
from invoices.buyer_supplier_party.models import InitialCreditBalance
from django.db.models import Sum
from django.db.models import Q
from rest_framework.response import Response



def calculate_client_credit_balance(client_id, date):
    datee = Q(date__lte=date) if date else Q(id__isnull=False)
    issue_date = Q(issue_date__lte=date) if date else Q(id__isnull=False)

    total = 0
    try:
        p_invs = PurchaseInvoices.objects.filter(issue_date, owner_id=client_id, repository_permit=True)
        s_invs = SalesInvoice.objects.filter(issue_date, owner_id=client_id, repository_permit=True)
        payments = Payment.objects.filter(datee, owner_id=client_id, paid=True)
        return_sales_invs = ReturnInvoice.objects.filter(issue_date, owner_id=client_id, repository_permit=True)
        reverse_payment = ExpensePayment.objects.filter(datee, owner_id=client_id, paid=True)
        initial_credit_balance = InitialCreditBalance.objects.filter(datee, party_id=client_id)
        total_debt_settlement = DebtSettlement.objects.filter(
            datee, 
            owner_id=client_id, 
            status="approved"
        ).aggregate(
            total=Sum('amount'),
        )['total'] or 0
    
    
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

        reverse_payment = reverse_payment.aggregate(
            total=Sum('amount'),
        )['total'] or 0

        total -= p_inv_credit 
        total += s_inv_credit 
        total += initial_credit_balance 
        total -= payments 
        total -= sales_refund 
        total += reverse_payment
        total -= total_debt_settlement
    except Exception as e:
        return e

    return total


class ListCreateView(
    ListModelMixin,
    CreateModelMixin,
    GenericAPIView
):
    queryset = Payment.objects.select_related(
        'owner',
        'by',
        'payment_method'
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
            credit = calculate_client_credit_balance(owner_id, date)
            return Response({
                'credit': credit
            })

        return super().list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class DetailPaymentView(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericAPIView
):
    queryset = Payment.objects.select_related(
        'owner',
        'by',
        'payment_method'
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

    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ListCreateExpensePaymentView(
    ListModelMixin,
    CreateModelMixin,
    GenericAPIView
):
    queryset = ExpensePayment.objects.select_related(
        'owner',
        'by',
        'payment_method'
    ).all()
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
    queryset = ExpensePayment.objects.select_related(
        'owner',
        'by',
        'payment_method'
    ).all()
    serializer_class = ExpensePaymentSerializer

    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)