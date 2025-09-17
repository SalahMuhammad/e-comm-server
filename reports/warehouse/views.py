# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.db.models import Q
from datetime import datetime, date
from rest_framework.generics import ListAPIView
import csv
from io import StringIO
import json

from items.models import Items , Repositories
from .services.item_movement_service import ItemMovementService


@method_decorator(login_required, name='dispatch')
class ItemMovementReportView(View):
    """View for item movement reports."""
    
    def get(self, request, item_id=None):
        """Display movement report form and results."""
        context = {
            'items': Items.objects.all().order_by('name'),
            'repositories': Repositories.objects.all().order_by('name')
        }
        
        # If item_id is provided in URL, auto-select it
        if item_id:
            context['selected_item_id'] = item_id
        
        return render(request, 'item_movement_report.html', context)
    
    def post(self, request):
        """Generate movement report based on form data."""
        try:
            # Get form data
            item_id = request.POST.get('item_id')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            repository_id = request.POST.get('repository_id')
            export_format = request.POST.get('export_format', 'html')
            
            # Validate required fields
            if not item_id:
                return JsonResponse({'error': 'Item is required'}, status=400)
            
            # Get item
            item = get_object_or_404(Items, id=item_id)
            
            # Parse dates
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
            repository_id = int(repository_id) if repository_id else None
            
            # Generate report
            service = ItemMovementService(item)
            report_data = service.get_movement_report(
                start_date=start_date,
                end_date=end_date,
                repository_id=repository_id
            )
            
            # Handle different export formats
            if export_format == 'json':
                return self._export_json(report_data)
            elif export_format == 'csv':
                return self._export_csv(report_data)
            else:
                # Return HTML response with report data
                context = {
                    'report_data': report_data,
                    'items': Items.objects.all().order_by('name'),
                    'repositories': Repositories.objects.all().order_by('name'),
                    'filters': {
                        'item_id': item_id,
                        'start_date': start_date,
                        'end_date': end_date,
                        'repository_id': repository_id
                    }
                }
                return render(request, 'reports/item_movement_report.html', context)
                
        except Exception as e:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': str(e)}, status=500)
            else:
                context = {
                    'error': str(e),
                    'items': Items.objects.all().order_by('name'),
                    'repositories': Repositories.objects.all().order_by('name')
                }
                return render(request, 'reports/item_movement_report.html', context)
    
    def _export_json(self, report_data):
        """Export report as JSON."""
        # Convert Decimal objects to strings for JSON serialization
        def decimal_handler(obj):
            if hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            elif hasattr(obj, '__str__'):  # Decimal objects
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        response = JsonResponse(report_data, json_dumps_params={'default': decimal_handler})
        response['Content-Disposition'] = f'attachment; filename="item_movement_report_{report_data["item"]["id"]}.json"'
        return response
    
    def _export_csv(self, report_data):
        """Export report as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="item_movement_report_{report_data["item"]["id"]}.csv"'
        
        writer = csv.writer(response)
        
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
        
        return response


class ItemRepositoryMovementReport(ListAPIView):
    def get(self, request, *args, **kwargs):
        """API endpoint for getting item movement data."""    
        Items.objects.all()
        try:
            item = Items \
                .objects \
                .filter(
                    Q(pk=request.GET.get('item'))
                    if request.GET.get('item') 
                    else 
                    Q(id__isnull=True)
                ).first()
            repository = Repositories \
                .objects \
                .filter(
                    Q(pk=request.GET.get('repository_id')) if 
                        request.GET.get('repository_id') else 
                    Q(id__isnull=True)
                ).first()

            # Get query parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            if not item: # and not repository: 
                return JsonResponse({'details': 'you should send item or repository...'}, status=400)
            
            # Parse dates
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
            
            # Generate report
            service = ItemMovementService(item) if item else ItemMovementService()
            report_data = service.get_movement_report(
                start_date=start_date,
                end_date=end_date,
                repository=repository
            )
            
            # Convert Decimal objects to strings for JSON serialization
            def decimal_handler(obj):
                if hasattr(obj, 'isoformat'):  # datetime objects
                    return obj.isoformat()
                elif hasattr(obj, '__str__'):  # Decimal objects
                    return str(obj)
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            return JsonResponse(report_data, json_dumps_params={'default': decimal_handler})
            
        except Exception as e:
            print(e)
            return JsonResponse({'error': str(e)}, status=500)


@login_required
def bulk_movement_report(request):
    """Generate movement reports for multiple items."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        item_ids = data.get('item_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        repository_id = data.get('repository_id')
        
        if not item_ids:
            return JsonResponse({'error': 'At least one item is required'}, status=400)
        
        # Parse dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        repository_id = int(repository_id) if repository_id else None
        
        # Generate reports for all items
        reports = []
        for item_id in item_ids:
            try:
                item = Items.objects.get(id=item_id)
                service = ItemMovementService(item)
                report_data = service.get_movement_report(
                    start_date=start_date,
                    end_date=end_date,
                    repository_id=repository_id
                )
                reports.append(report_data)
            except Items.DoesNotExist:
                continue
        
        # Convert Decimal objects to strings for JSON serialization
        def decimal_handler(obj):
            if hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            elif hasattr(obj, '__str__'):  # Decimal objects
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return JsonResponse({'reports': reports}, json_dumps_params={'default': decimal_handler})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
