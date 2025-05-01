from django.db import models
# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
from common.models import AbstractInvoice, AbstractInvoiceItems
# from django.core.exceptions import ValidationError


class PurchaseInvoices(AbstractInvoice):
    def save(self, *args, **kwargs):
        super().full_clean()
        super().save(*args, **kwargs)


class PurchaseInvoiceItems(AbstractInvoiceItems):
    invoice = models.ForeignKey(PurchaseInvoices, on_delete=models.CASCADE, related_name='p_invoice_items')


    def __str__(self) -> str:
        return f"{self.item.name} - {self.quantity} @ {self.unit_price}"
    
    def save(self, *args, **kwargs):
        super().full_clean()
        super().save(*args, **kwargs)
