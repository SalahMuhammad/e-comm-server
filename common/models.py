from django.db import models
from rest_framework.serializers import ValidationError
from users.models import User


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
    REFUNDED = 9, "Refunded"


class AbstractInvoice(UpdatedCreatedBy):
    owner = models.ForeignKey("buyer_supplier_party.Party", on_delete=models.PROTECT)
    issue_date = models.DateField()
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    remaining_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    status = models.IntegerField(choices=InvoiceStatus.choices, default=InvoiceStatus.UNPAID)
    repository_permit = models.BooleanField(default=0)
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
    
    def __str__(self):
        return f'{self.owner.name} - {self.issue_date} - {self.total_amount} - {self.status} - {self.repository_permit}'


    class Meta:
        abstract = True
        ordering = ['-issue_date', '-created_at']


class AbstractInvoiceItems(models.Model):
    item = models.ForeignKey('items.Items', on_delete=models.PROTECT)
    repository = models.ForeignKey('repositories.Repositories', on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=20, decimal_places=2, default=0)


    def clean(self):
        super().clean()
        
        if self.quantity <= 0:
            raise ValidationError({"detail": ["Quantity must be greater than zero."]})
        
        if self.unit_price < 0:
            raise ValidationError({"detail": ["Unit price cannot be negative."]})
        
        if self.discount < 0:
            raise ValidationError({"detail": ["Discount cannot be negative."]})
        
        if self.tax_rate < 0:
            raise ValidationError({"detail": ["Tax rate cannot be negative."]})
        
        if self.total < 0:
            raise ValidationError({"detail": ["Total cannot be negative."]})


    class Meta:
        abstract = True
        # ordering = ['-created_at']
