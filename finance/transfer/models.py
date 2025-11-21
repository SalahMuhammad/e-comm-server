from django.utils import timezone
from django.db import models
from common.models import UpdatedCreatedByV2
from finance.vault_and_methods.models import BusinessAccount
from django.core.validators import MinValueValidator
from datetime import date



class MoneyTransfer(UpdatedCreatedByV2):
    """Transfer between vaults"""
    # transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='transfer_details')
    from_vault = models.ForeignKey(BusinessAccount, on_delete=models.CASCADE, related_name='outgoing_transfers')
    to_vault = models.ForeignKey(BusinessAccount, on_delete=models.CASCADE, related_name='incoming_transfers')
    # from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transfers')
    # to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transfers')
    amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0.01)])
    TRANSFER_TYPE_CHOICES = [
        ('internal', 'Internal'),
        ('external', 'External'),
        ('p2p', 'Peer to Peer'),
    ]
    transfer_type = models.CharField(max_length=50, choices=TRANSFER_TYPE_CHOICES, default='internal')
    # exchange_rate = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    # fee_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)
    proof = models.ImageField(upload_to='transfer_proofs/', null=True, blank=True, help_text="Screenshot or receipt")



    class Meta:
        db_table = 'transfers'
        indexes = [
            models.Index(fields=['from_vault']),
            models.Index(fields=['to_vault']),
        ]

    def __str__(self):
        return f"Transfer from {self.from_vault.account_name} to {self.to_vault.account_name}"
