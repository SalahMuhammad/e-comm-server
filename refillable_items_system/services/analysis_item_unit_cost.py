from refillable_items_system.models import (
    OreItem, 
    ItemTransformer, 
    RefilledItem
)
from items.models import ItemPriceLog
from decimal import Decimal
from django.db.models import Q


class RefillableItemPriceCalculator:
    """
    Calculates the refilled item's price based on:
    1. OreItem's price at the transaction date
    2. The ratio of used_quantity to refilled_quantity
    
    Formula: (used_quantity / refilled_quantity) * ore_item_price_at_date
    """

    @staticmethod
    def get_item_price_at_date(item, transaction_date):
        """
        Get the price of an item at a specific date from ItemPriceLog.
        Returns the most recent price on or before the transaction date.
        
        Args:
            item: Items instance
            transaction_date: Date to get the price for
            
        Returns:
            Decimal: The price of the item at that date, or item.price1 if no log found
        """
        price_log = ItemPriceLog.objects.filter(
            item=item,
            date__lte=transaction_date
        ).order_by('-date').first()

        if price_log:
            return price_log.price

        # If no historical price found, use current price1
        return item.price1

    @staticmethod
    def calculate_refilled_item_price(refilled_item: RefilledItem):
        """
        Calculate the cost price of a refilled item based on the ore used.
        
        Args:
            refilled_item: RefilledItem instance
            
        Returns:
            Decimal: The calculated price per unit of refilled item
        """
        if refilled_item.refilled_quantity == 0:
            raise ValueError("refilled_quantity cannot be zero")
        
        # Get the OreItem's item price at the transaction date
        ore_item_price = RefillableItemPriceCalculator.get_item_price_at_date(
            refilled_item.used_item.item,
            refilled_item.date
        )
        
        # Calculate the cost: (used_quantity / refilled_quantity) * ore_price
        cost_per_unit = (
            refilled_item.used_quantity / refilled_item.refilled_quantity
        ) * ore_item_price
        
        return cost_per_unit.quantize(Decimal('0.01'))

    @staticmethod
    def calculate_batch_refilled_prices(refilled_items_queryset):
        """
        Calculate prices for multiple refilled items efficiently.
        
        Args:
            refilled_items_queryset: QuerySet of RefilledItem instances
            
        Returns:
            List[Dict]: List of dicts with refilled_item id and calculated price
        """
        results = []
        for refilled_item in refilled_items_queryset:
            try:
                price = RefillableItemPriceCalculator.calculate_refilled_item_price(
                    refilled_item
                )


                # print(refilled_item.refilled_item.item_price_log)


                results.append({
                    'id': refilled_item.id,
                    'refilled_item_id': refilled_item.refilled_item.id,
                    'refilled_item_name': refilled_item.refilled_item.name,
                    'ore_item_name': refilled_item.used_item.item.name,
                    'used_quantity': refilled_item.used_quantity,
                    'refilled_quantity': refilled_item.refilled_quantity,
                    'date': refilled_item.date,
                    'calculated_price': price,
                    # 'ore_price_at_date': RefillableItemPriceCalculator.get_item_price_at_date(
                    #     refilled_item.used_item.item,
                    #     refilled_item.date
                    # )
                    'note': refilled_item.notes
                })
            except Exception as e:
                results.append({
                    'id': refilled_item.id,
                    'error': str(e)
                })
        
        return results


class CanBasePrice:
    """
    Legacy class for calculating can/container base cost.
    Uses RefillableItemPriceCalculator for price lookups.
    """

    def __init__(self, can: ItemTransformer):
        self.can = can
        self.calculator = RefillableItemPriceCalculator()

    def calculate_can_cost(self, refilled_item: RefilledItem) -> Decimal:
        """
        Calculate the cost of a can based on refilled item transaction.
        
        Args:
            refilled_item: RefilledItem instance
            
        Returns:
            Decimal: The calculated cost
        """
        return self.calculator.calculate_refilled_item_price(refilled_item)
