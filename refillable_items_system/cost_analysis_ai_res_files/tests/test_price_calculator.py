"""
Unit tests for Refillable Items Price Calculator

Run with: python manage.py test refillable_items_system.tests.test_price_calculator
"""

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from refillable_items_system.models import (
    RefilledItem, 
    OreItem, 
    ItemTransformer,
    RefillableItemsInitialStockClientHas
)
from refillable_items_system.services.analysis_item_unit_cost import (
    RefillableItemPriceCalculator
)
from items.models import Items, ItemPriceLog, Types
from employees.models import Employee
from repositories.models import Repositories
from invoices.buyer_supplier_party.models import Party
from common.models import User


class RefillableItemPriceCalculatorTestCase(TestCase):
    """Test cases for price calculation"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods"""
        # Create user
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

        # Create repository
        cls.repository = Repositories.objects.create(
            name='Test Repository',
            by=cls.user
        )

        # Create employee
        cls.employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            by=cls.user
        )

        # Create item type
        cls.item_type = Types.objects.create(
            name='Refillable Items',
            by=cls.user
        )

        # Create ore item
        cls.ore_item_obj = Items.objects.create(
            name='Raw Ore',
            type=cls.item_type,
            price1=Decimal('100.00'),
            is_refillable=False,
            by=cls.user
        )

        cls.ore_item = OreItem.objects.create(
            item=cls.ore_item_obj,
            by=cls.user
        )

        # Create refilled item
        cls.refilled_item_obj = Items.objects.create(
            name='Refined Product',
            type=cls.item_type,
            price1=Decimal('50.00'),
            is_refillable=True,
            by=cls.user
        )

        # Create ItemTransformer to mark items as refillable
        ItemTransformer.objects.create(
            item=cls.ore_item_obj,
            transform=cls.refilled_item_obj,
            by=cls.user
        )

        # Create price logs for ore item
        ItemPriceLog.objects.create(
            item=cls.ore_item_obj,
            price=Decimal('100.00'),
            date=date(2025, 5, 1),
            by=cls.user
        )

        ItemPriceLog.objects.create(
            item=cls.ore_item_obj,
            price=Decimal('120.00'),
            date=date(2025, 5, 15),
            by=cls.user
        )

    def test_get_item_price_at_date_with_price_log(self):
        """Test getting price from ItemPriceLog"""
        price = RefillableItemPriceCalculator.get_item_price_at_date(
            self.ore_item_obj,
            date(2025, 5, 10)
        )
        # Should return the most recent price on or before 2025-05-10
        self.assertEqual(price, Decimal('100.00'))

    def test_get_item_price_at_date_before_any_logs(self):
        """Test getting price when transaction is before any logs"""
        price = RefillableItemPriceCalculator.get_item_price_at_date(
            self.ore_item_obj,
            date(2025, 4, 1)
        )
        # Should return price1 when no logs exist before date
        self.assertEqual(price, Decimal('100.00'))

    def test_get_item_price_at_date_after_latest_log(self):
        """Test getting price when transaction is after latest log"""
        price = RefillableItemPriceCalculator.get_item_price_at_date(
            self.ore_item_obj,
            date(2025, 5, 20)
        )
        # Should return the most recent log (2025-05-15)
        self.assertEqual(price, Decimal('120.00'))

    def test_calculate_refilled_item_price_basic(self):
        """Test basic price calculation"""
        refilled_item = RefilledItem.objects.create(
            refilled_item=self.refilled_item_obj,
            used_item=self.ore_item,
            employee=self.employee,
            repository=self.repository,
            refilled_quantity=Decimal('100.00'),
            used_quantity=Decimal('50.00'),
            date=date(2025, 5, 5),
            by=self.user
        )

        price = RefillableItemPriceCalculator.calculate_refilled_item_price(
            refilled_item
        )

        # Expected: (50 / 100) * 100 = 50
        expected = Decimal('50.00')
        self.assertEqual(price, expected)

    def test_calculate_refilled_item_price_with_higher_ore_price(self):
        """Test calculation with higher ore price"""
        refilled_item = RefilledItem.objects.create(
            refilled_item=self.refilled_item_obj,
            used_item=self.ore_item,
            employee=self.employee,
            repository=self.repository,
            refilled_quantity=Decimal('100.00'),
            used_quantity=Decimal('50.00'),
            date=date(2025, 5, 20),  # Uses price of 120
            by=self.user
        )

        price = RefillableItemPriceCalculator.calculate_refilled_item_price(
            refilled_item
        )

        # Expected: (50 / 100) * 120 = 60
        expected = Decimal('60.00')
        self.assertEqual(price, expected)

    def test_calculate_refilled_item_price_more_quantity(self):
        """Test calculation when more units are refilled"""
        refilled_item = RefilledItem.objects.create(
            refilled_item=self.refilled_item_obj,
            used_item=self.ore_item,
            employee=self.employee,
            repository=self.repository,
            refilled_quantity=Decimal('200.00'),
            used_quantity=Decimal('50.00'),
            date=date(2025, 5, 5),
            by=self.user
        )

        price = RefillableItemPriceCalculator.calculate_refilled_item_price(
            refilled_item
        )

        # Expected: (50 / 200) * 100 = 25
        expected = Decimal('25.00')
        self.assertEqual(price, expected)

    def test_calculate_refilled_item_price_zero_refilled_quantity_error(self):
        """Test that zero refilled quantity raises error"""
        refilled_item = RefilledItem.objects.create(
            refilled_item=self.refilled_item_obj,
            used_item=self.ore_item,
            employee=self.employee,
            repository=self.repository,
            refilled_quantity=Decimal('0.00'),  # Invalid
            used_quantity=Decimal('50.00'),
            date=date(2025, 5, 5),
            by=self.user
        )

        with self.assertRaises(ValueError):
            RefillableItemPriceCalculator.calculate_refilled_item_price(
                refilled_item
            )

    def test_batch_calculation(self):
        """Test batch price calculation"""
        # Create multiple refilled items
        items = []
        for i in range(3):
            refilled = RefilledItem.objects.create(
                refilled_item=self.refilled_item_obj,
                used_item=self.ore_item,
                employee=self.employee,
                repository=self.repository,
                refilled_quantity=Decimal('100.00'),
                used_quantity=Decimal('50.00'),
                date=date(2025, 5, 5),
                by=self.user
            )
            items.append(refilled)

        queryset = RefilledItem.objects.filter(id__in=[item.id for item in items])
        results = RefillableItemPriceCalculator.calculate_batch_refilled_prices(
            queryset
        )

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result['calculated_price'], Decimal('50.00'))
            self.assertNotIn('error', result)

    def test_model_method_get_refilled_item_price(self):
        """Test the model method for getting refilled item price"""
        refilled_item = RefilledItem.objects.create(
            refilled_item=self.refilled_item_obj,
            used_item=self.ore_item,
            employee=self.employee,
            repository=self.repository,
            refilled_quantity=Decimal('100.00'),
            used_quantity=Decimal('50.00'),
            date=date(2025, 5, 5),
            by=self.user
        )

        price = refilled_item.get_refilled_item_price()
        self.assertEqual(price, Decimal('50.00'))

    def test_model_method_get_ore_item_price_at_date(self):
        """Test the model method for getting ore item price at date"""
        refilled_item = RefilledItem.objects.create(
            refilled_item=self.refilled_item_obj,
            used_item=self.ore_item,
            employee=self.employee,
            repository=self.repository,
            refilled_quantity=Decimal('100.00'),
            used_quantity=Decimal('50.00'),
            date=date(2025, 5, 5),
            by=self.user
        )

        ore_price = refilled_item.get_ore_item_price_at_date()
        self.assertEqual(ore_price, Decimal('100.00'))

    def test_decimal_precision(self):
        """Test that calculations maintain 2 decimal place precision"""
        refilled_item = RefilledItem.objects.create(
            refilled_item=self.refilled_item_obj,
            used_item=self.ore_item,
            employee=self.employee,
            repository=self.repository,
            refilled_quantity=Decimal('3.00'),
            used_quantity=Decimal('5.00'),
            date=date(2025, 5, 5),
            by=self.user
        )

        price = RefillableItemPriceCalculator.calculate_refilled_item_price(
            refilled_item
        )

        # Expected: (5 / 3) * 100 = 166.6666... truncated to 166.67
        expected = Decimal('166.67')
        self.assertEqual(price, expected)


