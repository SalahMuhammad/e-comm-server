from rest_framework import serializers
from .models import MoneyVault


class MoneyVaultSerializer(serializers.ModelSerializer):

    
    class Meta:
        model = MoneyVault
        fields = '__all__'
        read_only_fields = ['balance']
