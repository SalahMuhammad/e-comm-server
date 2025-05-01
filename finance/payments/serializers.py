from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.name')


    class Meta:
        model = Payment
        fields = '__all__'
