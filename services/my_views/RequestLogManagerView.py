import json
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status



class RequestLogManagerView(APIView):
    """
    DRF APIView to list, view, single-delete, and bulk-delete request log files stored on disk.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_log_dir = Path('request_logs')

    def get(self, request, method=None, filename=None):
        # 1. Retrieve a specific log file content if method and filename are provided
        if method and filename:
            method_dir = self.base_log_dir / method.lower()
            file_path = method_dir / filename
            
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

        # 2. List all log files (safely handling optional ?method= filter)
        filter_method = request.query_params.get('method')
        results = []
        
        if filter_method and filter_method.strip():
            methods_to_check = [filter_method.strip().lower()]
        else:
            methods_to_check = ['get', 'post', 'patch', 'put', 'delete']
        
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
        
        results = sorted(results, key=lambda x: x['created_at'], reverse=True)
        return Response(results, status=status.HTTP_200_OK)

    def delete(self, request, method=None, filename=None):
        # 1. Single file deletion (if method and filename are in URL path)
        if method and filename:
            method_dir = self.base_log_dir / method.lower()
            file_path = method_dir / filename

            if not file_path.resolve().is_relative_to(self.base_log_dir.resolve()):
                return Response({'detail': 'Invalid path.'}, status=status.HTTP_400_BAD_REQUEST)

            if not file_path.exists() or not file_path.is_file():
                return Response({'detail': 'Log file not found.'}, status=status.HTTP_404_NOT_FOUND)

            try:
                file_path.unlink()
                return Response({'detail': 'Log file deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                return Response({'detail': f'Error deleting log file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. Bulk deletion (if method and filename are NOT in URL path)
        # Supports parameters passed via Query Params (?url_contains=...&method=...) or JSON Body
        url_contains = request.query_params.get('url_contains') or request.data.get('url_contains')
        target_method = request.query_params.get('method') or request.data.get('method')

        # Safeguard: Require at least one filter criterion to prevent accidental wiping of all logs
        if not url_contains and not target_method:
            return Response(
                {
                    'detail': 'Safety restriction: Please provide at least one filter criterion (url_contains or method) for bulk deletion.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count = 0
        failed_count = 0
        
        if target_method and target_method.strip():
            methods_to_check = [target_method.strip().lower()]
        else:
            methods_to_check = ['get', 'post', 'patch', 'put', 'delete']

        for m in methods_to_check:
            m_dir = self.base_log_dir / m
            if m_dir.exists() and m_dir.is_dir():
                for file_path in m_dir.glob('*.json'):
                    should_delete = False

                    if url_contains:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                log_data = json.load(f)
                            log_url = log_data.get('url', '')
                            if url_contains.lower() in log_url.lower():
                                should_delete = True
                        except Exception:
                            continue
                    else:
                        # If only a method filter was specified, target all files in that method folder
                        should_delete = True

                    if should_delete:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception:
                            failed_count += 1

        return Response(
            {
                'detail': 'Bulk deletion executed successfully.',
                'deleted_count': deleted_count,
                'failed_count': failed_count
            },
            status=status.HTTP_200_OK
        )
