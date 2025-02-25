from django.db import models
from items.models import Items
from repositories.models import Repositories
from rest_framework import serializers
from common.models import UpdatedCreatedBy


class Transfer(UpdatedCreatedBy):
	fromm = models.ForeignKey(Repositories, on_delete=models.PROTECT, related_name='fromm')
	too = models.ForeignKey(Repositories, on_delete=models.PROTECT, related_name='too')
	date = models.DateField(null=False)


	def clean(self):
		if self.fromm == self.too:
			raise serializers.ValidationError({'detail': "The 'from' and 'to' repositories cannot be the same."})
		
	def save(self, *args, **kwargs):
		# is_new = self.pk is None
		# super().save(*args, **kwargs)
        
		# if is_new:
		# 	for item in self.items.all():
		# 		stock_from = Stock.objects.get(
		# 			repository=self.fromm,
		# 			item=item.item
		# 		)
		# 		stock_to, created = Stock.objects.get_or_create(
		# 			repository=self.too,
		# 			item=item.item
		# 		)




		self.full_clean()
		return super().save(*args, **kwargs)
	

	class Meta:
		ordering = ['-updated_at']


class TransferItem(models.Model):
	transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name='items')
	item = models.ForeignKey(Items, on_delete=models.PROTECT)
	quantity = models.PositiveSmallIntegerField(default=1)

	
	# def save(self, *args, **kwargs):
	# 	a = self.items.fromm
	# 	b = self.items.too


		# stock_from = Stock.objects.get(repository=a, item=b)
		# stock_to, created = Stock.objects.get_or_create(repository=self.items.too, item=self.item)
		# item = instance.items.get(item=item_id)
		# stock_from.adjust_stock(item.quantity)
		# stock_to.adjust_stock(-item.quantity)


		# super().save(*args, **kwargs)

