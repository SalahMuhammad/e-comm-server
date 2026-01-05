# utils
from decimal import Decimal
from django.db.models import Sum
# models
from finance.vault_and_methods.models import BusinessAccount
from finance.payment.models import Payment2
from finance.reverse_payment.models import ReversePayment2
from finance.expenses.models import Expense
from finance.transfer.models import MoneyTransfer
from django.db.models import Q
# exceptions
from rest_framework.exceptions import ValidationError



class AccountBalance():
	"""
	AccountBalance class for managing and computing account balance information.
	This class handles account balance retrieval and computation from various transaction types
	including payments, reverse payments, expenses, and money transfers. It supports both
	direct balance retrieval from stored account data and dynamic computation from transaction records.
	Attributes:
		acc (BusinessAccount, optional): The business account instance. Defaults to None.
		is_computed_from_transactions (bool): Flag indicating whether balance should be computed
			from transactions rather than using stored balance. Defaults to False.
	Methods:
		get_account_or_accounts_balance() -> Decimal:
			Returns the account balance. Uses stored balance if available and not forced to compute
			from transactions, otherwise computes balance from transaction records.
		validate_balance() -> None:
			Validates that the account balance is non-negative.
			Raises ValidationError if balance is negative.
		_compute_from_transactions() -> Decimal:
			Computes the account balance by aggregating all relevant transactions:
			adds confirmed payments and incoming transfers, subtracts reverse payments,
			expenses, and outgoing transfers.
		_get_filters(is_for_payment_types=False, is_for_transfer_in=False, is_for_transfer_out=False) -> Q:
			Constructs Django ORM Q filter objects based on transaction type flags.
			Filters by specific account if provided, otherwise by all active accounts.
		_set_account(acc) -> BusinessAccount or None:
			Validates and sets the account instance. Accepts either a BusinessAccount instance
			or a valid account ID. Returns None if validation fails.
		_to_decimal(value) -> Decimal:
			Safely converts a value to Decimal, returning Decimal('0') if value is None.
	"""
	def __init__(self, acc=None, is_computed_from_transactions=False):
		self.acc = self._set_account(acc)
		self.is_computed_from_transactions = is_computed_from_transactions

	def get_account_or_accounts_balance(self):
		if self.acc and self.acc.current_balance is not None and not self.is_computed_from_transactions:
			return Decimal(self.acc.current_balance)
		return self._compute_from_transactions()

	def validate_balance(self, ):
		balance = self.get_account_or_accounts_balance()
		if balance < 0:
			raise ValidationError({
					'detail': f"insufficient funds in: {self.acc.account_name}"
				})

	def _compute_from_transactions(self):
		payment_types_filter = self._get_filters(is_for_payment_types=True)

		# payments
		total = self._to_decimal(
			Payment2.objects.select_related('business_account')\
			.filter(payment_types_filter)\
			.aggregate(total=Sum('amount'))['total']
		)

		# reverse payments
		total -= self._to_decimal(
			ReversePayment2.objects.select_related('business_account')\
			.filter(payment_types_filter)\
			.aggregate(total=Sum('amount'))['total']
		)

		# expensees
		total -= self._to_decimal(
			Expense.objects.select_related('business_account')\
			.filter(payment_types_filter)\
			.aggregate(total=Sum('amount'))['total']
		)

		total += self._to_decimal(
			MoneyTransfer.objects\
			.filter(self._get_filters(is_for_transfer_in=True))\
			.aggregate(total=Sum('amount'))['total'] or self._to_decimal('0')
		)

		total -= self._to_decimal(
			MoneyTransfer.objects\
			.filter(self._get_filters(is_for_transfer_out=True))\
			.aggregate(total=Sum('amount'))['total'] or self._to_decimal('0')
		)
		
		return total

	def _get_filters(self, is_for_payment_types=False, is_for_transfer_in=False, is_for_transfer_out=False):
		if is_for_payment_types:
			confirmed = Q(status=2)
			by_active_account = Q(business_account__is_active=True)
			by_business_account = Q(business_account=self.acc)
			return confirmed & (
				by_business_account if self.acc else by_active_account
			)

		if is_for_transfer_in:
			return Q(to_vault=self.acc) if self.acc else Q(to_vault__is_active=True)
		
		if is_for_transfer_out:
			return Q(from_vault=self.acc) if self.acc else Q(from_vault__is_active=True)

	def _set_account(self, acc):
		if isinstance(acc, BusinessAccount):
			return acc
		
		is_valid_account_id = BusinessAccount.objects.filter(pk=acc)
		if is_valid_account_id.exists():
			return is_valid_account_id[0]
		
		return None
	
	def _to_decimal(self, value):
		return Decimal(value) if value is not None else Decimal('0')

