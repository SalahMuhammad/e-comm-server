from rest_framework import serializers
from .models import Party


class PartySerializers(serializers.ModelSerializer):
    by_username = serializers.ReadOnlyField(source='by.username')


    class Meta:
        model = Party
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
            'credit_balance': {'read_only': True},
        }
