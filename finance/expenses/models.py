from django.db import models, transaction
from common.models import UpdatedCreatedByV2
# 
from finance.vault_and_methods.models import BusinessAccount
from django.core.validators import MinValueValidator
from datetime import date



class Category(UpdatedCreatedByV2):
	name = models.CharField(max_length=50, unique=True)
	description = models.TextField(max_length=200, blank=True, null=True)

	def __str__(self):
		return f'{self.name} ({self.description})'


class Expense(UpdatedCreatedByV2):
	status_choices = (
		('1', 'Pending'),
		('2', 'Confirmed'),
		('3', 'Rejected'),
		('4', 'Reimbursed')
	)

	category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.PROTECT, related_name='category')
	business_account = models.ForeignKey(BusinessAccount, on_delete=models.PROTECT)
	amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0.01)])
	date = models.DateField(default=date.today)
	status = models.CharField(max_length=2, choices=status_choices, default='1')
	image = models.ImageField(upload_to='expenses-docs/', null=True, blank=True, help_text="Screenshot or proof")
	notes = models.TextField(max_length=500, blank=True)


	class Meta:
		ordering = ['-date']

	def __str__(self):
		return f"{self.category} - {self.status} - {self.amount} EGP via {self.business_account.account_name}"

	def save(self, *args, **kwargs):
		from finance.vault_and_methods.services.account_balance_total import AccountBalance

		with transaction.atomic():
			super().save(*args, **kwargs)

			# validate account balance
			AccountBalance(self.business_account, True).validate_balance()
