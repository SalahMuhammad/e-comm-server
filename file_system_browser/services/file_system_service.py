import os
import mimetypes
from datetime import datetime
from django.conf import settings
import stat

class FileSystemService:
    """Service to handle file system operations"""
    
    @staticmethod
    def get_file_info(file_path):
        """Get detailed information about a file"""
        try:
            stat_info = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            return {
                'name': file_name,
                'path': file_path,
                'extension': file_ext,
                'size': stat_info.st_size,
                'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'is_file': os.path.isfile(file_path),
                'is_directory': os.path.isdir(file_path),
                'content_type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream',
                'permissions': oct(stat_info.st_mode)[-3:],
            }
        except (OSError, IOError):
            return None
    
    @staticmethod
    def is_allowed_file(file_path):
        """Check if file extension is allowed"""
        if not hasattr(settings, 'ALLOWED_FILE_EXTENSIONS'):
            return True
        
        _, ext = os.path.splitext(file_path)
        return ext.lower() in settings.ALLOWED_FILE_EXTENSIONS
    
    @staticmethod
    def get_directory_contents(directory_path, include_hidden=False):
        """Get contents of a directory"""
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            return []
        
        contents = []
        try:
            for item in os.listdir(directory_path):
                # Skip hidden files unless requested
                if not include_hidden and item.startswith('.'):
                    continue
                
                item_path = os.path.join(directory_path, item)
                file_info = FileSystemService.get_file_info(item_path)
                
                if file_info:
                    # Only include allowed files
                    if file_info['is_file'] and not FileSystemService.is_allowed_file(item_path):
                        continue
                    contents.append(file_info)
            
            # Sort: directories first, then files
            contents.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
            return contents
            
        except (OSError, IOError):
            return []
