from django.db.models import Sum
from django.db.models import Q
# 
from invoices.buyer_supplier_party.models import InitialCreditBalance
from invoices.purchase.models import PurchaseInvoices
from invoices.sales.models import SalesInvoice, ReturnInvoice
from finance.debt_settlement.models import DebtSettlement
from finance.payment.models import Payment2
from finance.reverse_payment.models import ReversePayment2



def calculate_owner_credit_balance(client_id, date):
    datee = Q(date__lte=date) if date else Q(id__isnull=False)
    issue_date = Q(issue_date__lte=date) if date else Q(id__isnull=False)

    total = 0
    try:
        p_invs = PurchaseInvoices.objects.filter(issue_date, owner_id=client_id, repository_permit=True).prefetch_related('p_invoice_items__item')
        s_invs = SalesInvoice.objects.filter(issue_date, owner_id=client_id, repository_permit=True).prefetch_related('s_invoice_items__item')
        payments = Payment2.objects.filter(datee, owner_id=client_id, status=2)
        return_sales_invs = ReturnInvoice.objects.filter(issue_date, owner_id=client_id, repository_permit=True)
        reverse_payment = ReversePayment2.objects.filter(datee, owner_id=client_id, status=2)
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

