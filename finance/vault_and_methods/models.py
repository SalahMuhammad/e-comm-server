from django.db import models
from common.models import UpdatedCreatedBy



class AccountType(UpdatedCreatedBy):
    name = models.CharField(max_length=100, help_text="mobile wallet, bank, cheque...")


    def __str__(self):
        return f'{self.name}'


class BusinessAccount(UpdatedCreatedBy):
    """Your business accounts where you receive money"""
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT)
    account_name = models.CharField(unique=True, max_length=255, help_text="e.g., 'Main Cash Register', 'Ahmed's Vodafone Cash'")
    
    # Account details
    account_number = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=50, blank=True, help_text="For mobile wallets")
    bank_name = models.CharField(max_length=255, blank=True)

    # Balance tracking (optional)
    current_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)


    class Meta:
        # db_table = 'business_accounts'
        indexes = [
            models.Index(fields=['account_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.account_name} ({self.account_type})"
