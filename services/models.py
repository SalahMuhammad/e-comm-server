from django.db import models


class AppConfiguration(models.Model):
    # Stores the entire JSON configuration safely in a JSONField
    data = models.JSONField()

    def __str__(self):
        return "Application Configuration"
