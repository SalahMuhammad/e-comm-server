from django.db import models
from common.models import UpdatedCreatedBy
from django.utils.timezone import now


class Party(UpdatedCreatedBy):
    name = models.CharField(max_length=255, unique=True)
    detail = models.TextField(max_length=1000, blank=True)
    credit_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)


    class Meta:
        ordering = ['created_at']


    def __str__(self) -> str:
        return self.name 


class InitialCreditBalance(UpdatedCreatedBy):
    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date = models.DateField(default=now)


    class Meta:
        ordering = ['created_at']


    def __str__(self) -> str:
        return f"{self.party.name} - {self.amount}"
