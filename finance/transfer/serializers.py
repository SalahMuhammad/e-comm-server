from rest_framework import serializers
from .models import MoneyTransfer
from common.encoder import MixedRadixEncoder



class TransferSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    last_updated_by = serializers.ReadOnlyField(source='last_updated_by.username')
    from_vault_name = serializers.SerializerMethodField()
    to_vault_name = serializers.SerializerMethodField()
    hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = MoneyTransfer
        fields = '__all__'

    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id) if obj.id else ' - '
    
    def get_from_vault_name(self, obj):
        return f'{obj.from_vault.account_type} - {obj.from_vault.account_name}'
    
    def get_to_vault_name(self, obj):
        return f'{obj.to_vault.account_type} - {obj.to_vault.account_name}'
