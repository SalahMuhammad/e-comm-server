from decimal import Decimal
from django.db.models import Sum
from django.core.exceptions import FieldError
# 
from finance.vault_and_methods.models import BusinessAccount
from finance.payment.models import Payment2
from finance.reverse_payment.models import ReversePayment2
from finance.expenses.models import Expense
from finance.transfer.models import MoneyTransfer
from django.db.models import Q
from django.core.exceptions import ValidationError



def get_total_money_in_vaults(account=None, is_explicit_compute_all_transactions=False) -> Decimal:
    """
    Return total money in vault(s).
    - If `account` is None: returns total across all active BusinessAccount.current_balance if present,
      otherwise computes as sum(confirmed payments) - sum(expenses) across all accounts.
    - If `account` is a BusinessAccount instance or pk: returns balance for that account.
    Raises ValueError if the computed value is less than 0.
    """
    def _to_decimal(value):
        return Decimal(value) if value is not None else Decimal('0')

    def _compute_from_transactions(acc=None):
        # build Q filters: if acc is None -> no restriction (all accounts), otherwise restrict to that account
        if acc is None:
            qb = Q(status=2) & Q(business_account__is_active=True) # for Payment2 / ReversePayment (business_account)
            q_expense = Q(status=2) & Q(business_account__is_active=True)
            q_to = Q(to_vault__is_active=True)         # for MoneyTransfer.to_vault
            q_from = Q(from_vault__is_active=True)       # for MoneyTransfer.from_vault
        else:
            qb = Q(business_account=acc) & Q(status=2)
            q_expense = Q(business_account=acc) & Q(status=2)
            q_to = Q(to_vault=acc)
            q_from = Q(from_vault=acc)

        payments_total = _to_decimal(
            Payment2.objects.select_related('business_account').filter(qb).aggregate(total=Sum('amount'))['total']
        )
        reverse_total = _to_decimal(
            ReversePayment2.objects.select_related('business_account').filter(qb).aggregate(total=Sum('amount'))['total']
        )
        expenses_total = _to_decimal(
            Expense.objects.select_related('business_account').filter(q_expense).aggregate(total=Sum('amount'))['total']
        )

        transfers_in = Decimal('0')
        transfers_out = Decimal('0')
        try:
            transfers_in = _to_decimal(
                MoneyTransfer.objects.filter(q_to).aggregate(total=Sum('amount'))['total']
            )
        except (FieldError, Exception):
            transfers_in = Decimal('0')

        try:
            transfers_out = _to_decimal(
                MoneyTransfer.objects.filter(q_from).aggregate(total=Sum('amount'))['total']
            )
        except (FieldError, Exception):
            transfers_out = Decimal('0')
        # payments_total = _to_decimal(
        #     Payment2.objects.filter(business_account=acc, status='confirmed').aggregate(total=Sum('amount'))['total']
        # )
        # reverse_total = _to_decimal(
        #     ReversePayment.objects.filter(business_account=acc, status='confirmed').aggregate(total=Sum('amount'))['total']
        # )
        # expenses_total = _to_decimal(
        #     Expense.objects.filter(account=acc, status=2).aggregate(total=Sum('amount'))['total']
        # )

        # transfers_in = Decimal('0')
        # transfers_out = Decimal('0')
        # # Query transfer fields defensively (names may vary); catch FieldError if field missing.
        # try:
        #     transfers_in = _to_decimal(
        #         MoneyTransfer.objects.filter(to_vault=acc).aggregate(total=Sum('amount'))['total']
        #     )
        # except (FieldError, Exception):
        #     transfers_in = Decimal('0')

        # try:
        #     transfers_out = _to_decimal(
        #         MoneyTransfer.objects.filter(from_vault=acc).aggregate(total=Sum('amount'))['total']
        #     )
        # except (FieldError, Exception):
        #     transfers_out = Decimal('0')
        return payments_total + transfers_in - transfers_out - expenses_total - reverse_total

    # Resolve account if provided
    if account is not None:
        if isinstance(account, BusinessAccount):
            acc = account
        else:
            acc = BusinessAccount.objects.get(pk=account)

        # Prefer explicit current_balance if it's being tracked
        if hasattr(acc, 'current_balance') and acc.current_balance is not None and not is_explicit_compute_all_transactions:
            total = Decimal(acc.current_balance)
        else:
            total = _compute_from_transactions(acc)
    else:
        # Try aggregate current_balance across accounts first
        if not is_explicit_compute_all_transactions:
            try:
                agg = BusinessAccount.objects.filter(is_active=True).aggregate(total=Sum('current_balance'))
                total = _to_decimal(agg.get('total'))
            except Exception:
                total = Decimal('0')

        elif is_explicit_compute_all_transactions:
            # If aggregate returned zero/None, fall back to transaction-based computation
            total = _compute_from_transactions()

            # payments_total = _to_decimal(
            #     Payment2.objects.filter(status='confirmed').aggregate(total=Sum('amount'))['total']
            # )
            # reverse_total = _to_decimal(
            #     ReversePayment.objects.filter(status='confirmed').aggregate(total=Sum('amount'))['total']
            # )
            # expenses_total = _to_decimal(
            #     Expense.objects.aggregate(total=Sum('amount'))['total']
            # )
            # # Transfers net to zero across all accounts; ignore unless specific fields are present and required.
            # total = payments_total - expenses_total - reverse_total

    if total < 0:
        raise ValidationError({
                'amount': f"insufficient funds: {total}"
            })

    return total
