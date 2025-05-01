from rest_framework import serializers
from .models import PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):

    
    class Meta:
        model = PaymentMethod
        fields = '__all__'
        read_only_fields = ['balance']
