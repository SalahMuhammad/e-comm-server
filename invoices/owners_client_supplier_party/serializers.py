from rest_framework import serializers
from .models import Owner


class OwnerSerializers(serializers.ModelSerializer):
    by_username = serializers.ReadOnlyField(source='by.username')


    class Meta:
        model = Owner
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
            'credit_balance': {'read_only': True},
        }
