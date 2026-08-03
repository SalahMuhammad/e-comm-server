from finance.payment.models import Payment2
from finance.reverse_payment.models import ReversePayment2
from finance.debt_settlement.models import DebtSettlement
from invoices.buyer_supplier_party.models import InitialCreditBalance
from invoices.sales.models import SalesInvoice, ReturnInvoice as ReturnSalesInvoice
from invoices.purchase.models import PurchaseInvoices
from invoices.maintenance.models import Maintenance
# 
from invoices.buyer_supplier_party.serializers import InitialCreditBalanceSerializer
from invoices.sales.serializers import InvoiceSerializer, ReturnInvoiceSerializer as ReturnSalesInvoiceSerializer
from invoices.maintenance.serializers import MaintenanceSerializer
from finance.debt_settlement.serializers import DebtSettlementSerializer
from invoices.purchase.serializers import InvoiceSerializer as PurchaseInvoiceSerializer
from finance.payment.serializers import PaymentSerializer
from finance.reverse_payment.serializers import ReversePaymentSerializer
# 
from itertools import chain
from decimal import Decimal
# 
from django.db.models import Sum
# 
from rest_framework.response import Response



def get_date(obj):
    if hasattr(obj, 'date'):
        return obj.date
    elif isinstance(obj, SalesInvoice):
        return obj.issue_date
    elif isinstance(obj, PurchaseInvoices):
        return obj.issue_date
    elif isinstance(obj, ReturnSalesInvoice):
        return obj.issue_date
    elif isinstance(obj, Maintenance):
        return obj.date_out

    return None

def getOwnerAccountStatement(owner_id):
    initial_credit_balance = InitialCreditBalance.objects.filter(party_id=owner_id)
    sales_invs = SalesInvoice.objects.select_related(
        'by', 
        'owner'
    ).filter(
        owner_id=owner_id,
        repository_permit=True
    ).prefetch_related(
        's_invoice_items__item', 
		's_invoice_items__repository'
    )
    return_sales_invs = ReturnSalesInvoice.objects.select_related(
		'by', 
		'owner', 
		'original_invoice',
	).filter(
        owner_id=owner_id,
        repository_permit=True
    ).prefetch_related(
		's_invoice_items__item', 
		's_invoice_items__repository'
	)
    maintenances = Maintenance.objects.select_related(
        'client', 'created_by', 'last_updated_by'
    ).filter(
        client_id=owner_id,
        maintenance_date__isnull=False,
        date_out__isnull=False
    ).prefetch_related('parts', 'parts__spare_part')
    purcahses_invs = PurchaseInvoices.objects.select_related(
        'by', 
        'owner'
    ).filter(
        owner_id=owner_id,
        repository_permit=True
    ).prefetch_related(
        'p_invoice_items__item', 
		'p_invoice_items__repository'
    )
    payments = Payment2.objects.select_related(
        'owner',
        'created_by',
        'last_updated_by',
        'business_account',
        'business_account__account_type',
        'sale'
    ).filter(owner_id=owner_id)
    revers_payments = ReversePayment2.objects.select_related(
        'owner',
        'created_by',
        'last_updated_by',
        'business_account',
        'business_account__account_type',
        'purchase'
    ).filter(owner_id=owner_id)
    debt_settlement = DebtSettlement.objects.select_related(
        'owner',
        'by',
    ).filter(
        owner_id=owner_id,
        status='approved'
    )
    
    models = [
        {
            "queryset": initial_credit_balance,
            "price_key": "amount",
        },
        {
            "queryset": sales_invs,
            "price_key": "total_amount",
        },
        {
            "queryset": return_sales_invs,
            "price_key": "total_amount",
        },
        {
            "queryset": maintenances,
            "price_key": "cost",
        },
        {
            "queryset": purcahses_invs,
            "price_key": "total_amount",
        },
        {
            "queryset": payments,
            "price_key": "amount",
        },
        {
            "queryset": revers_payments,
            "price_key": "amount",
        },
        {
            "queryset": debt_settlement,
            "price_key": "amount",
        },
    ]

    totals = {}
    transactionCount = {}
    for m in models:
        total = m["queryset"].aggregate(total=Sum(m["price_key"]))['total'] or 0
        if total:
            model_name = m["queryset"].model.__name__
            transactionCount[model_name] = m["queryset"].count()
            totals[model_name] = total

    result_list = sorted(
        chain(
            sales_invs, 
            return_sales_invs, 
            purcahses_invs, 
            payments, 
            initial_credit_balance, 
            revers_payments,
            debt_settlement,
            maintenances,
        ),
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
            data_dict['type'] = 'sales invoice refund'
            data_dict['total_amount'] = f'-{data_dict["total_amount"]}'
            list.append(data_dict)
        elif isinstance(instance, PurchaseInvoices):
            serializer = PurchaseInvoiceSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'purchase invoice'
            data_dict['total_amount'] = f'-{data_dict["total_amount"]}'
            list.append(data_dict)
        elif isinstance(instance, Payment2):
            serializer = PaymentSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'payment'
            data_dict['amount'] = f'-{data_dict["amount"]}'
            list.append(data_dict)
        elif isinstance(instance, InitialCreditBalance):
            serializer = InitialCreditBalanceSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'due from last year'
            list.append(data_dict)
        elif isinstance(instance, ReversePayment2):
            serializer = ReversePaymentSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'reverse payment'
            list.append(data_dict)
        elif isinstance(instance, DebtSettlement):
            serializer = DebtSettlementSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'debt settlement'
            data_dict['amount'] = Decimal(data_dict["amount"]) * -1
            list.append(data_dict)
        elif isinstance(instance, Maintenance):
            serializer = MaintenanceSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'maintenance'
            data_dict['hashed_id'] = data_dict['_hashed_id']
            data_dict['date'] = data_dict['date_out']
            data_dict['amount'] = Decimal(data_dict["cost"])
            if data_dict['amount'] == 0: continue
            list.append(data_dict)

    return {
        'owner_id': owner_id,
        'count': {
            **transactionCount
        },
        'credit_totals': {
            **totals
        },
        "list": list,
    }

def getOwnerAccountStatementAsHttpResponse(owner_id):
    return Response(getOwnerAccountStatement(owner_id))
