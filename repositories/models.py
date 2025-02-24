from django.db import models
from users.models import User


class Repositories(models.Model):
    name = models.CharField(max_length=255, unique=True)
    by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


    class Meta:
        ordering = ['name']
