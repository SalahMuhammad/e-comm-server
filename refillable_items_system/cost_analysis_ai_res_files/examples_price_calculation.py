"""
Examples of how to use the Refillable Items Price Calculator

This module demonstrates how to calculate prices for refilled items
based on the ore item used and the transaction date.
"""

from refillable_items_system.models import RefilledItem
from refillable_items_system.services.analysis_item_unit_cost import RefillableItemPriceCalculator


# Example 1: Calculate price for a single RefilledItem
def example_single_refilled_item():
    """Calculate the price of a single refilled item"""
    refilled_item = RefilledItem.objects.first()
    
    if refilled_item:
        # Get the calculated price using the model method
        price = refilled_item.get_refilled_item_price()
        ore_price = refilled_item.get_ore_item_price_at_date()
        
        print(f"Refilled Item: {refilled_item.refilled_item.name}")
        print(f"Ore Item: {refilled_item.used_item.item.name}")
        print(f"Ore Price at {refilled_item.date}: {ore_price}")
        print(f"Used Quantity: {refilled_item.used_quantity}")
        print(f"Refilled Quantity: {refilled_item.refilled_quantity}")
        print(f"Calculated Price per Unit: {price}")
        print(f"Total Cost: {price * refilled_item.refilled_quantity}")


# Example 2: Calculate prices for all refilled items in a date range
def example_batch_calculation():
    """Calculate prices for multiple refilled items"""
    from django.utils import timezone
    from datetime import timedelta
    
    # Get refilled items from last 30 days
    start_date = timezone.now().date() - timedelta(days=30)
    refilled_items = RefilledItem.objects.filter(date__gte=start_date)
    
    results = RefillableItemPriceCalculator.calculate_batch_refilled_prices(
        refilled_items
    )
    
    print("Batch Price Calculation Results:")
    for result in results:
        if 'error' not in result:
            print(f"\nID: {result['id']}")
            print(f"  Refilled Item: {result['refilled_item_name']}")
            print(f"  Ore Item: {result['ore_item_name']}")
            print(f"  Ore Price at Date: {result['ore_price_at_date']}")
            print(f"  Used: {result['used_quantity']} / Refilled: {result['refilled_quantity']}")
            print(f"  Calculated Price: {result['calculated_price']}")
        else:
            print(f"\nID: {result['id']} - Error: {result['error']}")


# Example 3: Using the calculator directly
def example_direct_calculator_usage():
    """Use the calculator class directly"""
    from refillable_items_system.models import OreItem
    from items.models import Items
    from datetime import date
    
    # Get an ore item
    ore_item = OreItem.objects.first()
    
    if ore_item:
        # Get the price of the ore item at a specific date
        transaction_date = date(2025, 5, 1)
        price = RefillableItemPriceCalculator.get_item_price_at_date(
            ore_item.item,
            transaction_date
        )
        print(f"Price of {ore_item.item.name} on {transaction_date}: {price}")


# Example 4: Getting refilled items with prices in API response
def example_api_serialization():
    """
    Shows how the calculated prices appear in API responses
    when using RefilledItemSerializer
    """
    from refillable_items_system.serializers import RefilledItemSerializer
    
    refilled_item = RefilledItem.objects.first()
    
    if refilled_item:
        serializer = RefilledItemSerializer(refilled_item)
        response_data = serializer.data
        
        # The response will include:
        # - refilled_item_calculated_price: calculated cost per unit
        # - ore_item_price_at_date: the ore price at transaction date
        print("API Response includes:")
        print(f"  refilled_item_calculated_price: {response_data.get('refilled_item_calculated_price')}")
        print(f"  ore_item_price_at_date: {response_data.get('ore_item_price_at_date')}")


# Example 5: Filtering refilled items by price range
def example_filter_by_price():
    """Filter refilled items based on calculated price"""
    refilled_items = RefilledItem.objects.all()[:10]  # Get first 10
    
    expensive_items = []
    for item in refilled_items:
        price = item.get_refilled_item_price()
        if price > 100:  # Example threshold
            expensive_items.append({
                'refilled_item': item.refilled_item.name,
                'price': price,
                'date': item.date
            })
    
    print("Expensive Refilled Items (price > 100):")
    for item in expensive_items:
        print(f"  {item['refilled_item']}: {item['price']} on {item['date']}")


if __name__ == "__main__":
    # Uncomment to run examples
    # example_single_refilled_item()
    # example_batch_calculation()
    # example_direct_calculator_usage()
    # example_api_serialization()
    # example_filter_by_price()
    pass
