# Refillable Items Price Calculation System

## Overview

This system calculates the cost price of refilled items based on the ore/raw materials used and their historical prices at the time of the refilling transaction.

## How It Works

### Price Calculation Formula

```
Refilled Item Cost Per Unit = (Used Quantity / Refilled Quantity) × Ore Item Price at Transaction Date
```

### Example

If on May 1st, 2025:
- Ore Item (Raw Material) price: 100 units
- Used Quantity: 50 units
- Refilled Quantity: 100 units

Then:
- **Cost Per Unit of Refilled Item** = (50 / 100) × 100 = **50 units**
- **Total Cost** = 50 × 100 = **5,000 units**

## Components

### 1. **RefillableItemPriceCalculator Service** 
Location: `refillable_items_system/services/analysis_refillable_items_prices.py`

#### Key Methods:

- **`get_item_price_at_date(item, transaction_date)`**
  - Retrieves the historical price of an item at a specific date
  - Looks up `ItemPriceLog` for prices on or before the transaction date
  - Falls back to `item.price1` if no historical log exists

- **`calculate_refilled_item_price(refilled_item)`**
  - Calculates the cost price for a single `RefilledItem` instance
  - Applies the formula: (used_quantity / refilled_quantity) × ore_price
  - Returns the price rounded to 2 decimal places

- **`calculate_batch_refilled_prices(refilled_items_queryset)`**
  - Efficiently calculates prices for multiple `RefilledItem` instances
  - Returns a list of dictionaries with detailed price information
  - Includes error handling for invalid data

### 2. **RefilledItem Model Extensions**
Location: `refillable_items_system/models.py`

Added methods to the `RefilledItem` model:

- **`get_refilled_item_price()`**
  - Calculates and returns the cost price per unit
  - Used by serializer and views

- **`get_ore_item_price_at_date()`**
  - Returns the ore item's price at the transaction date
  - Useful for breakdown analysis

### 3. **Serializer Integration**
Location: `refillable_items_system/serializers.py`

Updated `RefilledItemSerializer` to include calculated fields:

- **`refilled_item_calculated_price`** (read-only)
  - Includes the calculated cost per unit in API responses

- **`ore_item_price_at_date`** (read-only)
  - Includes the ore item's price at transaction date for reference

## Usage

### In Django Shell

```python
from refillable_items_system.models import RefilledItem
from refillable_items_system.services.analysis_refillable_items_prices import RefillableItemPriceCalculator

# Get a refilled item
refilled_item = RefilledItem.objects.first()

# Method 1: Using model methods
price = refilled_item.get_refilled_item_price()
ore_price = refilled_item.get_ore_item_price_at_date()

print(f"Calculated Price: {price}")
print(f"Ore Price at Date: {ore_price}")

# Method 2: Using calculator directly
price = RefillableItemPriceCalculator.calculate_refilled_item_price(refilled_item)

# Method 3: Batch calculation
refilled_items = RefilledItem.objects.filter(date__gte='2025-01-01')
results = RefillableItemPriceCalculator.calculate_batch_refilled_prices(refilled_items)
```

### In API Endpoints

GET request to list refilled items:

```bash
curl http://localhost:8000/api/refilled-items/
```

Response includes:

```json
{
  "id": 1,
  "refilled_item": 1,
  "refilled_item_name": "Cylinder 20L",
  "used_item": 5,
  "used_item_name": "Ore Material A",
  "refilled_quantity": 100,
  "used_quantity": 50,
  "date": "2025-05-01",
  "refilled_item_calculated_price": "50.00",
  "ore_item_price_at_date": "100.00",
  ...
}
```

### Management Command

Generate a price report:

```bash
# Report for last 30 days (default)
python manage.py refilled_items_price_report

# Specify date range
python manage.py refilled_items_price_report --from-date 2025-04-01 --to-date 2025-05-01

# Output as CSV
python manage.py refilled_items_price_report --output csv --csv-file prices_report.csv

# Output as JSON
python manage.py refilled_items_price_report --output json

# Output as formatted table
python manage.py refilled_items_price_report --output table
```

## Price History Tracking

The system uses `ItemPriceLog` model to track historical prices:

```python
from items.models import ItemPriceLog

# When an item's price changes, a log entry is created:
ItemPriceLog.objects.create(
    item=ore_item,
    price=new_price,
    date=transaction_date,
    by=user  # Who made the change
)
```

