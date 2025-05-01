from django.db import models
from repositories.models import Repositories
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
# from django.core.exceptions import ValidationError
from common.models import UpdatedCreatedBy
import os
from django.utils.timezone import now


class Items(UpdatedCreatedBy):
	name = models.CharField(max_length=150, unique=True)
	price1 = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	price2 = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	price3 = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	price4 = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	is_refillable = models.BooleanField(default=False)

	# run on fly whenever accessed
	# @property
	# def stock(self):
	# 	purchased_quantity = PurchaseInvoice.objects.filter(invoice__items__item=self).aggregate(Sum('invoice__items__quantity'))['invoice__items__quantity__sum'] or 0
	# 	sold_quantity = SalesInvoice.objects.filter(invoice__items__item=self).aggregate(Sum('invoice__items__quantity'))['invoice__items__quantity__sum'] or 0
	# 	return purchased_quantity - sold_quantity

	def __str__(self):
		return self.name


	class Meta:
		ordering = ['name', '-created_at']


class Images(models.Model):
	item = models.ForeignKey(Items, related_name='images', on_delete=models.SET_NULL, null=True)
	img = models.ImageField(upload_to='items-images', null=True)

	
	def delete(self, *args, **kwargs):
        # Delete the file from the file system
		if self.img:
			if os.path.isfile(self.img.path):
				os.remove(self.img.path)
        
        # Call the "real" delete() method
		super(Images, self).delete(*args, **kwargs)
	

class Stock(models.Model):
	quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	item = models.ForeignKey(Items, related_name='stock', on_delete=models.CASCADE)
	repository = models.ForeignKey(Repositories, on_delete=models.PROTECT)
	

	def adjust_stock(self, quantity):
		self.quantity += quantity
		try:
			self.full_clean()  # Validate the model
			self.save()
		except ValidationError as e:
			raise serializers.ValidationError({'detail': e})
			# raise serializers.ValidationError({'detail': e.messages})
		
	def clean(self):
		super().clean()
		if self.quantity < 0:
			raise ValidationError(f'لا توجد قطع كافيه من \'{self.item}\' في \'{self.repository}\'. المتاح: {self.quantity}')

	
	class Meta:
		constraints = [
			models.CheckConstraint(check=models.Q(quantity__gte=0), name='non_negative_quantity')
		]


	def __str__(self) -> str:
		return f"repository: {self.repository.name}, item: {self.item}"
	

	class Meta:
		ordering = ['repository']


class Barcode(models.Model):
	item = models.ForeignKey(Items, on_delete=models.CASCADE, blank=True, related_name='barcodes')
	barcode = models.CharField(max_length=50, unique=True, blank=True)


	class Meta:
		indexes = [
			models.Index(fields=['barcode']),
		]


class InitialStock(UpdatedCreatedBy):
	item = models.ForeignKey(Items, related_name='initial_stock', on_delete=models.CASCADE)
	repository = models.ForeignKey(Repositories, on_delete=models.PROTECT)
	quantity = models.DecimalField(max_digits=10, decimal_places=2)
	date = models.DateField(default=now)


	def __str__(self):
		return f'item: {self.item.name}, repository: {self.repository.name}, quantity: {self.quantity}'
