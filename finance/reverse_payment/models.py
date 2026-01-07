from django.db import models, transaction
from finance.payment.models import AbstractTransaction
from invoices.purchase.models import PurchaseInvoices
# 
from rest_framework.exceptions import ValidationError
from django.utils import timezone
import uuid



class ReversePayment2(AbstractTransaction):
	purchase = models.ForeignKey(PurchaseInvoices, on_delete=models.PROTECT, related_name='r_payments', blank=True, null=True, help_text="not required, if selected it's effects invoice status.")
	

	class Meta:
		indexes = [
			models.Index(fields=['purchase', 'status']),
			models.Index(fields=['owner']),
			models.Index(fields=['-date']),
			# models.Index(fields=['payment_method']),business_account
		]
		ordering = ['-date']

	def __str__(self):
		return f"{self.payment_ref} - {self.owner.name} - {self.amount} EGP via {self.business_account}"

	def clean(self):
		if self.purchase and self.owner != self.purchase.owner:
			raise ValidationError({
				'detail': 'paid order should be related to the owner...'
			})
		super().clean()

	def save(self, *args, **kwargs):
		from finance.vault_and_methods.services.account_balance_total import AccountBalance

		if not self.payment_ref:
			# Generate payment reference: PAY-20251018-ABC123
			self.payment_ref = f"PAY-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

		self.full_clean()

		with transaction.atomic():
			super().save(*args, **kwargs)

			# validate account balance
			AccountBalance(self.business_account, True).validate_balance()

			if self.purchase:
				self.purchase.save()

	def delete(self, *args, **kwargs):
		with transaction.atomic():
			purchase = self.purchase
			res = super().delete(*args, **kwargs)

			if purchase:
				purchase.save()
			return res
