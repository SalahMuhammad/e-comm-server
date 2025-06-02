from decimal import ROUND_HALF_UP, Decimal
from rest_framework import serializers
from .models import SalesInvoice, SalesInvoiceItem, ReturnInvoice, ReturnInvoiceItem
from common.utilities import set_request_items_totals
from common.encoder import MixedRadixEncoder



class InvoiceItemSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')
    repository_name = serializers.ReadOnlyField(source='repository.name')


    class Meta:
        model = SalesInvoiceItem
        exclude = ['invoice']


class InvoiceSerializer(serializers.ModelSerializer):
    s_invoice_items = InvoiceItemSerializer(many=True)
    by_username = serializers.ReadOnlyField(source='by.username')
    owner_name = serializers.ReadOnlyField(source='owner.name')
    hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = SalesInvoice
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
        }


    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)
    
    def validate_s_invoice_items(self, value):
        if not value:
            raise serializers.ValidationError("Items cannot be empty.")
        
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('s_invoice_items')
        edited_items, sum_items_total = set_request_items_totals(items_data)
        validated_data['total_amount'] = Decimal(str(sum_items_total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        invoice = super().create(validated_data)

        for item_data in edited_items:
            SalesInvoiceItem.objects.create(
                invoice=invoice,
                **item_data
            )

        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('s_invoice_items')


        # for item_data in edited_items:
        #     SalesInvoiceItem.objects.create(
        #         invoice=invoice,
        #         **item_data
        #     )
        
        return super().update(instance, validated_data)
    

class ReturnInvoiceItemSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')
    repository_name = serializers.ReadOnlyField(source='repository.name')


    class Meta:
        model = ReturnInvoiceItem
        exclude = ['invoice']


class ReturnInvoiceSerializer(serializers.ModelSerializer):
    s_invoice_items = ReturnInvoiceItemSerializer(many=True)
    by_username = serializers.ReadOnlyField(source='by.username')
    owner_name = serializers.ReadOnlyField(source='owner.name')
    hashed_id = serializers.SerializerMethodField()
    original_invoice_hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = ReturnInvoice
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
        }


    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)
    
    def get_original_invoice_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.original_invoice.id)

    def validate_s_invoice_items(self, value):
        if not value:
            raise serializers.ValidationError("Items cannot be empty.")

        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('s_invoice_items')
        edited_items, sum_items_total = set_request_items_totals(items_data)
        validated_data['total_amount'] = Decimal(str(sum_items_total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        invoice = super().create(validated_data)

        original_invoice_items = {i.item.id: i.quantity for i in invoice.original_invoice.s_invoice_items.all()}
        for item_data in edited_items:
            rii = ReturnInvoiceItem.objects.create(
                invoice=invoice,
                **item_data
            )

            # i assume that invoice's item is not duplicated in the original invoice
            if not original_invoice_items.get(rii.item.id, None):
                raise serializers.ValidationError({f"Item {rii.item.name} not found in original invoice items."})
            if rii.quantity > original_invoice_items[rii.item.id]:
                raise serializers.ValidationError({f"Quantity of item {rii.item.name} cannot be greater than the original invoice quantity."})

        return invoice