class RefillableItemSerializerTestCase(TestCase):
    """Test cases for serializer integration"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        from refillable_items_system.serializers import RefilledItemSerializer

        cls.serializer_class = RefilledItemSerializer

        # Create minimal test data (reuse setup method from above)
        cls.user = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            email='test2@example.com'
        )

        cls.repository = Repositories.objects.create(
            name='Test Repository 2',
            by=cls.user
        )

        cls.employee = Employee.objects.create(
            first_name='Jane',
            last_name='Smith',
            phone='0987654321',
            by=cls.user
        )

        cls.item_type = Types.objects.create(
            name='Test Type',
            by=cls.user
        )

        cls.ore_item_obj = Items.objects.create(
            name='Test Ore',
            type=cls.item_type,
            price1=Decimal('100.00'),
            by=cls.user
        )

        cls.ore_item = OreItem.objects.create(
            item=cls.ore_item_obj,
            by=cls.user
        )

        cls.refilled_item_obj = Items.objects.create(
            name='Test Refilled',
            type=cls.item_type,
            price1=Decimal('50.00'),
            by=cls.user
        )

        ItemTransformer.objects.create(
            item=cls.ore_item_obj,
            transform=cls.refilled_item_obj,
            by=cls.user
        )

        ItemPriceLog.objects.create(
            item=cls.ore_item_obj,
            price=Decimal('100.00'),
            date=date(2025, 5, 1),
            by=cls.user
        )

    def test_serializer_includes_calculated_price(self):
        """Test that serializer includes calculated prices"""
        refilled_item = RefilledItem.objects.create(
            refilled_item=self.refilled_item_obj,
            used_item=self.ore_item,
            employee=self.employee,
            repository=self.repository,
            refilled_quantity=Decimal('100.00'),
            used_quantity=Decimal('50.00'),
            date=date(2025, 5, 5),
            by=self.user
        )

        serializer = self.serializer_class(refilled_item)
        data = serializer.data

        self.assertIn('refilled_item_calculated_price', data)
        self.assertIn('ore_item_price_at_date', data)
        self.assertEqual(data['refilled_item_calculated_price'], '50.00')
        self.assertEqual(data['ore_item_price_at_date'], '100.00')
