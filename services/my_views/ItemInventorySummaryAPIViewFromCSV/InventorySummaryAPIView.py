import os
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .utils import get_safe_item_name, parse_detailed_csv

class InventorySummaryAPIView(APIView):
    """
    API endpoint for inventory_summary.csv with links to detailed exports.
    """
    def get(self, request):
        csv_path = os.path.join(
            settings.MEDIA_ROOT, 
            'year-closure', 
            'inventory_csv_export', 
            'inventory_summary.csv'
        )
        
        if not os.path.exists(csv_path):
            return Response(
                {"error": "Summary CSV file not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Read CSV using pandas
        df = pd.read_csv(csv_path)
        # Replace NaN values with None for clean JSON serialization
        df = df.where(pd.notnull(df), None)
        
        records = df.to_dict(orient='records')
        
        # Inject detail API link for each item
        base_url = request.build_absolute_uri('/api/services/inventory/detailed/')
        for record in records:
            item_name = record.get('item_name')
            if item_name:
                safe_name = get_safe_item_name(str(item_name))
                record['detail_link'] = f"{base_url}{safe_name}/"
            else:
                record['detail_link'] = None

        return Response({
            "total_items": len(records),
            "data": records
        }, status=status.HTTP_200_OK)


class InventoryDetailAPIView(APIView):
    def get(self, request, safe_item_name):
        # Append .csv explicitly here since URL path doesn't include the extension
        file_name = f"{safe_item_name}.csv" if not safe_item_name.endswith('.csv') else safe_item_name
        
        file_path = os.path.join(
            settings.MEDIA_ROOT, 
            'year-closure', 
            'inventory_detailed_exports', 
            file_name
        )

        if not os.path.exists(file_path):
            return Response(
                {"error": f"Detailed CSV for item '{safe_item_name}' not found at {file_path}."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        parsed_data = parse_detailed_csv(file_path)
        
        return Response({
            "item_safe_name": safe_item_name,
            "details": parsed_data
        }, status=status.HTTP_200_OK)
