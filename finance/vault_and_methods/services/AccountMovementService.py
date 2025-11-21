from finance.payment.models import Payment2
from finance.reverse_payment.models import ReversePayment2
from finance.expenses.models import Expense
from finance.transfer.models import MoneyTransfer

from django.db.models import Q, Sum, DecimalField, Value, CharField, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import date
from typing import Optional, List, Dict, Any
from common.encoder import MixedRadixEncoder


class AccountMovementService:
    """
    Service to track all account movements (transactions) across different transaction types.
    Supports filtering by date period and/or specific business account(s).
    """
    
    @staticmethod
    def get_movements(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[int] = None,
        account_ids: Optional[List[int]] = None,
        include_pending: bool = False
    ) -> Dict[str, Any]:
        """
        Get all account movements with optional filters.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            account_id: Single business account to filter by
            account_ids: Multiple business accounts to filter by
            include_pending: Whether to include pending transactions
            
        Returns:
            Dictionary containing movements list and summary statistics
        """        
        movements = []
        
        # Build account filter
        account_filter = Q()
        if account_id:
            account_filter = Q(business_account_id=account_id)
        elif account_ids:
            account_filter = Q(business_account_id__in=account_ids)
        
        # Build date filter
        date_filter = Q()
        if start_date:
            date_filter &= Q(date__gte=start_date)
        if end_date:
            date_filter &= Q(date__lte=end_date)
        
        # Build status filter
        status_filter = Q()
        if not include_pending:
            status_filter = Q(status__in=[2, 4])
        
        # 1. Collect Payments (Money IN)
        payments = Payment2.objects.filter(
            account_filter & date_filter & status_filter
        ).select_related('business_account', 'owner', 'sale').values(
            'id',
            'payment_ref',
            'date',
            'amount',
            'status',
            'notes',
            account_name=F('business_account__account_name'),
            account_id=F('business_account_id'),
            party_name=F('owner__name'),
            sale_ref=F('sale__id')
        )
        
        for p in payments:
            movements.append({
                'id': f"PAY-{p['id']}",
                'type': 'payment',
                'type_display': 'Payment Received',
                'reference': p['payment_ref'],
                'date': p['date'],
                'account_id': p['account_id'],
                'account_name': p['account_name'],
                'party': p['party_name'],
                'related_doc': p['sale_ref'],
                'amount_in': p['amount'],
                'amount_out': Decimal('0'),
                'status': p['status'],
                'notes': p['notes'],
            })
        

        reverse_payments = ReversePayment2.objects.filter(
            account_filter & date_filter & status_filter
        ).select_related('business_account', 'owner', 'purchase').values(
            'id',
            'payment_ref',
            'date',
            'amount',
            'status',
            'notes',
            account_name=F('business_account__account_name'),
            account_id=F('business_account_id'),
            party_name=F('owner__name'),
            purchase_ref=F('purchase__id')
        )
        
        for rp in reverse_payments:
            movements.append({
                'id': f"RPAY-{rp['id']}",
                'type': 'reverse_payment',
                'type_display': 'Payment Made',
                'reference': rp['payment_ref'],
                'date': rp['date'],
                'account_id': rp['account_id'],
                'account_name': rp['account_name'],
                'party': rp['party_name'],
                'related_doc': rp['purchase_ref'],
                'amount_in': Decimal('0'),
                'amount_out': rp['amount'],
                'status': rp['status'],
                'notes': rp['notes'],
            })
        

        expenses = Expense.objects.filter(
            account_filter & date_filter & status_filter
        ).select_related('business_account', 'category').values(
            'id',
            'date',
            'amount',
            'status',
            'notes',
            account_name=F('business_account__account_name'),
            account_id=F('business_account_id'),
            category_name=F('category__name')
        )
        
        for exp in expenses:
            movements.append({
                'id': f"EXP-{exp['id']}",
                'type': 'expense',
                'type_display': 'Expense',
                'reference': f"EXP-{exp['id']}",
                'date': exp['date'],
                'account_id': exp['account_id'],
                'account_name': exp['account_name'],
                'party': exp['category_name'] or 'N/A',
                'related_doc': None,
                'amount_in': Decimal('0'),
                'amount_out': exp['amount'],
                'status': dict(Expense.status_choices).get(exp['status']),
                'notes': exp['notes'],
            })
        

        transfer_out_filter = Q()
        if account_id:
            transfer_out_filter = Q(from_vault_id=account_id)
        elif account_ids:
            transfer_out_filter = Q(from_vault_id__in=account_ids)
        
        transfers_out = MoneyTransfer.objects.filter(
            transfer_out_filter & date_filter
        ).select_related('from_vault', 'to_vault').values(
            'id',
            'date',
            'amount',
            'transfer_type',
            'notes',
            from_account_name=F('from_vault__account_name'),
            from_account_id=F('from_vault_id'),
            to_account_name=F('to_vault__account_name')
        )
        
        for t in transfers_out:
            movements.append({
                'id': f"TFOUT-{t['id']}",
                'type': 'transfer_out',
                'type_display': 'Transfer Out',
                'reference': f"TF-{t['id']}",
                'date': t['date'],
                'account_id': t['from_account_id'],
                'account_name': t['from_account_name'],
                'party': f"To: {t['to_account_name']}",
                'related_doc': None,
                'amount_in': Decimal('0'),
                'amount_out': t['amount'],
                'status': 'Completed',
                'notes': t['notes'],
            })
        
        # 5. Collect Money Transfers IN
        transfer_in_filter = Q()
        if account_id:
            transfer_in_filter = Q(to_vault_id=account_id)
        elif account_ids:
            transfer_in_filter = Q(to_vault_id__in=account_ids)
        
        transfers_in = MoneyTransfer.objects.filter(
            transfer_in_filter & date_filter
        ).select_related('from_vault', 'to_vault').values(
            'id',
            'date',
            'amount',
            'transfer_type',
            'notes',
            to_account_name=F('to_vault__account_name'),
            to_account_id=F('to_vault_id'),
            from_account_name=F('from_vault__account_name')
        )
        
        for t in transfers_in:
            movements.append({
                'id': f"TFIN-{t['id']}",
                'type': 'transfer_in',
                'type_display': 'Transfer In',
                'reference': f"TF-{t['id']}",
                'date': t['date'],
                'account_id': t['to_account_id'],
                'account_name': t['to_account_name'],
                'party': f"From: {t['from_account_name']}",
                'related_doc': None,
                'amount_in': t['amount'],
                'amount_out': Decimal('0'),
                'status': 'Completed',
                'notes': t['notes'],
            })
        
        # Sort all movements by date (descending)
        movements.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate summary
        total_in = sum(m['amount_in'] for m in movements)
        total_out = sum(m['amount_out'] for m in movements)
        net_movement = total_in - total_out
        
        return {
            'movements': movements,
            'summary': {
                'total_in': total_in,
                'total_out': total_out,
                'net_movement': net_movement,
                'count': len(movements),
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'account_id': account_id,
                'account_ids': account_ids,
                'include_pending': include_pending,
            }
        }
    
    @staticmethod
    def get_account_balance_history(
        account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get balance history for a specific account over time.
        
        Args:
            account_id: Business account ID
            start_date: Start date for history
            end_date: End date for history
            
        Returns:
            List of balance snapshots with running balance
        """
        from django.apps import apps
        BusinessAccount = apps.get_model('finance.vault_and_methods', 'BusinessAccount')
        
        # Get opening balance
        account = BusinessAccount.objects.get(id=account_id)
        opening_balance = account.current_balance
        
        # Get movements
        result = AccountMovementService.get_movements(
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            include_pending=False
        )
        
        # Calculate running balance (assuming current_balance is accurate)
        # We work backwards from current balance
        balance_history = []
        running_balance = opening_balance
        
        # Sort movements chronologically (oldest first) for balance calculation
        movements = sorted(result['movements'], key=lambda x: x['date'])
        
        for movement in movements:
            balance_history.append({
                'date': movement['date'],
                'reference': movement['reference'],
                'type': movement['type_display'],
                'amount_in': movement['amount_in'],
                'amount_out': movement['amount_out'],
                'balance_before': running_balance,
                'balance_after': running_balance + movement['amount_in'] - movement['amount_out'],
                'notes': movement['notes'],
            })
            running_balance = running_balance + movement['amount_in'] - movement['amount_out']
        
        return balance_history
    
    @staticmethod
    def get_multi_account_summary(
        account_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get movement summary for multiple accounts.
        
        Args:
            account_ids: List of business account IDs
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Dictionary mapping account_id to summary statistics
        """
        summary_by_account = {}
        
        for account_id in account_ids:
            result = AccountMovementService.get_movements(
                start_date=start_date,
                end_date=end_date,
                account_id=account_id,
                include_pending=False
            )
            
            summary_by_account[account_id] = {
                'account_name': result['movements'][0]['account_name'] if result['movements'] else 'N/A',
                'total_in': result['summary']['total_in'],
                'total_out': result['summary']['total_out'],
                'net_movement': result['summary']['net_movement'],
                'transaction_count': result['summary']['count'],
            }
        
        return summary_by_account
