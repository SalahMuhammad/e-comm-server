from .models import RequestLog
from .serializers import RequestLogSerializer
from rest_framework import viewsets


class RequestLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling request logs.
    """
    queryset = RequestLog.objects.all()
    serializer_class = RequestLogSerializer
