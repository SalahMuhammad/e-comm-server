from django.db import models
# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
from items.models import Items
from repositories.models import Repositories
from common.models import UpdatedCreatedBy


class Invoice(UpdatedCreatedBy):
    repository = models.ForeignKey(Repositories, on_delete=models.PROTECT)
    # owner = models.ForeignKey(Owner, on_delete=models.PROTECT)
    is_purchase_invoice = models.BooleanField(default=0)
    # content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    # object_id = models.PositiveIntegerField(null=True)
    # content_object = GenericForeignKey("content_type", "object_id")
    paid = models.DecimalField(max_digits=8, decimal_places=2, blank=True)
    date = models.DateField(null=False)


    class Meta:
        ordering = ['-updated_at']


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Items, related_name='invoice_items', on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self) -> str:
        return f"{self.item.name} - {self.quantity} @ {self.unit_price}"
