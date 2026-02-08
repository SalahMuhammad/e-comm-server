import subprocess
# 
from rest_framework.views import APIView
from rest_framework.response import Response
# 
from .services.media_browser import get_media_path_files



# Create your views here.
class MediaBrowser(APIView):
    def get(self, request, *args, **kwargs):
        return Response(get_media_path_files(''))


import subprocess
import os
import json
import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .services.media_browser import get_media_path_files
from auth.permissions import IsSuperuser
from rest_framework.permissions import AllowAny

class MediaBrowser(APIView):
    def get(self, request, *args, **kwargs):
        return Response(get_media_path_files(''))


class CreateDbBackup(APIView):
    permission_classes = [IsSuperuser]
    
    def post(self, request, *args, **kwargs):
        # We use POST for creation to be semantically correct, but frontend might be using GET currently? 
        # Checking actions.js, createDbBackup uses POST.
        # But previous view had `get`. I will support POST.
        
        try:
            command = ['python3', 'manage.py', 'db_backup']
            if request.data.get('data-only') or request.query_params.get('data-only'):
                command.append('--data_only')
            if request.data.get('media') or request.query_params.get('media'):
                command.append('--media')
                
            # Add Notes and User
            notes = request.data.get('notes', '')
            if notes:
                command.extend(['--notes', notes])
            
            user = request.user.username if request.user and request.user.is_authenticated else 'System'
            command.extend(['--user', user])
                
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            
            # Parse output to find file path
            output_lines = result.stdout.split('\n')
            backup_file = None
            for line in output_lines:
                if "Backup saved to:" in line:
                    backup_file = line.split("Backup saved to:")[1].strip()
                    break
            
            if backup_file and os.path.exists(backup_file):
                with open(backup_file, "rb") as f:
                    file_data = base64.b64encode(f.read()).decode('utf-8')
                    
                file_name = os.path.basename(backup_file)
                
                return Response({
                    "message": "Backup created successfully",
                    "file_name": file_name,
                    "file_data": file_data,
                    "content_type": "application/sql", # or text/plain
                    "is_file": True
                })
            else:
                 return Response({"message": "Backup created but file not found in output"}, status=status.HTTP_200_OK)

        except subprocess.CalledProcessError as e:
            return Response({"error": str(e.stderr)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        # Keep get for compatibility if needed, pass to post logic
        return self.post(request, *args, **kwargs)


class RestoreDbBackup(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """List available backups"""
        try:
            with open('media/config.json', 'r') as file:
                config = json.load(file)
            backup_dir = os.path.expanduser(config.get('db_backup_path', 'media/backups'))
            
            if not os.path.exists(backup_dir):
                return Response([], status=status.HTTP_200_OK)
                
            backups = []
            for f in os.listdir(backup_dir):
                if f.endswith('.sql') or f.endswith('.dump') or f.endswith('.zip'):
                    if f.endswith('.json'): continue # Skip metadata files themselves when listing backups

                    file_path = os.path.join(backup_dir, f)
                    stats = os.stat(file_path)
                    
                    # Try to find corresponding metadata file
                    base_name = os.path.splitext(f)[0]
                    # If it's a .zip created from .sql, the base name might need adjustment if logic differs,
                    # but our db_backup uses simpler naming: `timestamp[_flags]`.zip
                    # Metadata file is `timestamp[_flags]`.json
                    
                    metadata_path = os.path.join(backup_dir, f"{base_name}.json")
                    metadata = {}
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r') as mf:
                                metadata = json.load(mf)
                        except:
                            pass

                    backups.append({
                        "id": f,
                        "name": f,
                        "created_at": stats.st_mtime, # Frontend can format this
                        "size": stats.st_size,
                        "notes": metadata.get('notes', ''),
                        "user": metadata.get('user', ''),
                        "created_at_formatted": metadata.get('created_at', '') # Use recorded creation time if available
                    })
            
            # Sort by created_at desc
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return Response(backups)
        except Exception as e:
             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """Restore from file or existing backup"""
        try:
            file_obj = request.FILES.get('file')
            backup_id = request.data.get('backup_id')
            
            target_path = None
            temp_file = False
            
            if file_obj:
                # Save uploaded file temporarily
                with open('media/config.json', 'r') as file:
                    config = json.load(file)
                backup_dir = os.path.expanduser(config.get('db_backup_path', 'media/backups'))
                
                target_path = os.path.join(backup_dir, f"restore_temp_{file_obj.name}")
                with open(target_path, 'wb+') as destination:
                    for chunk in file_obj.chunks():
                        destination.write(chunk)
                temp_file = True # Mark to delete after
                
            elif backup_id:
                # Use existing backup
                target_path = backup_id # db_restore handles full path or filename in dir
            else:
                return Response({"error": "No file or backup_id provided"}, status=status.HTTP_400_BAD_REQUEST)
                
            # Run restore command
            command = ['python3', 'manage.py', 'db_restore', target_path]
            subprocess.run(command, capture_output=True, text=True, check=True)
            
            if temp_file and os.path.exists(target_path):
                os.remove(target_path)
                
            return Response({"message": "Database restored successfully"})
            
        except subprocess.CalledProcessError as e:
            print(f"DEBUG: Restore subprocess failed: {e.stderr}")
            return Response({"error": f"Restore failed: {e.stderr}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f"DEBUG: Restore view execution failed: {e}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateItemsAsXLSX(APIView):
    def get(self, request, *args, **kwargs):
        subprocess.run(['python3', 'manage.py', 'items_as_xlsx'], capture_output=True, text=True)
        return Response()

class BackupConfigView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request, *args, **kwargs):
        try:
            config_path = 'media/config.json'
            if not os.path.exists(config_path):
                # Ensure directory exists
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                
                # Create default config
                default_config = {
                    "db_backup_path": "media/backups",
                    "max_backups": 15
                }
                with open(config_path, 'w') as file:
                    json.dump(default_config, file, indent=4)
                
                return Response({"max_backups": 15})
                 
            with open(config_path, 'r') as file:
                config = json.load(file)
            return Response({"max_backups": config.get('max_backups', 15)})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        try:
            max_backups = request.data.get('max_backups')
            if max_backups is None:
                return Response({"error": "max_backups is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                max_backups = int(max_backups)
                if max_backups < 1:
                     return Response({"error": "max_backups must be at least 1"}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                 return Response({"error": "max_backups must be a number"}, status=status.HTTP_400_BAD_REQUEST)

            config_path = 'media/config.json'
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    try:
                        config = json.load(file)
                    except json.JSONDecodeError:
                        pass
            
            config['max_backups'] = max_backups
            
            with open(config_path, 'w') as file:
                json.dump(config, file, indent=4)
                
            return Response({"message": "Configuration updated", "max_backups": max_backups})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