### How Price Lookup Works

1. Query `ItemPriceLog` for the specified item and date
2. Find the most recent price on or before the transaction date
3. If no log exists, use the item's current `price1` field

Example:
- If refilling happened on 2025-05-15 and ore item price history is:
  - 2025-05-10: 100
  - 2025-05-01: 95
  - 2024-04-15: 90
- The system will use **100** (most recent before 2025-05-15)

## Data Model Relationships

```
RefilledItem
├── refilled_item → Items (the finished product)
├── used_item → OreItem → Items (the raw material)
├── employee → Employee (who performed the refilling)
├── repository → Repositories (where it was stored)
└── date (transaction date)

OreItem
└── item → Items

ItemPriceLog
├── item → Items
└── date (price effective date)
```

## Example Scenarios

### Scenario 1: Simple Refilling
- **Ore Item**: Gas Cylinder (Empty) - Price: $50
- **Refilled Item**: Gas Cylinder (Full)
- **Used Quantity**: 1 cylinder
- **Refilled Quantity**: 1 cylinder
- **Calculated Price**: (1/1) × $50 = **$50 per unit**

### Scenario 2: Bulk Refilling
- **Ore Item**: Liquid (Bulk) - Price: $100/liter
- **Refilled Item**: Small Bottles
- **Used Quantity**: 10 liters
- **Refilled Quantity**: 20 bottles
- **Calculated Price**: (10/20) × $100 = **$50 per bottle**

### Scenario 3: Raw Material Reduction
- **Ore Item**: Raw Ore - Price: $200/kg
- **Refilled Item**: Refined Product
- **Used Quantity**: 5 kg raw ore
- **Refilled Quantity**: 3 kg refined product
- **Calculated Price**: (5/3) × $200 = **$333.33 per kg refined**

## Error Handling

The system handles various error cases:

1. **Zero refilled_quantity**: Prevents division by zero, raises `ValueError`
2. **Missing price history**: Falls back to current `price1`
3. **Invalid refilled items**: Returns error in batch calculation results
4. **Missing OreItem**: Catches database errors gracefully

## Performance Considerations

### Single Item Calculation
- ~2-3 database queries per item
- O(1) time complexity

### Batch Calculation
- Uses select_related for optimal query performance
- Reduces N+1 query problems
- Scales well for 100+ items

### Optimization Tips

```python
# Good: Uses select_related to minimize queries
refilled_items = RefilledItem.objects.select_related(
    'refilled_item',
    'used_item',
    'used_item__item'
).all()

results = RefillableItemPriceCalculator.calculate_batch_refilled_prices(
    refilled_items
)
```

## Integration with Other Systems

### Invoice System
Can be used to set cost prices in purchase invoices:

```python
from invoices.purchase.models import PurchaseInvoiceItem

price = refilled_item.get_refilled_item_price()
PurchaseInvoiceItem.objects.create(
    item=refilled_item.refilled_item,
    unit_price=price,
    ...
)
```

### Warehouse Reports
Included in inventory valuation reports:

```python
from reports.warehouse.services.item_movement_service import ItemMovementService

# Price information can be queried by date range
```

## Testing

Example test cases:

```python
from django.test import TestCase
from refillable_items_system.models import RefilledItem, OreItem
from items.models import Items, ItemPriceLog

class RefillableItemPriceTestCase(TestCase):
    def setUp(self):
        # Create test items and price logs
        self.ore_item = OreItem.objects.create(item=Items.objects.create(name='Ore'))
        ItemPriceLog.objects.create(item=self.ore_item.item, price=100, date='2025-05-01')
        
    def test_price_calculation(self):
        refilled = RefilledItem.objects.create(
            refilled_item=Items.objects.create(name='Refilled'),
            used_item=self.ore_item,
            used_quantity=50,
            refilled_quantity=100,
            date='2025-05-01',
            ...
        )
        price = refilled.get_refilled_item_price()
        self.assertEqual(price, 50.00)
```

## Notes

- All prices are stored and calculated with 2 decimal places precision
- The system uses historical price logs for accuracy in cost calculations
- Prices are recalculated on each access (not cached) to ensure accuracy
- The management command generates reports on demand without modifying data

## See Also

- [Items Price Logging System](../items/models.py)
- [Refillable Items Models](./models.py)
- [API Documentation](../backend/endpoints.md)
