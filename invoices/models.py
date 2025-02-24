from django.db import models
# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
from owners.models import Owner
from users.models import User
from items.models import Items
from repositories.models import Repositories


class Invoice(models.Model):
    repository = models.ForeignKey(Repositories, on_delete=models.PROTECT)
    owner = models.ForeignKey(Owner, on_delete=models.PROTECT)
    is_purchase_invoice = models.BooleanField(default=0)
    # content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    # object_id = models.PositiveIntegerField(null=True)
    # content_object = GenericForeignKey("content_type", "object_id")
    paid = models.DecimalField(max_digits=8, decimal_places=2, blank=True)
    by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['-updated']


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Items, related_name='invoice_items', on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self) -> str:
        return f"{self.item.name} - {self.quantity} @ {self.unit_price}"
