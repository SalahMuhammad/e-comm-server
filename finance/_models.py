from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended user model with financial profile"""
    phone = models.CharField(max_length=50, blank=True, null=True)
    
    KYC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='pending')
    kyc_level = models.IntegerField(default=0)
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'





class PaymentMethod(models.Model):
    """User payment methods"""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    
    METHOD_TYPE_CHOICES = [
        ('card', 'Card'),
        ('bank_account', 'Bank Account'),
        ('crypto_wallet', 'Crypto Wallet'),
        ('mobile_money', 'Mobile Money'),
    ]
    method_type = models.CharField(max_length=50, choices=METHOD_TYPE_CHOICES)
    provider = models.CharField(max_length=100, blank=True)
    is_default = models.BooleanField(default=False)
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_methods'
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.method_type}"


class PaymentMethodCard(models.Model):
    """Card payment method details"""
    id = models.BigAutoField(primary_key=True)
    payment_method = models.OneToOneField(PaymentMethod, on_delete=models.CASCADE, related_name='card_details')
    card_holder_name = models.CharField(max_length=255)
    last_four_digits = models.CharField(max_length=4)
    
    CARD_BRAND_CHOICES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
    ]
    card_brand = models.CharField(max_length=50, choices=CARD_BRAND_CHOICES, blank=True)
    expiry_month = models.IntegerField()
    expiry_year = models.IntegerField()
    billing_address_id = models.BigIntegerField(null=True, blank=True)
    token = models.CharField(max_length=255, blank=True)
    fingerprint = models.CharField(max_length=255, unique=True, blank=True)

    class Meta:
        db_table = 'payment_method_cards'

    def __str__(self):
        return f"{self.card_brand} ****{self.last_four_digits}"


class PaymentMethodBankAccount(models.Model):
    """Bank account payment method details"""
    id = models.BigAutoField(primary_key=True)
    payment_method = models.OneToOneField(PaymentMethod, on_delete=models.CASCADE, related_name='bank_account_details')
    account_holder_name = models.CharField(max_length=255)
    account_number_last_four = models.CharField(max_length=4)
    routing_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=255)
    
    ACCOUNT_TYPE_CHOICES = [
        ('checking', 'Checking'),
        ('savings', 'Savings'),
    ]
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES)
    token = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'payment_method_bank_accounts'

    def __str__(self):
        return f"{self.bank_name} ****{self.account_number_last_four}"


class Transaction(models.Model):
    """Main transaction ledger"""
    id = models.BigAutoField(primary_key=True)
    transaction_ref = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    vault = models.ForeignKey(Vault, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
    ]
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0.00000001)])
    currency_code = models.CharField(max_length=3)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('reversed', 'Reversed'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['vault']),
            models.Index(fields=['transaction_ref']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_ref} - {self.transaction_type} - {self.amount} {self.currency_code}"

    def save(self, *args, **kwargs):
        if not self.transaction_ref:
            self.transaction_ref = f"TXN-{uuid.uuid4().hex[:16].upper()}"
        super().save(*args, **kwargs)


class TransactionEntry(models.Model):
    """Double-entry bookkeeping ledger"""
    id = models.BigAutoField(primary_key=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='entries')
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name='ledger_entries')
    
    ENTRY_TYPE_CHOICES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    balance_after = models.DecimalField(max_digits=20, decimal_places=8)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transaction_entries'
        indexes = [
            models.Index(fields=['vault', '-created_at']),
            models.Index(fields=['transaction']),
        ]

    def __str__(self):
        return f"{self.entry_type} - {self.amount} - Vault: {self.vault_id}"


class PaymentTransaction(models.Model):
    """Payment gateway transaction details"""
    id = models.BigAutoField(primary_key=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='payment_details')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    payment_gateway = models.CharField(max_length=100, blank=True)
    gateway_transaction_id = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    fee_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    net_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    three_d_secure_status = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_transactions'

    def __str__(self):
        return f"Payment for {self.transaction.transaction_ref}"


class Transfer(models.Model):
    """Transfer between vaults"""
    id = models.BigAutoField(primary_key=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='transfer_details')
    from_vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name='outgoing_transfers')
    to_vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name='incoming_transfers')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transfers')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transfers')
    
    TRANSFER_TYPE_CHOICES = [
        ('internal', 'Internal'),
        ('external', 'External'),
        ('p2p', 'Peer to Peer'),
    ]
    transfer_type = models.CharField(max_length=50, choices=TRANSFER_TYPE_CHOICES)
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    fee_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transfers'
        indexes = [
            models.Index(fields=['from_vault']),
            models.Index(fields=['to_vault']),
        ]

    def __str__(self):
        return f"Transfer from {self.from_user.username} to {self.to_user.username}"


class BalanceHold(models.Model):
    """Temporary holds on vault balances"""
    id = models.BigAutoField(primary_key=True)
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name='holds')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0.00000001)])
    reason = models.CharField(max_length=255, blank=True)
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('released', 'Released'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'balance_holds'
        indexes = [
            models.Index(fields=['vault', 'status']),
        ]

    def __str__(self):
        return f"Hold on Vault {self.vault_id}: {self.amount}"


class TransactionFee(models.Model):
    """Fees associated with transactions"""
    id = models.BigAutoField(primary_key=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='fees')
    
    FEE_TYPE_CHOICES = [
        ('platform_fee', 'Platform Fee'),
        ('payment_gateway_fee', 'Payment Gateway Fee'),
        ('transfer_fee', 'Transfer Fee'),
        ('conversion_fee', 'Conversion Fee'),
    ]
    fee_type = models.CharField(max_length=50, choices=FEE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency_code = models.CharField(max_length=3)
    percentage = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transaction_fees'

    def __str__(self):
        return f"{self.fee_type}: {self.amount} {self.currency_code}"


class BalanceAuditLog(models.Model):
    """Audit trail for all balance changes"""
    id = models.BigAutoField(primary_key=True)
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name='audit_logs')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    ACTION_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('hold', 'Hold'),
        ('release', 'Release'),
    ]
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    balance_before = models.DecimalField(max_digits=20, decimal_places=8)
    balance_after = models.DecimalField(max_digits=20, decimal_places=8)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'balance_audit_log'
        indexes = [
            models.Index(fields=['vault', '-created_at']),
        ]

    def __str__(self):
        return f"{self.action} on Vault {self.vault_id}: {self.amount}"


class ReconciliationBatch(models.Model):
    """Reconciliation records for balance verification"""
    id = models.BigAutoField(primary_key=True)
    batch_date = models.DateField()
    vault = models.ForeignKey(Vault, on_delete=models.SET_NULL, null=True, blank=True)
    expected_balance = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    actual_balance = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    difference = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    STATUS_CHOICES = [
        ('matched', 'Matched'),
        ('discrepancy', 'Discrepancy'),
        ('investigating', 'Investigating'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'reconciliation_batches'

    def __str__(self):
        return f"Reconciliation {self.batch_date} - {self.status}"
