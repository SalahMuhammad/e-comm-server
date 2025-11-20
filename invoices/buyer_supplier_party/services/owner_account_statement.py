from finance.payment.models import Payment2
from finance.reverse_payment.models import ReversePayment
from finance.debt_settlement.models import DebtSettlement
from invoices.buyer_supplier_party.models import InitialCreditBalance
from invoices.sales.models import SalesInvoice, ReturnInvoice as ReturnSalesInvoice
from invoices.purchase.models import PurchaseInvoices
# 
from invoices.buyer_supplier_party.serializers import InitialCreditBalanceSerializer
from invoices.sales.serializers import InvoiceSerializer, ReturnInvoiceSerializer as ReturnSalesInvoiceSerializer
from finance.debt_settlement.serializers import DebtSettlementSerializer
from invoices.purchase.serializers import InvoiceSerializer as PurchaseInvoiceSerializer
from finance.payments.serializers import PaymentSerializer, ExpensePaymentSerializer
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
		'original_invoice'
	).filter(
        owner_id=owner_id,
        repository_permit=True
    ).prefetch_related(
		's_invoice_items__item', 
		's_invoice_items__repository'
	)
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
        'by',
        'payment_method'
    ).filter(owner_id=owner_id)
    revers_payments = ReversePayment.objects.select_related(
        'owner',
        'by',
        'payment_method'
    ).filter(owner_id=owner_id)
    debt_settlement = DebtSettlement.objects.select_related(
        'owner',
        'by',
    ).filter(
        owner_id=owner_id,
        status='approved'
    )


    initial_credit_balance_total_credit = initial_credit_balance.aggregate(total_amount=Sum('amount'))
    s_invs_total_credit = sales_invs.aggregate(total_amount=Sum('total_amount'))
    return_sales_invs_total_credit = return_sales_invs.aggregate(total_amount=Sum('total_amount'))
    purcahses_invs_total_credit = purcahses_invs.aggregate(total_amount=Sum('total_amount'))
    payments_total_credit = payments.aggregate(total_amount=Sum('amount'))
    revers_payments_total = revers_payments.aggregate(total=Sum('amount'))
    # detbt_settlement_total = debt_settlement.aggregate(total=Sum('amount'))

    result_list = sorted(
        chain(
            sales_invs, 
            return_sales_invs, 
            purcahses_invs, 
            payments, 
            initial_credit_balance, 
            revers_payments,
            debt_settlement,
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
        elif isinstance(instance, ReversePayment):
            serializer = ExpensePaymentSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'reverse payment'
            list.append(data_dict)
        elif isinstance(instance, DebtSettlement):
            serializer = DebtSettlementSerializer(instance)
            data_dict = dict(serializer.data)
            data_dict['type'] = 'debt settlement'
            data_dict['amount'] = Decimal(data_dict["amount"]) * -1
            list.append(data_dict)

    return {
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
    }

def getOwnerAccountStatementAsHttpResponse(owner_id):
    return Response(getOwnerAccountStatement(owner_id))
