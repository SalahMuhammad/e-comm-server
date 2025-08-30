from rest_framework import serializers
from refillable_items_system.models import RefundedRefillableItem, RefilledItem, ItemTransformer, OreItem


class RefundedRefillableItemSerializer(serializers.ModelSerializer):
    # item = serializers.PrimaryKeyRelatedField(queryset=Items.objects.all())
    # client_id = serializers.IntegerField()
    item_name = serializers.ReadOnlyField(source='item.name')
    repository_name = serializers.ReadOnlyField(source='repository.name')
    owner_name = serializers.ReadOnlyField(source='owner.name')


    class Meta:
        model = RefundedRefillableItem
        fields = '__all__'


class RefilledItemSerializer(serializers.ModelSerializer):
    refilled_item_name = serializers.ReadOnlyField(source='refilled_item.name')
    used_item_name = serializers.ReadOnlyField(source='used_item.item.name')
    employee_name = serializers.ReadOnlyField(source='employee.name')
    repository_name = serializers.ReadOnlyField(source='repository.name')
    by_username = serializers.ReadOnlyField(source='by.username')

    class Meta:
        model = RefilledItem
        fields = '__all__'


class ItemTransformerSerializer(serializers.ModelSerializer):
    empty = serializers.ReadOnlyField(source='item.name')
    filled = serializers.ReadOnlyField(source='transform.name')


    class Meta: 
        model = ItemTransformer
        fields = '__all__'


class OreItemSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')


    class Meta:
        model = OreItem
        fields = '__all__'
    

class CustomDataSerializer(serializers.Serializer):
    date = serializers.DateField()
    qty = serializers.IntegerField()
    description = serializers.CharField(max_length=100)
    remaining = serializers.IntegerField()
