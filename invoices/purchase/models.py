from django.db import models
# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
from common.models import AbstractInvoice, AbstractInvoiceItems
from invoices_owners.suppliers.models import Suppliers


class PurchaseInvoices(AbstractInvoice):
    supplier = models.ForeignKey(Suppliers, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=20, decimal_places=2, blank=True)


class PurchaseInvoiceItems(AbstractInvoiceItems):
    invoice = models.ForeignKey(PurchaseInvoices, on_delete=models.CASCADE, related_name='items')


    def __str__(self) -> str:
        return f"{self.item.name} - {self.quantity} @ {self.unit_price}"
