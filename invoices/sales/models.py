from django.db import models
from common.models import AbstractInvoice, AbstractInvoiceItems


class SalesInvoice(AbstractInvoice):
    def save(self, *args, **kwargs):
        super().full_clean()
        super().save(*args, **kwargs)


class SalesInvoiceItem(AbstractInvoiceItems):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name='s_invoice_items')


    def __str__(self) -> str:
        return f"{self.item.name} - {self.quantity} @ {self.unit_price}"
    
    def save(self, *args, **kwargs):
        super().full_clean()
        super().save(*args, **kwargs)


class ReturnInvoice(AbstractInvoice):
    original_invoice = models.OneToOneField(SalesInvoice, on_delete=models.PROTECT, related_name='return_invoices')


    def save(self, *args, **kwargs):
        super().full_clean()
        super().save(*args, **kwargs)


class ReturnInvoiceItem(AbstractInvoiceItems):
    invoice = models.ForeignKey(ReturnInvoice, on_delete=models.CASCADE, related_name='s_invoice_items')


    def __str__(self) -> str:
        return f"{self.item.name} - {self.quantity} @ {self.unit_price}"
    
    def save(self, *args, **kwargs):
        super().full_clean()
        super().save(*args, **kwargs)
