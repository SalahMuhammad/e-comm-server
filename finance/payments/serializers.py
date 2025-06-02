from rest_framework import serializers
from .models import Payment, ExpensePayment


class PaymentSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.name')
    by_name = serializers.ReadOnlyField(source='by.username')
    payment_method_name = serializers.ReadOnlyField(source='payment_method.name')


    class Meta:
        model = Payment
        fields = '__all__'
        extra_kwargs = {
            'owner': {'write_only': True},
            'payment_method': {'write_only': True},
            'by': {'write_only': True},
        }


class ExpensePaymentSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.name')
    by_name = serializers.ReadOnlyField(source='by.username')
    payment_method_name = serializers.ReadOnlyField(source='payment_method.name')


    class Meta:
        model = ExpensePayment
        fields = '__all__'
        extra_kwargs = {
            'owner': {'write_only': True},
            'payment_method': {'write_only': True},
            'by': {'write_only': True},
        }
