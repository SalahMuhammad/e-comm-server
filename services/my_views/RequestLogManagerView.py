import json
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status



class RequestLogManagerView(APIView):
    """
    DRF APIView to list, view, and delete request log files stored on disk.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_log_dir = Path('request_logs')

    def get(self, request, method=None, filename=None):
        # 1. Retrieve a specific log file content if method and filename are provided
        if method and filename:
            method_dir = self.base_log_dir / method.lower()
            file_path = method_dir / filename
            
            # Security check to prevent path traversal attacks
            if not file_path.resolve().is_relative_to(self.base_log_dir.resolve()):
                return Response({'detail': 'Invalid path.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not file_path.exists() or not file_path.is_file():
                return Response({'detail': 'Log file not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Response(data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': f'Error reading log file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. List all log files (optionally filtered by ?method=get)
        filter_method = request.query_params.get('method')
        results = []
        
        methods_to_check = [filter_method.lower()] if filter_method else ['get', 'post', 'patch', 'put', 'delete']
        
        for m in methods_to_check:
            m_dir = self.base_log_dir / m
            if m_dir.exists() and m_dir.is_dir():
                for file_path in m_dir.glob('*.json'):
                    stat = file_path.stat()
                    results.append({
                        'method': m.upper(),
                        'filename': file_path.name,
                        'size_bytes': stat.st_size,
                        'created_at': stat.st_mtime
                    })

        # Sort logs by most recent first
        results = sorted(results, key=lambda x: x['created_at'], reverse=True)
        return Response(results, status=status.HTTP_200_OK)

    def delete(self, request, method=None, filename=None):
        # Delete a specific log file from disk
        if not method or not filename:
            return Response({'detail': 'Method and filename are required for deletion.'}, status=status.HTTP_400_BAD_REQUEST)

        method_dir = self.base_log_dir / method.lower()
        file_path = method_dir / filename

        # Security check to prevent path traversal attacks
        if not file_path.resolve().is_relative_to(self.base_log_dir.resolve()):
            return Response({'detail': 'Invalid path.'}, status=status.HTTP_400_BAD_REQUEST)

        if not file_path.exists() or not file_path.is_file():
            return Response({'detail': 'Log file not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            file_path.unlink()
            return Response({'detail': 'Log file deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'detail': f'Error deleting log file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
