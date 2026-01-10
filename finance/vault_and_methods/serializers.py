from rest_framework import serializers
from common.encoder import MixedRadixEncoder
from finance.vault_and_methods.models import AccountType, BusinessAccount


# Serializers
class AccountTypeSerializer(serializers.ModelSerializer):
    """Serializer for account types"""
    hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = AccountType
        fields = '__all__'

    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)


class BusinessAccountSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating business accounts"""
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)
    hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = BusinessAccount
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'account_type_name']

    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)


class BusinessAccountDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving business account details"""
    account_type = AccountTypeSerializer(read_only=True)
    account_type_id = serializers.IntegerField(write_only=True, source='account_type.id')
    
    class Meta:
        model = BusinessAccount
        fields = [
            'id',
            'account_type',
            'account_type_id',
            'account_name',
            'account_number',
            'phone_number',
            'bank_name',
            'current_balance',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']




# ---------------------------------------------------------------------------




class MovementSerializer(serializers.Serializer):
    """Serializer for individual movement records"""
    id = serializers.CharField()
    type = serializers.CharField()
    type_display = serializers.CharField()
    reference = serializers.CharField()
    date = serializers.DateField()
    account_id = serializers.IntegerField()
    account_name = serializers.CharField()
    party = serializers.CharField()
    related_doc = serializers.CharField(allow_null=True)
    amount_in = serializers.DecimalField(max_digits=20, decimal_places=2)
    amount_out = serializers.DecimalField(max_digits=20, decimal_places=2)
    status = serializers.CharField()
    notes = serializers.CharField(allow_blank=True)


class MovementSummarySerializer(serializers.Serializer):
    """Serializer for movement summary statistics"""
    total_in = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_out = serializers.DecimalField(max_digits=20, decimal_places=2)
    net_movement = serializers.DecimalField(max_digits=20, decimal_places=2)
    count = serializers.IntegerField()


class MovementFiltersSerializer(serializers.Serializer):
    """Serializer for applied filters"""
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    account_id = serializers.IntegerField(allow_null=True)
    account_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_null=True
    )
    include_pending = serializers.BooleanField()


class AccountMovementResponseSerializer(serializers.Serializer):
    """Main response serializer"""
    movements = MovementSerializer(many=True)
    summary = MovementSummarySerializer()
    filters = MovementFiltersSerializer()


class BalanceHistoryItemSerializer(serializers.Serializer):
    """Serializer for balance history items"""
    date = serializers.DateTimeField()
    reference = serializers.CharField()
    type = serializers.CharField()
    amount_in = serializers.DecimalField(max_digits=20, decimal_places=2)
    amount_out = serializers.DecimalField(max_digits=20, decimal_places=2)
    balance_before = serializers.DecimalField(max_digits=20, decimal_places=2)
    balance_after = serializers.DecimalField(max_digits=20, decimal_places=2)
    notes = serializers.CharField(allow_blank=True)


class AccountSummarySerializer(serializers.Serializer):
    """Serializer for account summary"""
    account_name = serializers.CharField()
    total_in = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_out = serializers.DecimalField(max_digits=20, decimal_places=2)
    net_movement = serializers.DecimalField(max_digits=20, decimal_places=2)
    transaction_count = serializers.IntegerField()



