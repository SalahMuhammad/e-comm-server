from django.db.models import Sum
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date
from django.db.models import Q


class ItemMovementService:
    """Service to handle item movement reporting across all related models."""
    
    def __init__(self, item = None):
        self.item = item
    
    def get_movement_report(self, 
                          start_date: Optional[date] = None, 
                          end_date: Optional[date] = None,
                          repository: Optional[int] = None) -> Dict:
        """
        Generate comprehensive movement report for an item.
        
        Args:
            start_date: Start date for the report period
            end_date: End date for the report period
            repository_id: Specific repository to filter by
            
        Returns:
            Dict containing movement summary and details
        """

        repositoryyy = repository if hasattr(repository, 'id') else None
        
        # Get all movements
        movements = self._get_all_movements(start_date, end_date, repositoryyy.id if hasattr(repositoryyy, 'id') else None)
        
        # Calculate totals
        # totals = self._calculate_totals(movements)
        
        # Calculate final stock
        # final_stock = initial_stock + totals['net_movement']

        
        return {
            'details': {
                'item': self.item.name if self.item else 'all',
                'repository': repositoryyy.name if hasattr(repositoryyy, 'name') else 'all',
                'sku': getattr(self.item, 'sku', None),
            },
            'period': {
                'start_date': start_date or 'all',
                'end_date': end_date or 'all',
            },
            'stock_summa'
            'ry': {
                # 'initial_stock': initial_stock,
                # 'final_stock': final_stock,
                # 'net_movement': totals['net_movement']
            },
            # 'movement_totals': totals,
            'movements': movements,
            # 'movement_breakdown': self._get_movement_breakdown(movements)
        }
    
    def _get_initial_stock(self, start_date, end_date, repository_id: Optional[int] = None) -> Decimal:
        """Get initial stock quantity."""
        from items.models import InitialStock
        
        queryset = InitialStock.objects.filter(Q(item=self.item) if self.item else Q())
        queryset = self._apply_date_filter(queryset, start_date, end_date)
        
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        
        movements = []
        for transaction in queryset: #.select_related('repository'):
            movements.append({
                'date': transaction.date,
                'type': 'initial_stock',
                'reference_id': transaction.id,
                # 'reference_number': getattr(sale, 'sale_number', f"SALE-{sale.id}"),
                'quantity': transaction.quantity,  # Negative for outgoing
                # 'unit_price': sale.unit_price,
                # 'total_value': -sale.total_value,
                # 'repository': sale.repository.name if sale.repository else None,
                # 'repository_id': sale.repository_id,
                # 'notes': getattr(sale, 'notes', ''),
                # 'owner': transaction.owner.name
            })
        
        return movements
        return queryset.aggregate(
            total=Sum('quantity')
        )['total'] or Decimal('0')
    
    def _get_all_movements(self, 
                          start_date: Optional[date], 
                          end_date: Optional[date],
                          repository_id: Optional[int]) -> List[Dict]:
        """Collect all movements from different models."""
        movements = []

        # Get initial stock (incoming)
        movements.extend(self._get_initial_stock(start_date, end_date, repository_id))
        
        # Sales (outgoing)
        movements.extend(self._get_sales_movements(start_date, end_date, repository_id))
        
        # Purchases (incoming)
        movements.extend(self._get_purchase_movements(start_date, end_date, repository_id))
        
        # Sales Refunds (incoming)
        movements.extend(self._get_sales_refund_movements(start_date, end_date, repository_id))
        
        # Purchase Refunds (outgoing)
        # movements.extend(self._get_purchase_refund_movements(start_date, end_date, repository_id))
        
        # Repository Transfers
        # movements.extend(self._get_transfer_movements(start_date, end_date, repository_id))

        # refillable_item_refund (transformed)
        movements.extend(self._get_refillabel_item_refund(start_date, end_date, repository_id))

        # refillable_item_refilled (transformed)
        movements.extend(self._get_refillabel_item_refilled(start_date, end_date, repository_id))
        
        # ore_item_used (outgoing)
        movements.extend(self._get_ore_item_used(start_date, end_date, repository_id))

        # damaged_items (outgoing)
        movements.extend(self._get_damaged_items(start_date, end_date, repository_id))
        
        # Sort by date
        movements.sort(key=lambda x: x['date' or 'issue_date'])
        
        return movements
    
    def _get_sales_movements(self, start_date, end_date, repository_id) -> List[Dict]:
        """Get sales movements."""
        from invoices.sales.models import SalesInvoice, SalesInvoiceItem
                
        queryset = SalesInvoice.objects.filter(Q(s_invoice_items__item=self.item) if self.item else Q())
        queryset = self._apply_date_filter(queryset, start_date, end_date)

        # queryset = SalesInvoiceItem.objects.filter(
        #     Q(item=self.item) if self.item else Q()
        # ).values(
        #     'invoice__pk',
        #     'invoice__issue_date',
        #     'invoice__owner',
        #     'invoice__owner__name'
        # ).annotate(
        #     total_quantity=Sum('quantity')
        # )
        
        if repository_id:
            queryset = queryset.filter(s_invoice_items__repository_id=repository_id)
        
        movements = []
        for sale in queryset: #.select_related('repository'):
            movements.append({
                'date': sale.issue_date,
                'type': 'SALE',
                'reference_id': sale.id,
                # 'reference_number': getattr(sale, 'sale_number', f"SALE-{sale.id}"),
                # 'quantity': - sale['total_quantity'],  # Negative for outgoing
                # 'unit_price': sale.unit_price,
                # 'total_value': -sale.total_value,
                # 'repository': sale.repository.name if sale.repository else None,
                # 'repository_id': sale.repository_id,
                # 'notes': getattr(sale, 'notes', ''),
                'owner': sale.owner if sale.owner else None,
                'owner_name': sale.owner.name if sale.owner.name else None
            })

        return movements
    
    def _get_purchase_movements(self, start_date, end_date, repository_id) -> List[Dict]:
        """Get purchase movements."""
        from invoices.purchase.models import PurchaseInvoices, PurchaseInvoiceItems
        
        queryset = PurchaseInvoices.objects.filter(Q(p_invoice_items__item=self.item) if self.item else Q())
        queryset = self._apply_date_filter(queryset, start_date, end_date)

        # queryset = PurchaseInvoiceItems.objects.filter(
        #     Q(item=self.item) if self.item else Q()
        # ).values(
        #     'invoice__pk',
        #     'invoice__issue_date',
        #     'invoice__owner',
        #     'invoice__owner__name'
        # ).annotate(
        #     total_quantity=Sum('quantity')
        # )
        
        if repository_id:
            queryset = queryset.filter(p_invoice_items__repository_id=repository_id)
        
        movements = []
        for purchase in queryset: #.select_related('repository', 'supplier'):
            movements.append({
                'date': purchase.issue_date,
                'type': 'PURCHASE',
                'reference_id': purchase.id,
                # 'reference_number': getattr(purchase, 'purchase_number', f"PUR-{purchase.id}"),
                # 'quantity': purchase.quantity,  # Positive for incoming
                # 'unit_price': purchase.unit_price,
                # 'total_value': purchase.total_value,
                # 'repository': purchase.repository.name if purchase.repository else None,
                # 'repository_id': purchase.repository_id,
                # 'notes': getattr(purchase, 'notes', ''),
                'owner': purchase.owner if purchase.owner else None,
                'owner_name': purchase.owner.name if purchase.owner.name else None
            })
        
        return movements
    
    def _get_sales_refund_movements(self, start_date, end_date, repository_id) -> List[Dict]:
        """Get sales refund movements."""
        from invoices.sales.models import ReturnInvoice
        
        queryset = ReturnInvoice.objects.filter(Q(s_invoice_items__item=self.item) if self.item else Q())
        queryset = self._apply_date_filter(queryset, start_date, end_date)
        
        if repository_id:
            queryset = queryset.filter(s_invoice_items__repository_id=repository_id)
        
        movements = []
        for sales_refund in queryset: #.select_related('repository'):
            movements.append({
                'date': sales_refund.issue_date,
                'type': 'SALES_REFUND',
                'reference_id': sales_refund.id,
                # 'reference_number': getattr(refund, 'refund_number', f"SR-{refund.id}"),
                # 'quantity': refund.quantity,  # Positive for incoming
                # 'unit_price': refund.unit_price,
                # 'total_value': refund.total_value,
                # 'repository': refund.repository.name if refund.repository else None,
                # 'repository_id': refund.repository_id,
                # 'notes': getattr(refund, 'notes', ''),
                'owner': sales_refund.owner.id if hasattr(sales_refund.owner, 'id') else None,
                'owner_name': sales_refund.owner.name if hasattr(sales_refund.owner, 'name') else None,
                'original_sale_id': sales_refund.original_invoice
            })
        
        return movements
    
    def _get_refillabel_item_refund(self, start_date, end_date, repository_id) -> List[Dict]:
        """Get sales refund movements."""
        from refillable_items_system.models import RefundedRefillableItem
        
        queryset = RefundedRefillableItem.objects.filter(Q(item=self.item) if self.item else Q())
        queryset = self._apply_date_filter(queryset, start_date, end_date)
        
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        
        movements = []
        for refillable_refund in queryset: #.select_related('repository'):
            movements.append({
                'date': refillable_refund.date,
                'type': 'refillabe_item_refund',
                'reference_id': refillable_refund.id,
                # 'reference_number': getattr(refund, 'refund_number', f"SR-{refund.id}"),
                'quantity': refillable_refund.quantity,  # Positive for incoming
                # 'unit_price': refund.unit_price,
                # 'total_value': refund.total_value,
                # 'repository': refund.repository.name if refund.repository else None,
                # 'repository_id': refund.repository_id,
                # 'notes': getattr(refund, 'notes', ''),
                'owner': refillable_refund.owner.id if hasattr(refillable_refund.owner, 'id') else None,
                'owner_name': refillable_refund.owner.name if hasattr(refillable_refund.owner, 'name') else None
            })
        
        return movements
    
    def _get_refillabel_item_refilled(self, start_date, end_date, repository_id) -> List[Dict]:
        """Get sales refund movements."""
        from refillable_items_system.models import RefilledItem
        # has an issue you should solve
        queryset = RefilledItem.objects.filter(Q(refilled_item=self.item) if self.item else Q())
        queryset = self._apply_date_filter(queryset, start_date, end_date)
        
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        
        movements = []
        for refilled in queryset: #.select_related('repository'):
            movements.append({
                'date': refilled.date,
                'type': 'refillabe_item_refilled',
                'reference_id': refilled.id,
                # 'reference_number': getattr(refund, 'refund_number', f"SR-{refund.id}"),
                'quantity': refilled.refilled_quantity,  # Positive for incoming
                # 'unit_price': refund.unit_price,
                # 'total_value': refund.total_value,
                # 'repository': refund.repository.name if refund.repository else None,
                # 'repository_id': refund.repository_id,
                # 'notes': getattr(refund, 'notes', ''),
                'employee': refilled.employee,
            })
        
        return movements

    def _get_ore_item_used(self, start_date, end_date, repository_id) -> List[Dict]:
        """Get sales refund movements."""
        from refillable_items_system.models import RefilledItem

        queryset = RefilledItem.objects.filter(Q(used_item__item=self.item) if self.item else Q())
        queryset = self._apply_date_filter(queryset, start_date, end_date)
        
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        
        movements = []
        for used_item in queryset: #.select_related('repository'):
            movements.append({
                'date': used_item.date,
                'type': 'ore_item_used',
                'reference_id': used_item.id,
                # 'reference_number': getattr(refund, 'refund_number', f"SR-{refund.id}"),
                'quantity': used_item.used_quantity,  # Positive for incoming
                # 'unit_price': refund.unit_price,
                # 'total_value': refund.total_value,
                # 'repository': refund.repository.name if refund.repository else None,
                # 'repository_id': refund.repository_id,
                # 'notes': getattr(refund, 'notes', ''),
                'employee': used_item.employee,
            })
        
        return movements

    def _get_damaged_items(self, start_date, end_date, repository_id) -> List[Dict]:
        """Get sales refund movements."""
        from items.models import DamagedItems

        queryset = DamagedItems.objects.filter(Q(item=self.item) if self.item else Q())
        queryset = self._apply_date_filter(queryset, start_date, end_date)
        
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        
        movements = []
        for damaged_item in queryset: #.select_related('repository'):
            movements.append({
                'date': damaged_item.date,
                'type': 'damaged_item',
                'reference_id': damaged_item.id,
                # 'reference_number': getattr(refund, 'refund_number', f"SR-{refund.id}"),
                'quantity': damaged_item.quantity,  # Positive for incoming
                # 'unit_price': refund.unit_price,
                # 'total_value': refund.total_value,
                # 'repository': refund.repository.name if refund.repository else None,
                # 'repository_id': refund.repository_id,
                # 'notes': getattr(refund, 'notes', ''),
                'owner': damaged_item.owner.id if hasattr(damaged_item.owner, 'id') else None,
                'owner_name': damaged_item.owner.name if hasattr(damaged_item.owner, 'name') else None
            })
        
        return movements

    # def _get_purchase_refund_movements(self, start_date, end_date, repository_id) -> List[Dict]:
    #     """Get purchase refund movements."""
    #     from your_app.models import RefundPurchase
        
    #     queryset = RefundPurchase.objects.filter(item=self.item)
    #     queryset = self._apply_date_filter(queryset, start_date, end_date)
        
    #     if repository_id:
    #         queryset = queryset.filter(repository_id=repository_id)
        
    #     movements = []
    #     for refund in queryset.select_related('repository'):
    #         movements.append({
    #             'date': refund.date,
    #             'type': 'PURCHASE_REFUND',
    #             'reference_id': refund.id,
    #             'reference_number': getattr(refund, 'refund_number', f"PR-{refund.id}"),
    #             'quantity': -refund.quantity,  # Negative for outgoing
    #             'unit_price': refund.unit_price,
    #             'total_value': -refund.total_value,
    #             'repository': refund.repository.name if refund.repository else None,
    #             'repository_id': refund.repository_id,
    #             'notes': getattr(refund, 'notes', ''),
    #             'original_purchase_id': getattr(refund, 'original_purchase_id', None)
    #         })
        
    #     return movements
    
    # def _get_transfer_movements(self, start_date, end_date, repository_id) -> List[Dict]:
    #     """Get repository transfer movements."""
    #     from your_app.models import RepositoryTransfer
        
    #     # Get transfers where this item is involved
    #     queryset = RepositoryTransfer.objects.filter(item=self.item)
    #     queryset = self._apply_date_filter(queryset, start_date, end_date)
        
    #     movements = []
        
    #     for transfer in queryset.select_related('from_repository', 'to_repository'):
    #         # If filtering by repository, include transfers from or to that repository
    #         if repository_id and repository_id not in [transfer.from_repository_id, transfer.to_repository_id]:
    #             continue
            
    #         # Outgoing from source repository
    #         if not repository_id or repository_id == transfer.from_repository_id:
    #             movements.append({
    #                 'date': transfer.date,
    #                 'type': 'TRANSFER_OUT',
    #                 'reference_id': transfer.id,
    #                 'reference_number': getattr(transfer, 'transfer_number', f"TR-{transfer.id}"),
    #                 'quantity': -transfer.quantity,  # Negative for outgoing
    #                 'unit_price': getattr(transfer, 'unit_price', Decimal('0')),
    #                 'total_value': -transfer.quantity * getattr(transfer, 'unit_price', Decimal('0')),
    #                 'repository': transfer.from_repository.name,
    #                 'repository_id': transfer.from_repository_id,
    #                 'notes': f"Transfer to {transfer.to_repository.name}",
    #                 'destination_repository': transfer.to_repository.name,
    #                 'destination_repository_id': transfer.to_repository_id
    #             })
            
    #         # Incoming to destination repository
    #         if not repository_id or repository_id == transfer.to_repository_id:
    #             movements.append({
    #                 'date': transfer.date,
    #                 'type': 'TRANSFER_IN',
    #                 'reference_id': transfer.id,
    #                 'reference_number': getattr(transfer, 'transfer_number', f"TR-{transfer.id}"),
    #                 'quantity': transfer.quantity,  # Positive for incoming
    #                 'unit_price': getattr(transfer, 'unit_price', Decimal('0')),
    #                 'total_value': transfer.quantity * getattr(transfer, 'unit_price', Decimal('0')),
    #                 'repository': transfer.to_repository.name,
    #                 'repository_id': transfer.to_repository_id,
    #                 'notes': f"Transfer from {transfer.from_repository.name}",
    #                 'source_repository': transfer.from_repository.name,
    #                 'source_repository_id': transfer.from_repository_id
    #             })
        
    #     return movements
    
    def _apply_date_filter(self, queryset, start_date, end_date):
        """Apply date filter to queryset."""
        if queryset.exists():
            first_obj = queryset.first()
            if hasattr(first_obj, 'date'):
                field = 'date'
            else:
                field = 'issue_date'
        else:
            return queryset
        if start_date:
            queryset = queryset.filter(**({f'{field}__gte': start_date}))
        if end_date:
            queryset = queryset.filter(**({f'{field}__lte': end_date}))
        return queryset
    
    def _calculate_totals(self, movements: List[Dict]) -> Dict:
        """Calculate movement totals."""
        totals = {
            'total_in': Decimal('0'),
            'total_out': Decimal('0'),
            'net_movement': Decimal('0'),
            'sales_quantity': Decimal('0'),
            'purchase_quantity': Decimal('0'),
            'sales_refund_quantity': Decimal('0'),
            'purchase_refund_quantity': Decimal('0'),
            'transfer_in_quantity': Decimal('0'),
            'transfer_out_quantity': Decimal('0'),
        }
        
        for movement in movements:
            quantity = Decimal(str(movement['quantity']))
            
            if quantity > 0:
                totals['total_in'] += quantity
            else:
                totals['total_out'] += abs(quantity)
            
            # Track by movement type
            movement_type = movement['type']
            if movement_type == 'SALE':
                totals['sales_quantity'] += abs(quantity)
            elif movement_type == 'PURCHASE':
                totals['purchase_quantity'] += quantity
            elif movement_type == 'SALES_REFUND':
                totals['sales_refund_quantity'] += quantity
            elif movement_type == 'PURCHASE_REFUND':
                totals['purchase_refund_quantity'] += abs(quantity)
            elif movement_type == 'TRANSFER_IN':
                totals['transfer_in_quantity'] += quantity
            elif movement_type == 'TRANSFER_OUT':
                totals['transfer_out_quantity'] += abs(quantity)
        
        totals['net_movement'] = totals['total_in'] - totals['total_out']
        
        return totals
    
    def _get_movement_breakdown(self, movements: List[Dict]) -> Dict:
        """Get breakdown of movements by type and repository."""
        breakdown = {
            'by_type': {},
            'by_repository': {},
            'by_month': {}
        }
        
        for movement in movements:
            movement_type = movement['type']
            repository_name = movement['repository'] or 'Unknown'
            month_key = movement['date'].strftime('%Y-%m')
            quantity = Decimal(str(movement['quantity']))
            
            # By type
            if movement_type not in breakdown['by_type']:
                breakdown['by_type'][movement_type] = {'quantity': Decimal('0'), 'count': 0}
            breakdown['by_type'][movement_type]['quantity'] += quantity
            breakdown['by_type'][movement_type]['count'] += 1
            
            # By repository
            if repository_name not in breakdown['by_repository']:
                breakdown['by_repository'][repository_name] = {'quantity': Decimal('0'), 'count': 0}
            breakdown['by_repository'][repository_name]['quantity'] += quantity
            breakdown['by_repository'][repository_name]['count'] += 1
            
            # By month
            if month_key not in breakdown['by_month']:
                breakdown['by_month'][month_key] = {'quantity': Decimal('0'), 'count': 0}
            breakdown['by_month'][month_key]['quantity'] += quantity
            breakdown['by_month'][month_key]['count'] += 1
        
        return breakdown
