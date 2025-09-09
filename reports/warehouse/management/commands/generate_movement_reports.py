# management/commands/generate_movement_reports.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, date
import csv
import os

from items.models import  Items
from reports.warehouse.services.item_movement_service import ItemMovementService


class Command(BaseCommand):
    help = 'Generate item movement reports for specified items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--items',
            nargs='+',
            type=int,
            help='Item IDs to generate reports for'
        )
        parser.add_argument(
            '--all-items',
            action='store_true',
            help='Generate reports for all items'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--repository',
            type=int,
            help='Repository ID to filter by'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./reports',
            help='Output directory for reports'
        )
        parser.add_argument(
            '--format',
            choices=['csv', 'json'],
            default='csv',
            help='Output format'
        )

    def handle(self, *args, **options):
        # Parse dates
        start_date = None
        end_date = None
        
        if options['start_date']:
            try:
                start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid start date format. Use YYYY-MM-DD')
                )
                return

        if options['end_date']:
            try:
                end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid end date format. Use YYYY-MM-DD')
                )
                return

        # Get items to process
        if options['all_items']:
            items = Items.objects.all()
        elif options['items']:
            items = Items.objects.filter(id__in=options['items'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify either --items or --all-items')
            )
            return

        if not items.exists():
            self.stdout.write(
                self.style.ERROR('No items found')
            )
            return

        # Create output directory
        output_dir = options['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        # Generate reports
        total_items = items.count()
        processed = 0
        
        for item in items:
            try:
                self.stdout.write(f'Processing item: {item.name} ({item.id})')
                
                # Generate report
                service = ItemMovementService(item)
                report_data = service.get_movement_report(
                    start_date=start_date,
                    end_date=end_date,
                    repository_id=options['repository']
                )
                
                # Save report
                if options['format'] == 'csv':
                    self._save_csv_report(report_data, output_dir)
                else:
                    self._save_json_report(report_data, output_dir)
                
                processed += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing item {item.id}: {str(e)}')
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {processed}/{total_items} reports in {output_dir}'
            )
        )

    def _save_csv_report(self, report_data, output_dir):
        """Save report as CSV file."""
        filename = f"item_movement_{report_data['item']['id']}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header information
            writer.writerow(['Item Movement Report'])
            writer.writerow(['Item:', report_data['item']['name']])
            writer.writerow(['Period:', f"{report_data['period']['start_date'] or 'All'} to {report_data['period']['end_date'] or 'All'}"])
            writer.writerow(['Repository:', report_data['period']['repository_id'] or 'All'])
            writer.writerow([])
            
            # Write stock summary
            writer.writerow(['Stock Summary'])
            writer.writerow(['Initial Stock:', report_data['stock_summary']['initial_stock']])
            writer.writerow(['Final Stock:', report_data['stock_summary']['final_stock']])
            writer.writerow(['Net Movement:', report_data['stock_summary']['net_movement']])
            writer.writerow([])
            
            # Write movement details
            writer.writerow(['Movement Details'])
            writer.writerow([
                'Date', 'Type', 'Reference', 'Quantity', 'Unit Price', 
                'Total Value', 'Repository', 'Notes'
            ])
            
            for movement in report_data['movements']:
                writer.writerow([
                    movement['date'],
                    movement['type'],
                    movement['reference_number'],
                    movement['quantity'],
                    movement.get('unit_price', ''),
                    movement.get('total_value', ''),
                    movement.get('repository', ''),
                    movement.get('notes', '')
                ])

    def _save_json_report(self, report_data, output_dir):
        """Save report as JSON file."""
        import json
        
        filename = f"item_movement_{report_data['item']['id']}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Convert Decimal objects to strings for JSON serialization
        def decimal_handler(obj):
            if hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            elif hasattr(obj, '__str__'):  # Decimal objects
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(report_data, jsonfile, indent=2, default=decimal_handler)