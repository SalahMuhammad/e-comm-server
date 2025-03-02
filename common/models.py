from django.db import models
from django.core.exceptions import ValidationError
from users.models import User
# from django.utils.timezone import now

class UpdatedCreatedBy(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    by = models.ForeignKey(User, on_delete=models.PROTECT)

    # @property
    # def alive(self):
    #     return (now() - updated_at).days < 7

    class Meta:
        abstract = True



class InvoiceStatus(models.IntegerChoices):
    DRAFT = 1, "Draft"
    ISSUED = 2, "Issued"
    UNPAID = 3, "Unpaid"
    PARTIALLY_PAID = 4, "Partially Paid"
    PAID = 5, "Paid"
    OVERDUE = 6, "Overdue"
    CANCELLED = 7, "Cancelled"
    DISPUTED = 8, "Disputed"


class AbstractInvoice(UpdatedCreatedBy):
    issue_date = models.DateField()
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=20, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=20, decimal_places=2)
    status = models.IntegerField(choices=InvoiceStatus.choices, default=InvoiceStatus.UNPAID)
    notes = models.TextField(blank=True)
    
    # owner = models.ForeignKey(Owner, on_delete=models.PROTECT)
    # is_purchase_invoice = models.BooleanField(default=0)
    # content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    # object_id = models.PositiveIntegerField(null=True)
    # content_object = GenericForeignKey("content_type", "object_id")    

    def clean(self):
        super().clean()
        if self.due_date and self.issue_date and self.due_date < self.issue_date:
            raise ValidationError({"detail": "Due date must be after issue date."})


    class Meta:
        abstract = True
        ordering = ['-created_at']


class AbstractInvoiceItems(models.Model):
    item = models.ForeignKey('items.Items', related_name='invoice_items', on_delete=models.PROTECT)
    repository = models.ForeignKey('repositories.Repositories', on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=20, decimal_places=2)


    class Meta:
        abstract = True
        # ordering = ['-created_at']
