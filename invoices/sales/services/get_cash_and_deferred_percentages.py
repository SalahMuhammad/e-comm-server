from django.db.models import Sum, Count, Q
from decimal import Decimal
from finance.payment.models import Payment2
from finance.reverse_payment.models import ReversePayment2
from invoices.sales.models import SalesInvoice
from invoices.purchase.models import PurchaseInvoices
from invoices.buyer_supplier_party.models import Party


def get_cash_deferred_percentages():
    """
    Calculate the percentage of cash (confirmed) vs deferred (pending) transactions.
    
    Considers both:
    - Payment2: Sales payments
    - ReversePayment2: Purchase reverse payments
    
    Returns:
        dict: Contains 'cash_percentage', 'deferred_percentage', and transaction amounts
    """
    # total = 0

    # Get confirmed (cash) transactions
    sales_orders_total = SalesInvoice.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

    dual_owners = [a[0] for a in get_customers_with_both_invoices()]
    purchas_orders_total = PurchaseInvoices.objects.filter(
        owner_id__in=dual_owners
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

    # Get confirmed (cash) transactions
    confirmed_payments = Payment2.objects.filter(
        status='2'  # Confirmed
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    confirmed_reverse_payments = ReversePayment2.objects.filter(
        status='2',  # Confirmed
        owner_id__in=dual_owners
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return {
        'total_orders': sales_orders_total - (purchas_orders_total - confirmed_reverse_payments),
        'total_payed': confirmed_payments,
    }


def get_customers_with_both_invoices():
    """
    Get all customers (Party) that have both purchase and sales invoices.
    
    Returns:
        QuerySet: Party objects with both sales and purchase invoices
    """
    return Party.objects.annotate(
        sales_count=Count('salesinvoice', filter=Q(salesinvoice__isnull=False)),
        purchase_count=Count('purchaseinvoices', filter=Q(purchaseinvoices__isnull=False))
    ).filter(
        sales_count__gt=0,
        purchase_count__gt=0
    ).values_list('id', 'name')
