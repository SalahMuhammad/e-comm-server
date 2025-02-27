from django.db import models
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


class AbstractInvoicesOwners(UpdatedCreatedBy):
    name = models.CharField(max_length=255, unique=True)
    detail = models.TextField(max_length=1000, blank=True)


    class Meta:
        abstract = True
        ordering = ['name']


    def __str__(self) -> str:
        return self.name


class AbstractInvoice(UpdatedCreatedBy):
    repository = models.ForeignKey('repositories.Repositories', on_delete=models.PROTECT)
    # owner = models.ForeignKey(Owner, on_delete=models.PROTECT)
    # is_purchase_invoice = models.BooleanField(default=0)
    # content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    # object_id = models.PositiveIntegerField(null=True)
    # content_object = GenericForeignKey("content_type", "object_id")
    paid = models.DecimalField(max_digits=20, decimal_places=2, blank=True)
    date = models.DateField(null=False)


    class Meta:
        abstract = True
        ordering = ['-created_at']


class AbstractInvoiceItems(models.Model):
    item = models.ForeignKey('items.Items', related_name='invoice_items', on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    class Meta:
        abstract = True
        # ordering = ['-created_at']
