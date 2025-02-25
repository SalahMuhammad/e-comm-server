from django.db import models
from common.models import UpdatedCreatedBy


class MoneyVault(UpdatedCreatedBy):
    name = models.CharField(max_length=100)
    # owner = models.ForeignKey('auth.User', related_name='money_vaults', on_delete=models.PROTECT)
    balance = models.DecimalField(default=0, max_digits=20, decimal_places=2)

    def __str__(self):
        return f'{self.name}\ money vault'
