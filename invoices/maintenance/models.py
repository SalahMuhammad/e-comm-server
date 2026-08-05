from django.db import models
from common.models import UpdatedCreatedByV2
from invoices.buyer_supplier_party.models import Party
from items.models import Items
from datetime import date
from decimal import Decimal
from django.core.validators import MinValueValidator



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
    )
    date_in = models.DateField(default=date.today, blank=True)
    maintenance_date = models.DateField(null=True, blank=True)
    date_out = models.DateField(null=True, blank=True)
    maintained_by = models.ForeignKey("employees.Employee", on_delete=models.PROTECT, blank=True, null=True, related_name='maintained_by')
    malfunctions = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, validators=[MinValueValidator(Decimal('0.00'))])


    def __str__(self):
        return f'client: {self.client}, S/N: {self.serial_number}, Date In: {self.date_in}'

    def save(self, *args, **kwargs):
        status_map = {
            (False, False): 'pending',
            (False, True):  'maintained',
            (True, False):  'rejected',
            (True, True):   'mcomplete'
        }

        self.status = status_map[(bool(self.date_out), bool(self.maintenance_date))]

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_in']


class TransactionSpareParts(UpdatedCreatedByV2):
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, related_name='parts')
    spare_part = models.ForeignKey(Items, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
