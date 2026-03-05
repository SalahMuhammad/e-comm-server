"""
Management command to generate a report of refilled items with calculated prices.

Usage:
  python manage.py refilled_items_price_report [--from-date YYYY-MM-DD] [--to-date YYYY-MM-DD] [--output csv]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from refillable_items_system.models import RefilledItem
from refillable_items_system.services.analysis_item_unit_cost import RefillableItemPriceCalculator
import csv


class Command(BaseCommand):
    help = 'Generate a report of refilled items with calculated prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-date',
            type=str,
            help='Start date (YYYY-MM-DD)',
            required=False
        )
        parser.add_argument(
            '--to-date',
            type=str,
            help='End date (YYYY-MM-DD)',
            required=False
        )
        parser.add_argument(
            '--output',
            type=str,
            choices=['csv', 'json', 'table'],
            default='table',
            help='Output format'
        )
        parser.add_argument(
            '--csv-file',
            type=str,
            help='CSV file path (default: refilled_items_prices.csv)',
            required=False
        )

    def handle(self, *args, **options):
        # Parse dates
        from_date = None
        to_date = None

        if options['from_date']:
            try:
                from_date = datetime.strptime(options['from_date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid from-date format. Use YYYY-MM-DD'))
                return

        if options['to_date']:
            try:
                to_date = datetime.strptime(options['to_date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid to-date format. Use YYYY-MM-DD'))
                return

        # Default to last 30 days if no dates provided
        if not from_date and not to_date:
            to_date = timezone.now().date()
            from_date = to_date - timedelta(days=30)
            self.stdout.write(
                f"No date range specified. Using last 30 days: {from_date} to {to_date}"
            )

        # Get refilled items
        queryset = RefilledItem.objects.select_related(
            'refilled_item',
            'used_item',
            'used_item__item',
            'employee',
            'repository'
        )

        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        refilled_items = queryset.order_by('-date')

        if not refilled_items.exists():
            self.stdout.write(self.style.WARNING('No refilled items found for the specified date range.'))
            return

        # Calculate prices
        results = RefillableItemPriceCalculator.calculate_batch_refilled_prices(refilled_items)

        # Output results
        output_format = options['output']

        if output_format == 'csv':
            self._output_csv(results, options.get('csv_file', 'refilled_items_prices.csv'))
        elif output_format == 'json':
            self._output_json(results)
        else:
            self._output_table(results)

    def _output_table(self, results):
        """Output results as a formatted table"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*150))
        self.stdout.write(self.style.SUCCESS('REFILLED ITEMS PRICE REPORT'))
        self.stdout.write(self.style.SUCCESS('='*150))

        for result in results:
            if 'error' not in result:
                self.stdout.write(f"\nID: {result['id']}")
                self.stdout.write(f"  Refilled Item: {result['refilled_item_name']}")
                self.stdout.write(f"  Ore Item: {result['ore_item_name']}")
                self.stdout.write(f"  Date: {result['date']}")
                self.stdout.write(f"  Ore Price at Date: {result['ore_price_at_date']:,.2f}")
                self.stdout.write(f"  Used Quantity: {result['used_quantity']} units")
                self.stdout.write(f"  Refilled Quantity: {result['refilled_quantity']} units")
                self.stdout.write(f"  Calculated Price per Unit: {result['calculated_price']:,.2f}")
                self.stdout.write(f"  Total Cost: {result['calculated_price'] * result['refilled_quantity']:,.2f}")
            else:
                self.stdout.write(self.style.ERROR(f"\nID: {result['id']} - Error: {result['error']}"))

        self.stdout.write(self.style.SUCCESS('\n' + '='*150 + '\n'))

    def _output_csv(self, results, filename):
        """Output results as CSV"""
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'id', 'refilled_item_name', 'ore_item_name', 'date',
                'ore_price_at_date', 'used_quantity', 'refilled_quantity',
                'calculated_price', 'total_cost'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                if 'error' not in result:
                    writer.writerow({
                        'id': result['id'],
                        'refilled_item_name': result['refilled_item_name'],
                        'ore_item_name': result['ore_item_name'],
                        'date': result['date'],
                        'ore_price_at_date': result['ore_price_at_date'],
                        'used_quantity': result['used_quantity'],
                        'refilled_quantity': result['refilled_quantity'],
                        'calculated_price': result['calculated_price'],
                        'total_cost': result['calculated_price'] * result['refilled_quantity']
                    })

        self.stdout.write(self.style.SUCCESS(f'CSV report saved to: {filename}'))

    def _output_json(self, results):
        """Output results as JSON"""
        import json
        output = []
        for result in results:
            if 'error' not in result:
                result['total_cost'] = result['calculated_price'] * result['refilled_quantity']
            output.append(result)
        
        self.stdout.write(json.dumps(output, indent=2, default=str))
