from django.db import models
from common.models import UpdatedCreatedBy


class Owner(UpdatedCreatedBy):
    name = models.CharField(max_length=255, unique=True)
    detail = models.TextField(max_length=1000, blank=True)
    credit_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)


    class Meta:
        ordering = ['name']


    def __str__(self) -> str:
        return self.name 
