from .models import Party
from .serializers import PartySerializers
from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError

from rest_framework.decorators import api_view
from finance.payments.views import calculate_client_credit_balance
from refillable_items_system.views import calculateRefillableItemsClientHas


@api_view(['GET'])
def ownerView(request, *args, **kwargs):
    datee = request.GET.get('date', None)
    client_id = kwargs['pk']
    credit = calculate_client_credit_balance(client_id, datee)
    refillable_items = calculateRefillableItemsClientHas(client_id)
    return Response({
        'credit': credit,
        'refillable_items_client_has': refillable_items
    })

@api_view(['GET'])
def listClientCredits(request, *args, **kwargs):
    l = []
    for client in Party.objects.all():
        credit = calculate_client_credit_balance(client.id, None)
        
        if credit != 0:
            l.append({
                "name": client.name,
                "amount": credit
            })

    return Response({
        'list': l
    })


from invoices.sales.models import SalesInvoice, ReturnInvoice as ReturnSalesInvoice
from invoices.sales.serializers import InvoiceSerializer, ReturnInvoiceSerializer as ReturnSalesInvoiceSerializer
from invoices.purchase.serializers import InvoiceSerializer as PurchaseInvoiceSerializer
from invoices.buyer_supplier_party.models import InitialCreditBalance
from invoices.buyer_supplier_party.serializers import InitialCreditBalanceSerializer
from finance.payments.serializers import PaymentSerializer, ExpensePaymentSerializer
from invoices.purchase.models import PurchaseInvoices
from finance.payments.models import Payment, ExpensePayment
from itertools import chain
from django.db.models import Sum

def get_date(obj):
        if hasattr(obj, 'date'):
            return obj.date
        elif isinstance(obj, SalesInvoice):
            return obj.issue_date
        elif isinstance(obj, PurchaseInvoices):
            return obj.issue_date
        elif isinstance(obj, ReturnSalesInvoice):
            return obj.issue_date

        return None

@api_view(['GET'])
def customerAccountStatement(request, *args, **kwargs):
    owner_id = kwargs['pk']
    initial_credit_balance = InitialCreditBalance.objects.filter(party_id=owner_id)
    sales_invs = SalesInvoice.objects.filter(owner_id=owner_id)
    return_sales_invs = ReturnSalesInvoice.objects.filter(owner_id=owner_id)
    purcahses_invs = PurchaseInvoices.objects.filter(owner_id=owner_id)
    payments = Payment.objects.filter(owner_id=owner_id)
    revers_payments = ExpensePayment.objects.filter(owner_id=owner_id)


    initial_credit_balance_total_credit = initial_credit_balance.aggregate(total_amount=Sum('amount'))
    s_invs_total_credit = sales_invs.aggregate(total_amount=Sum('total_amount'))
    return_sales_invs_total_credit = return_sales_invs.aggregate(total_amount=Sum('total_amount'))
    purcahses_invs_total_credit = purcahses_invs.aggregate(total_amount=Sum('total_amount'))
    payments_total_credit = payments.aggregate(total_amount=Sum('amount'))
    revers_payments_total = revers_payments.aggregate(total=Sum('amount'))

    result_list = sorted(
        chain(sales_invs, return_sales_invs, purcahses_invs, payments, initial_credit_balance, revers_payments),
        key=get_date,
        # reverse=True,
    )

    list = []
    for instance in result_list:
        if isinstance(instance, SalesInvoice):
            serializer = InvoiceSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'sales invoice'
            list.append(data_dict)
        elif isinstance(instance, ReturnSalesInvoice):
            serializer = ReturnSalesInvoiceSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'return sales invoice'
            list.append(data_dict)
        elif isinstance(instance, PurchaseInvoices):
            serializer = PurchaseInvoiceSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'purchase invoice'
            list.append(data_dict)
        elif isinstance(instance, Payment):
            serializer = PaymentSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'payment'
            list.append(data_dict)
        elif isinstance(instance, InitialCreditBalance):
            serializer = InitialCreditBalanceSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'initial credit balance'
            list.append(data_dict)
        elif isinstance(instance, ExpensePayment):
            serializer = ExpensePaymentSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'reverse payment'
            list.append(data_dict)


    return Response({
        'sales_invs': sales_invs.count(),
        'return_sales_invs': return_sales_invs.count(),
        'purcahses_invs': purcahses_invs.count(),
        'payments': payments.count(),
        'credit_totals': {
            'Initial Credit Balance': initial_credit_balance_total_credit['total_amount'] if initial_credit_balance_total_credit['total_amount'] else 0,
            'Sales Invoices': s_invs_total_credit['total_amount'] if s_invs_total_credit['total_amount'] else 0,
            'Return Sales Invoices': - return_sales_invs_total_credit['total_amount'] if return_sales_invs_total_credit['total_amount'] else 0,
            'Purchase Invoices': - purcahses_invs_total_credit['total_amount'] if purcahses_invs_total_credit['total_amount'] else 0,
            'payments': - payments_total_credit['total_amount'] if payments_total_credit['total_amount'] else 0,
            'Revers Payments': revers_payments_total['total'] if revers_payments_total['total'] else 0,
        },
        "list": list,
    })





class ListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset = Party.objects.all()
    serializer_class = PartySerializers

    def get_queryset(self):
        name_param = self.request.query_params.get('s')
        pk_param = self.request.query_params.get('pk')

        if name_param:
            q = self.queryset.filter(name__icontains=name_param)
            return q
        if pk_param:
            q = self.queryset.filter(id=pk_param)
            return q

        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class DetailView(
    mixins.RetrieveModelMixin, 
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    queryset = Party.objects.all()
    serializer_class = PartySerializers


    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request,*args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as e:
            return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
  

