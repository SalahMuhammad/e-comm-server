from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, Http404
from django.conf import settings
from django.utils.encoding import smart_str
from .services.file_system_service import FileSystemService
from .serializers import DirectoryListingSerializer
import os


class FileSystemListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List available file system roots"""
        roots = getattr(settings, 'FILE_SYSTEM_ROOTS', {})
        
        available_roots = []
        for name, path in roots.items():
            if os.path.exists(path) and os.path.isdir(path):
                available_roots.append({
                    'name': name,
                    'path': path,
                    'display_name': name.replace('_', ' ').title()
                })
        
        return Response({
            'available_roots': available_roots,
            'message': 'Use /browse/?path=<path> to browse directories'
        })

class DirectoryBrowseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Browse directory contents"""
        path = request.query_params.get('path', '')
        include_hidden = request.query_params.get('include_hidden', 'false').lower() == 'true'
        
        if not path:
            return Response({
                'error': 'Path parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Security check: ensure path is within allowed roots
        if not self._is_path_allowed(path):
            return Response({
                'error': 'Access to this path is not allowed'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not os.path.exists(path) or not os.path.isdir(path):
            return Response({
                'error': 'Directory not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get directory contents
        contents = FileSystemService.get_directory_contents(path, include_hidden)
        
        # Calculate statistics
        total_files = sum(1 for item in contents if item['is_file'])
        total_directories = sum(1 for item in contents if item['is_directory'])
        
        # Get parent directory
        parent_path = os.path.dirname(path) if path != os.path.dirname(path) else None
        if parent_path and not self._is_path_allowed(parent_path):
            parent_path = None
        
        serializer = DirectoryListingSerializer(data={
            'current_path': path,
            'parent_path': parent_path,
            'items': contents,
            'total_files': total_files,
            'total_directories': total_directories
        })
        
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _is_path_allowed(self, path):
        """Check if the path is within allowed roots"""
        roots = getattr(settings, 'FILE_SYSTEM_ROOTS', {})
        abs_path = os.path.abspath(path)
        
        for root_path in roots.values():
            abs_root = os.path.abspath(root_path)
            if abs_path.startswith(abs_root):
                return True
        return False

class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Download a file from the file system"""
        file_path = request.query_params.get('path', '')
        items_export = request.query_params.get('itmes_export', None)
        
        if items_export:
            import subprocess

            # Example: Run a simple 'ls' command
            result = subprocess.run(['python3', 'manage.py', 'items_as_xlsx'], capture_output=True, text=True)
            file_path = result.stdout.split('\n')[1] or None

        if not file_path:
            return Response({
                'error': 'File path is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Security check
        if not self._is_path_allowed(file_path):
            return Response({
                'error': 'Access to this file is not allowed'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return Response({
                'error': 'File not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if file type is allowed
        if not FileSystemService.is_allowed_file(file_path):
            return Response({
                'error': 'File type not allowed'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Get file info
            file_info = FileSystemService.get_file_info(file_path)
            
            # Create response with file streaming for large files
            def file_iterator(file_path, chunk_size=8192):
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            
            response = HttpResponse(
                file_iterator(file_path),
                content_type=file_info['content_type']
            )
            
            filename = smart_str(file_info['name'])
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = file_info['size']
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Error downloading file: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _is_path_allowed(self, path):
        """Check if the path is within allowed roots"""
        roots = getattr(settings, 'FILE_SYSTEM_ROOTS', {})
        abs_path = os.path.abspath(path)
        
        for root_path in roots.values():
            abs_root = os.path.abspath(root_path)
            if abs_path.startswith(abs_root):
                return True
        return False

class FileInfoView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get detailed information about a file"""
        file_path = request.query_params.get('path', '')
        
        if not file_path:
            return Response({
                'error': 'File path is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Security check
        if not self._is_path_allowed(file_path):
            return Response({
                'error': 'Access to this file is not allowed'
            }, status=status.HTTP_403_FORBIDDEN)
        
        file_info = FileSystemService.get_file_info(file_path)
        
        if not file_info:
            return Response({
                'error': 'File not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(file_info)
    
    def _is_path_allowed(self, path):
        """Check if the path is within allowed roots"""
        roots = getattr(settings, 'FILE_SYSTEM_ROOTS', {})
        abs_path = os.path.abspath(path)
        
        for root_path in roots.values():
            abs_root = os.path.abspath(root_path)
            if abs_path.startswith(abs_root):
                return True
        return False

class FileSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search for files in specified directory"""
        search_path = request.query_params.get('path', '')
        query = request.query_params.get('q', '')
        recursive = request.query_params.get('recursive', 'false').lower() == 'true'
        
        if not search_path or not query:
            return Response({
                'error': 'Both path and query parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Security check
        if not self._is_path_allowed(search_path):
            return Response({
                'error': 'Access to this path is not allowed'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            results = self._search_files(search_path, query, recursive)
            return Response({
                'query': query,
                'search_path': search_path,
                'recursive': recursive,
                'results': results,
                'count': len(results)
            })
        except Exception as e:
            return Response({
                'error': f'Search failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _search_files(self, root_path, query, recursive=False):
        """Search for files matching query"""
        results = []
        query_lower = query.lower()
        
        if recursive:
            # Walk through all subdirectories
            for root, dirs, files in os.walk(root_path):
                for file in files:
                    if query_lower in file.lower():
                        file_path = os.path.join(root, file)
                        if FileSystemService.is_allowed_file(file_path):
                            file_info = FileSystemService.get_file_info(file_path)
                            if file_info:
                                results.append(file_info)
        else:
            # Search only in current directory
            contents = FileSystemService.get_directory_contents(root_path)
            for item in contents:
                if item['is_file'] and query_lower in item['name'].lower():
                    results.append(item)
        
        return results
    
    def _is_path_allowed(self, path):
        """Check if the path is within allowed roots"""
        roots = getattr(settings, 'FILE_SYSTEM_ROOTS', {})
        abs_path = os.path.abspath(path)
        
        for root_path in roots.values():
            abs_root = os.path.abspath(root_path)
            if abs_path.startswith(abs_root):
                return True
        return False
