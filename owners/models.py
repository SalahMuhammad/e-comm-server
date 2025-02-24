from django.db import models
from users.models import User
# from django.contrib.contenttypes.fields import GenericRelation
# from invoices.models import Invoice


class Owner(models.Model):
    name = models.CharField(max_length=255, unique=True)
    detail = models.TextField(max_length=1000, blank=True)
    # invoice = GenericRelation(Invoice)
    is_supplier = models.BooleanField(default=0)
    by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # def __str__(self) -> str:
    #     return self.name


    class Meta:
        ordering = ['name']
