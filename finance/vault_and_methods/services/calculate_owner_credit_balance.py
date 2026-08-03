from django.db.models import Sum
from django.db.models import Q
# 
from invoices.buyer_supplier_party.models import InitialCreditBalance
from invoices.purchase.models import PurchaseInvoices
from invoices.sales.models import SalesInvoice, ReturnInvoice
from invoices.maintenance.models import Maintenance
from finance.debt_settlement.models import DebtSettlement
from finance.payment.models import Payment2
from finance.reverse_payment.models import ReversePayment2



def calculate_owner_credit_balance(client_id, date):
    datee = Q(date__lte=date) if date else Q(id__isnull=False)
    issue_date = Q(issue_date__lte=date) if date else Q(id__isnull=False)

    total = 0
    try:
        p_invs_total = calculate_models_total(PurchaseInvoices, {
                "owner_id": client_id, 
                "repository_permit": True
            }, 
            'total_amount',
            issue_date
        )

        s_invs_total = calculate_models_total(SalesInvoice, { 
                "owner": client_id, 
                "repository_permit": True
            }, 
            'total_amount',
            issue_date
        )

        maintenance_total = calculate_models_total(Maintenance, {
                "client": client_id,
                "maintenance_date__isnull": False, 
                "date_out__isnull": False,
            }, 
            'cost',
            Q(date_out__lte=date) if date else Q(id__isnull=False)
        )

        payment_total = calculate_models_total(Payment2, { 
                "owner": client_id, 
                "status": 2
            }, 
            'amount',
            datee
        )

        sales_refund_total = calculate_models_total(ReturnInvoice, { 
                "owner": client_id, 
                "repository_permit": True
            }, 
            'total_amount',
            issue_date
        )

        reverse_payment_total = calculate_models_total(ReversePayment2, { 
                "owner": client_id, 
                "status": 2
            }, 
            'amount',
            datee
        )

        initial_credit_balance_total = calculate_models_total(InitialCreditBalance, { 
                "party": client_id, 
            }, 
            'amount',
            datee
        )

        total_debt_settlement_total = calculate_models_total(DebtSettlement, { 
                "owner": client_id, 
                "status": "approved"
            }, 
            'amount',
            datee
        )

        total -= p_invs_total 
        total += s_invs_total 
        total += maintenance_total
        total += initial_credit_balance_total 
        total -= payment_total 
        total -= sales_refund_total 
        total += reverse_payment_total
        total -= total_debt_settlement_total
    except Exception as e:
        return e

    return total

def calculate_models_total(model, filter_obj, total_key, q_object_date):
    return model.objects.filter(
        q_object_date,
        **filter_obj
    ).aggregate(
        total=Sum(total_key),
    )['total'] or 0
