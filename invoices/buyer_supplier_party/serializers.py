from rest_framework import serializers
from .models import Party, InitialCreditBalance


class PartySerializers(serializers.ModelSerializer):
    by_username = serializers.ReadOnlyField(source='by.username')


    class Meta:
        model = Party
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
            'credit_balance': {'read_only': True},
        }


class InitialCreditBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = InitialCreditBalance
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
            'owner': {'write_only': True},
        }
