from rest_framework import serializers
from refillable_items_system.models import RefundedRefillableItem, RefilledItem


class RefundedRefillableItemSerializer(serializers.ModelSerializer):
    # item = serializers.PrimaryKeyRelatedField(queryset=Items.objects.all())
    # client_id = serializers.IntegerField()
    item_name = serializers.ReadOnlyField(source='item.name')
    repository_name = serializers.ReadOnlyField(source='repository.name')
    clien_name = serializers.ReadOnlyField(source='client.name')


    class Meta:
        model = RefundedRefillableItem
        fields = '__all__'


class RefilledItemSerializer(serializers.ModelSerializer):
    refilled_item_name = serializers.ReadOnlyField(source='refilled_item.name')
    used_item_name = serializers.ReadOnlyField(source='used_item.item.name')
    employee_name = serializers.ReadOnlyField(source='employee.name')
    repository_name = serializers.ReadOnlyField(source='repository.name')

    class Meta:
        model = RefilledItem
        fields = '__all__'
