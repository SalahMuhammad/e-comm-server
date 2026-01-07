from rest_framework import serializers
from .models import Payment2
from common.encoder import MixedRadixEncoder



class PaymentSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.name')
    created_by = serializers.ReadOnlyField(source='created_by.username')
    last_updated_by = serializers.ReadOnlyField(source='last_updated_by.username')
    ref_order_total_amount = serializers.ReadOnlyField(source='sale.total_amount')
    # payment_method_name = serializers.ReadOnlyField(source='business_account.account_name')
    payment_method_name = serializers.SerializerMethodField()
    related_order_ref = serializers.SerializerMethodField()
    hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = Payment2
        fields = '__all__'
        extra_kwargs = {
            'payment_ref': {'required': False, 'allow_blank': True},
        }


    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id) if obj.id else ' - '
    
    def get_related_order_ref(self, obj):
        if obj.sale:
            return MixedRadixEncoder().encode(obj.sale.id)
        else: 
            return None
    
    def get_payment_method_name(self, obj):
        return f'{obj.business_account.account_type} - {obj.business_account.account_name}'
