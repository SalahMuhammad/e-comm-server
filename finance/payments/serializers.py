from rest_framework import serializers
from .models import Payment, ExpensePayment
from common.encoder import MixedRadixEncoder


class PaymentSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.name')
    by_username = serializers.ReadOnlyField(source='by.username')
    payment_method_name = serializers.ReadOnlyField(source='payment_method.name')
    hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = Payment
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
        }

    
    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)


class ExpensePaymentSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.name')
    by_username = serializers.ReadOnlyField(source='by.username')
    payment_method_name = serializers.ReadOnlyField(source='payment_method.name')
    hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = ExpensePayment
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
        }

    
    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)
