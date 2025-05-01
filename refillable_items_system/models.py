from django.db import models
from common.models import UpdatedCreatedBy
from invoices.buyer_supplier_party.models import Party
from repositories.models import Repositories
from rest_framework.exceptions import ValidationError
from items.models import Items
from employees.models import Employee


# Create your models here.
class ItemTransformer(models.Model):
    item = models.ForeignKey(Items, related_name='transform_item_from', on_delete=models.CASCADE)
    transform = models.ForeignKey(Items, related_name='transform_item_to', on_delete=models.CASCADE)

    def __str__(self):
        return f'id: {self.item.id}, item: {self.item.name} -> id: {self.transform.id}, transform: {self.transform.name}'


class OreItem(UpdatedCreatedBy):
    item = models.OneToOneField(Items, related_name='ore_items', on_delete=models.PROTECT)


    def __str__(self):
        return self.item.name


class RefillableItemsInitialStockClientHas(UpdatedCreatedBy):
    item = models.ForeignKey(Items, related_name='refillable_initial_stock', on_delete=models.CASCADE)
    owner = models.ForeignKey(Party, related_name='refillable_initial_stock', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    def clean(self):
        # Call the parent class's clean method
        super().clean()
        
        # Check if the item is refillable
        if not ItemTransformer.objects.filter(item=self.item).exists():
            raise ValidationError({
                'item': 'Only refillable items can be used in initial stock records.'
            })
        
    def __str__(self):
        return f'client: {self.owner}, item: {self.item}, quantity: {self.quantity}'
    
    def save(self, *args, **kwargs):
        self.full_clean()  # This calls the clean method
        super().save(*args, **kwargs)


    class Meta:
        ordering = ['-date', '-created_at']


class RefundedRefillableItem(UpdatedCreatedBy):
    item = models.ForeignKey(Items, on_delete=models.CASCADE)
    owner = models.ForeignKey(Party, on_delete=models.CASCADE)
    repository = models.ForeignKey(Repositories, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    notes = models.TextField(blank=True)

    def clean(self):
        # Call the parent class's clean method
        super().clean()

        # Check if the item is refillable
        if not ItemTransformer.objects.filter(item=self.item).exists():
            raise ValidationError({
                'item': 'nooooooooooo Only refillable items can be used in RefundedRefillableItem.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()  # This calls the clean method
        super().save(*args, **kwargs)

    def __str__(self):
        return f'item: {self.item}, owner: {self.owner}, quantity: {self.quantity}'
    

    class Meta:
        ordering = ['-date', '-created_at']


class RefilledItem(UpdatedCreatedBy):
    refilled_item = models.ForeignKey(Items, on_delete=models.CASCADE)
    used_item = models.ForeignKey(OreItem, on_delete=models.CASCADE, related_name='used_item')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    repository = models.ForeignKey(Repositories, on_delete=models.CASCADE)
    refilled_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    used_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    notes = models.TextField(blank=True)


    def clean(self):
        # Call the parent class's clean method
        super().clean()

        # Check if the item is refillable
        if not ItemTransformer.objects.filter(item=self.refilled_item).exists():
            raise ValidationError({
                'refilled_item': f'RefilledItem()\'s model unkown used item or refilled item, refilled(id: {self.refilled_item.id}, name: {self.refilled_item}), used (id: {self.used_item.id}, name: {self.used_item}).'
            })
        if self.refilled_quantity <= 0:
            raise ValidationError({
                'refilled_quantity': 'Refilled quantity must be greater than zero.'
            })
        if self.used_quantity <= 0:
            raise ValidationError({
                'used_quantity': 'Used quantity must be greater than zero.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


    class Meta:
        ordering = ['-date', '-created_at']