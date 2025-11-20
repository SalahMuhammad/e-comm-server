from django.db import models
# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
from common.models import AbstractInvoice, AbstractInvoiceItems
from invoices.sales.models import invoice_status_handler
# from django.core.exceptions import ValidationError



class PurchaseInvoices(AbstractInvoice):
    def save(self, *args, **kwargs):
        r_payments = self.r_payments if self.id else None
        
        res = invoice_status_handler(r_payments, self.remaining_balance, self.total_amount)
        self.status = res[0]
        self.remaining_balance = res[1]
        
        super().full_clean()
        super().save(*args, **kwargs)


class PurchaseInvoiceItems(AbstractInvoiceItems):
    invoice = models.ForeignKey(PurchaseInvoices, on_delete=models.CASCADE, related_name='p_invoice_items')


    def __str__(self) -> str:
        return f"{self.item.name} - {self.quantity} @ {self.unit_price}"
    
    def save(self, *args, **kwargs):
        super().full_clean()
        super().save(*args, **kwargs)
