from rest_framework import serializers
from .models import TransferItem, Transfer


class ItemTransferSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')
    status = serializers.ChoiceField(choices=['new', 'edited', 'deleted'] , required=True, write_only=True)


    class Meta:
        model = TransferItem
        # fields = '__all__'
        exclude = ['transfer']



class TransferSerializer(serializers.ModelSerializer):
    # items = ItemTransferSerializer(many=True, read_only=True)
    items = ItemTransferSerializer(many=True, required=True)


    def create(self, validated_data):
        if len(validated_data.pop('items', [])) == 0:
            raise serializers.ValidationError({'detail': "items cannot be empty..."})

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if len(validated_data.pop('items', [])) == 0:
            raise serializers.ValidationError({'detail': "items cannot be empty..."})
        
        return super().update(instance, validated_data)
    


    class Meta:
        model = Transfer
        fields = '__all__'
    