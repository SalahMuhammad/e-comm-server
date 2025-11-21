from rest_framework import serializers



# Serializers
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
