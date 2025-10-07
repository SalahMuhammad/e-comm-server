from django.db import models
from common.models import UpdatedCreatedBy
from invoices.buyer_supplier_party.models import Party


class DebtSettlement(UpdatedCreatedBy):
    status = (
        ('not_approved', 'not_approved'),
        ('approved', 'approved'),
    )

    amount = models.DecimalField(max_digits=20, decimal_places=2)
    owner = models.ForeignKey(Party, on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=20, choices=status, default='not_approved')
    date = models.DateField()
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
