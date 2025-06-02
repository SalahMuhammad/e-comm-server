from django.db import models
from common.models import UpdatedCreatedBy
from invoices.buyer_supplier_party.models import Party


class Payment(UpdatedCreatedBy):

    payment_types = (
        ('invoice_payment', 'invoice_payment'),
        ('advance_payment', 'advance_payment'),
        ('refund', 'refund'),
        ('expense', 'expense')
    )
    
    owner = models.ForeignKey(Party, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    # content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.PROTECT)
    # object_id = models.PositiveIntegerField()
    # owner = models.GenericForeignKey('content_type', 'object_id')

    paid = models.BooleanField(default=False)
    payment_method = models.ForeignKey('payment_method.PaymentMethod', on_delete=models.PROTECT)
    payment_type = models.CharField(max_length=20, choices=payment_types, default='invoice_payment')
    date = models.DateField()
    note = models.TextField(blank=True)


    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self) -> str:
        return f"{self.owner} - {self.amount}"


class ExpensePayment(UpdatedCreatedBy):
    payment_types = (
        ('invoice_payment', 'invoice_payment'),
        ('refund', 'refund'),
        ('expense', 'expense')
    )

    owner = models.ForeignKey(Party, on_delete=models.PROTECT, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    paid = models.BooleanField(default=False)
    payment_method = models.ForeignKey('payment_method.PaymentMethod', on_delete=models.PROTECT)
    payment_type = models.CharField(max_length=20, choices=payment_types, default='invoice_payment')
    date = models.DateField()
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
