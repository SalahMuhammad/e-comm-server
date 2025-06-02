from django.db import models
from common.models import UpdatedCreatedBy


class RequestLog(UpdatedCreatedBy):
    """
    Model to store request logs.
    """
    method = models.CharField(max_length=10)
    url = models.URLField()
    headers = models.JSONField()
    body = models.JSONField(null=True, blank=True)
    response_status = models.IntegerField()
    response_body = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.method} {self.url} - {self.response_status}"
    

    class Meta:
        ordering = ['-created_at']
