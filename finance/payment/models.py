from django.db import models, transaction
from common.models import UpdatedCreatedByV2
from finance.vault_and_methods.models import BusinessAccount
from invoices.buyer_supplier_party.models import Party
from invoices.sales.models import SalesInvoice
# 
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
from rest_framework.exceptions import ValidationError
from datetime import date
from decimal import Decimal



class AbstractTransaction(UpdatedCreatedByV2):
	"""
	Payment2
	---------
	Model representing a customer payment record. Used to record receipts made to the business
	(e.g., cash, mobile wallet, bank transfer). Stores who paid, where the funds were received,
	optional payment/proof details, and a status used to control reconciliation.
	Key behavior
	- A unique payment reference (payment_ref) is required; if not supplied it is automatically
		generated on save in the form "PAY-YYYYMMDD-XXXXXXXX" where XXXXXXXX is an 8-character
		uppercase hex segment derived from a UUID.
	- When a payment's status is 'confirmed', the model calls update_sale_payment() after saving
		to recompute the related Sale.amount_paid as the sum of confirmed payments.
	- amount is validated to be >= 0.01.
	- The model keeps an audit via UpdatedCreatedBy (inherited).
	Fields (summary)
	- payment_ref (str): Unique payment reference. Help text: "Unique payment reference used on
		receipts and for reconciliation. If not provided it will be auto-generated in the format
		PAY-YYYYMMDD-<8-CHAR-ID> (e.g. PAY-20251018-ABC12345)."
	- owner (ForeignKey -> Party): Payer/party who made the payment (protected on delete).
	- amount (Decimal): Amount paid; validated to a minimum of 0.01.
	- transaction_id (str, optional): Transaction identifier for bank or instant payment methods.
	- sender_phone (str, optional): Phone number for mobile wallet payments.
	- sender_name (str, optional): Sender name for bank transfers.
	- bank_name (str, optional): Bank name for bank transfers.
	- business_account (ForeignKey -> BusinessAccount): Business account that received the funds.
	- received_by (str, optional): Staff member who physically received cash (if applicable).
	- payment_date (datetime): When the payment was made / recorded (defaults to now).
	- status (str): One of 'pending', 'confirmed', 'rejected'. Default is 'confirmed' in the
		current implementation. Semantics:
			- pending: awaiting confirmation/reconciliation
			- confirmed: funds reconciled/accepted (triggers sale amount update)
			- rejected: payment not accepted (does not contribute to sale totals)
	- notes (text, optional): Free text for receipt number, screenshot reference, etc.
	- payment_proof (Image, optional): Attached screenshot/receipt image.
	Meta / indexing
	- db_table 'payments'
	- Indexes on sale, owner, payment_date (descending) and payment_method (note: some code
		comments indicate payment_method and sale fields may be optional/commented out).
	- Default ordering is by -payment_date.
	Important implementation notes and caveats
	- The save() method auto-generates payment_ref when missing and triggers update_sale_payment()
		when status == 'confirmed'. Because update_sale_payment() aggregates confirmed payments from
		the related sale, updates should ideally be executed within a transaction or use
		select_for_update to avoid race conditions when multiple payments are confirmed concurrently.
	- The __str__ representation references payment_method and owner.name; ensure those attributes
		exist in the runtime model configuration to avoid AttributeError if fields are removed or
		commented out.
	- Some meta indexes reference fields that are commented out in the current code snapshot
		(e.g., sale, payment_method). If those fields remain absent, remove or update the indexes
		to avoid migration errors.
	Usage
	- Create a Payment2 with owner, amount and business_account at minimum. The payment_ref will
		be generated automatically if omitted. Change status to 'confirmed' to include the amount
		in the related Sale.amount_paid aggregation.
	See also
	- update_sale_payment(): recomputes and persists the related Sale.amount_paid by summing all
		confirmed payments attached to that sale.
	"""
	"""Customer payments - can be cash, mobile wallet, or bank transfer"""
	payment_ref = models.CharField(max_length=100, unique=True)
	# sale = models.ForeignKey(SalesInvoice, on_delete=models.PROTECT, related_name='payments', blank=True, null=True, help_text="not required, if selected it's effects invoice status.")
	owner = models.ForeignKey(Party, on_delete=models.PROTECT)
	
	amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
	
	# PAYMENT_METHOD_CHOICES = [
	#     ('cash', 'Cash'),
	#     ('instapay', 'InstaPay'),
	#     ('vodafone_cash', 'Vodafone Cash'),
	#     ('bank_transfer', 'Bank Transfer'),
	#     ('other', 'Other'),
	# ]
	# payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
	
	# Payment details (optional based on method)
	transaction_id = models.CharField(max_length=255, blank=True, help_text="For InstaPay/Bank Transfer")
	sender_phone = models.CharField(max_length=50, blank=True, help_text="For mobile wallets")
	sender_name = models.CharField(max_length=255, blank=True, help_text="For bank transfers")
	bank_name = models.CharField(max_length=255, blank=True, help_text="For bank transfers")
	
	# Link to business account where money was received
	business_account = models.ForeignKey(
		BusinessAccount, 
		on_delete=models.PROTECT, 
		# related_name='received_payments',
		help_text="Which business account received this payment"
	)
	
	# Who physically received the payment (for cash payments)
	received_by = models.CharField(max_length=255, blank=True, help_text="Staff member name (for cash payments)")
	
	date = models.DateField(default=date.today)
	
	STATUS_CHOICES = [
		('1', 'Pending'),
		('2', 'Confirmed'),
		('3', 'Rejected'),
		('4', 'Reimbursed'),
	]
	status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='1')
	
	notes = models.TextField(blank=True, help_text="Receipt number, screenshot reference, etc.")
	
	# Optional: attach payment proof
	payment_proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True, help_text="Screenshot or receipt")
	
	
	class Meta:
		abstract = True

	def __str__(self):
		return f"{self.payment_ref} - {self.owner.name} - {self.amount} EGP via {self.business_account}"

	# def save(self, *args, **kwargs):
	#     if not self.payment_ref:
	#         # Generate payment reference: PAY-20251018-ABC123
	#         self.payment_ref = f"PAY-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
		
	#     super().save(*args, **kwargs)
		
		# is_new = self.pk is None

		# if self.sale:
		#     if self.owner != self.sale.owner:
		#         raise ValidationError("Payment owner must match the sale owner")

		# with transaction.atomic():
		#     super().save(*args, **kwargs)
		
		#     # Update the sale's amount_paid when payment is confirmed
		#     # if self.status == 'confirmed':
		#     self.sale.save()
	
	# def update_sale_payment(self):
	#     """Update the sale's total amount paid"""
	#     total_paid = self.sale.payments.filter(
	#         status='confirmed'
	#     ).aggregate(
	#         total=models.Sum('amount')
	#     )['total'] or Decimal('0')
		
	#     self.sale.remaining_balance = self.sale.total_amount - total_paid
	#     self.sale.save()

	# def delete(self, *args, **kwargs):
	#     with transaction.atomic():
	#         sale = self.sale
	#         res = super().delete(*args, **kwargs)
	#         sale.save()
	#         return res



class Payment2(AbstractTransaction):
	sale = models.ForeignKey(SalesInvoice, on_delete=models.PROTECT, related_name='payments', blank=True, null=True, help_text="not required, if selected it's effects invoice status.")


	class Meta:
		db_table = 'payment'
		indexes = [
			models.Index(fields=['sale', 'status']),
			models.Index(fields=['owner']),
			models.Index(fields=['-date']),
			# models.Index(fields=['payment_method']),business_account
		]
		ordering = ['-date']
 
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._initial_data = self.__dict__.copy()
 
	def __str__(self):
		return f"{self.payment_ref} - {self.owner.name} - {self.amount} EGP via {self.business_account}"

	def clean(self):
		if self.sale and self.owner != self.sale.owner:
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
			if not self._initial_data['business_account_id'] == self.business_account.id:
				AccountBalance(self._initial_data['business_account_id'], True).validate_balance()

			if self.sale:
				self.sale.save()

	def delete(self, *args, **kwargs):
		from finance.vault_and_methods.services.account_balance_total import AccountBalance

		with transaction.atomic():
			sale = self.sale
			res = super().delete(*args, **kwargs)

			# validate account balance
			AccountBalance(self.business_account, True).validate_balance()

			if sale:
				sale.save()
			return res
