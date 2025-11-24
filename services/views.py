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


class CreateDbBackup(APIView):
    def get(self, request, *args, **kwargs):
        command = [
            'python3', 
            'manage.py', 
            'db_backup'
        ]
        command.append('--data_only') if request.query_params.get('data-only', None) else None
        subprocess.run(command, capture_output=True, text=True)

        return Response()


class CreateItemsAsXLSX(APIView):
    def get(self, request, *args, **kwargs):
        subprocess.run(['python3', 'manage.py', 'items_as_xlsx'], capture_output=True, text=True)
        return Response()
