from django.db import models
from common.models import UpdatedCreatedByV2
from invoices.buyer_supplier_party.models import Party
from items.models import Items
from datetime import date


class Maintenance(UpdatedCreatedByV2):
    client = models.ForeignKey(Party, on_delete=models.PROTECT, related_name='maintenance_transactions')
    serial_number = models.CharField(max_length=100, blank=True)
    item = models.ForeignKey(Items, on_delete=models.PROTECT)
    status = models.CharField(max_length=50, choices=[
            ('pending', 'pending'), 
            ('maintained', 'maintained'), 
            ('rejected', 'rejected'), 
            ('mcomplete', 'mcomplete'), 
            # ('unknown', 'unknown'),
        ], 
        default='pending', 
        help_text="Maintenance date + Malfunctions => 'maintained', date out + blank(Maintenance date) + blank(Malfunctions) => 'rejected', blank(Maintenance date) + blank(Date Out) + blank(Malfunctions) => 'pending', otherwise 'unknown'"
    )
    date_in = models.DateField(default=date.today)
    maintenance_date = models.DateField(null=True, blank=True)
    date_out = models.DateField(null=True, blank=True)
    by = models.ForeignKey("users.User", on_delete=models.PROTECT, blank=True, null=True, related_name='maintained_by')
    malfunctions = models.TextField(blank=True)
    notes = models.TextField(blank=True)


    def __str__(self):
        return f'client: {self.client}, S/N: {self.serial_number}, Date In: {self.date_in}'

    def save(self, *args, **kwargs):
        self.status = 'pending'
        if self.maintenance_date and not self.date_out:
            self.status = 'maintained'
        elif self.date_out and not self.maintenance_date:
            self.status = 'rejected'
        elif self.maintenance_date and self.date_out:
            self.status = 'mcomplete'
        # elif (not self.maintenance_date and self.malfunctions) or (self.date_out and not self.malfunctions):
        #     self.status = 'unknown'

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_in']


class TransactionSpareParts(UpdatedCreatedByV2):
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, related_name='parts')
    spare_part = models.ForeignKey(Items, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)