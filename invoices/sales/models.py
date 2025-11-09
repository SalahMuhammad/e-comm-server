from decimal import Decimal
from django.db import models
from common.models import AbstractInvoice, AbstractInvoiceItems



class SalesInvoice(AbstractInvoice):
    def save(self, *args, **kwargs):
        payments = self.payments if self.id else None
        
        res = invoice_status_handler(payments, self.remaining_balance, self.total_amount)
        self.status = res[0]
        self.remaining_balance = res[1]

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




# utils ------------------------------------------------------------------




def invoice_status_handler(payments, remaining_balance, total_amount):
    confirmed_payments = 0

    if payments:
        confirmed_payments = payments \
        .filter(
            status='confirmed'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

    remaining_balance = total_amount - confirmed_payments

    status = -1
    if remaining_balance == total_amount:
        status = 3 # unpaid
    elif remaining_balance == 0:
        status = 5 # paid
    elif remaining_balance < 0:
        status = 6 # overpaid
    elif remaining_balance > 0:
        status = 4 # partially paid

    return (status, remaining_balance)
