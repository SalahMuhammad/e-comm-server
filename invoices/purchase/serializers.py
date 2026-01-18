from decimal import ROUND_HALF_UP, Decimal
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
# models
from finance.reverse_payment.models import ReversePayment2
from .models import PurchaseInvoices, PurchaseInvoiceItems
# 
from common.utilities import set_request_items_totals
from common.encoder import MixedRadixEncoder



class InvoiceItemsSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')
    repository_name = serializers.ReadOnlyField(source='repository.name')


    class Meta:
        model = PurchaseInvoiceItems
        exclude = ['invoice']


# class TaggedObjectRelatedField(serializers.RelatedField):
#     def to_representation(self, value):
#         if isinstance(value, Supplier):
#             serializer = SupplierSerializers(value)
#         elif isinstance(value, CustomerSerializers):
#             serializer = CustomerSerializers(value)
#         else:
#             raise Exception('Unexpected type of tagged object')

#         return serializer.data


class InvoiceSerializer(serializers.ModelSerializer):
    p_invoice_items = InvoiceItemsSerializer(many=True)
    by_username = serializers.ReadOnlyField(source='by.username')
    owner_name = serializers.ReadOnlyField(source='owner.name')
    hashed_id = serializers.SerializerMethodField()
    # payment info
    payment_amount = serializers.DecimalField(max_digits=20, decimal_places=2, write_only=True, allow_null=True, required=False)
    payment_account = serializers.CharField(write_only=True, allow_null=True, allow_blank=True, required=False)
    payment_notes = serializers.CharField(write_only=True, allow_null=True, allow_blank=True, required=False)


    class Meta:
        model = PurchaseInvoices
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
        }


    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)

    def validate_p_invoice_items(self, value):
        if not value:
            raise serializers.ValidationError("Items cannot be empty.")

        return value

    def create(self, validated_data):
        items_data = validated_data.pop('p_invoice_items')
        edited_items, sum_items_total = set_request_items_totals(items_data)
        validated_data['total_amount'] = Decimal(str(sum_items_total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        # related to payment info
        p_amount = validated_data.pop('payment_amount', None)
        p_account = validated_data.pop('payment_account', None)
        p_notes = validated_data.pop('payment_notes', None)
        
        invoice = super().create(validated_data)

        for item_data in edited_items:
            PurchaseInvoiceItems.objects.create(
                invoice=invoice,
                **item_data
            )

        if p_account:
            try:
                ReversePayment2.objects.create(
                    business_account_id=MixedRadixEncoder().decode(p_account),
                    owner=invoice.owner,
                    purchase_id=invoice.id,
                    amount=p_amount,
                    status=2,
                    notes=p_notes,
                    created_by=invoice.by,
                    last_updated_by=invoice.by
                )
            except Exception as e:
                raise ValidationError(e)

        return invoice

    def update(self, instance, validated_data):
        validated_data.pop('p_invoice_items')
        validated_data.pop('payment_amount', None)
        validated_data.pop('payment_account', None)
        validated_data.pop('payment_notes', None)


        # for item_data in edited_items:
        #     SalesInvoiceItem.objects.create(
        #         invoice=invoice,
        #         **item_data
        #     )
        
        return super().update(instance, validated_data)
    


    # def __init__(self, *args, **kwargs):
    #     fieldss = kwargs.pop('fieldss', None)
    #     super(InvoiceSerializer, self).__init__(*args, **kwargs)
    #     if fieldss:
    #         allowed = set(fieldss.split(','))
    #         existing = set(self.fields.keys())
    #         for field_name in existing - allowed:
    #             self.fields.pop(field_name)


    # def validate_items(self, value):
    #     for i, item in enumerate(value):
    #         quantity = item.get('quantity', 1)
    #         unit_price = item['unit_price'] 
    #         tax_rate = item.get('tax_rate', 0)
    #         discount = item.get('discount', 0)
            
    #         item['total'] = quantity * unit_price + tax_rate - discount
        
    #     # item_ids = [item['item'].id for item in value]
    #     # if len(item_ids) != len(set(item_ids)):
    #     #     raise serializers.ValidationError("Duplicate items are not allowed in the invoice...😵")
    #     # return value
    #     return value
    
    # def validate(self, data):
    #     items = data.get('items', [])
        
    #     # Calculate total from all items
    #     total_amount = sum(item.get('total', 0) for item in items)
        
    #     # Set total_amount in the data
    #     data['total_amount'] = total_amount
        
    #     # Call the parent's validate method
    #     data = super().validate(data)
        
    #     return data
        

    # def create(self, validated_data):
        invoice_items_data = validated_data.pop('items', [])
        is_purchase_invoice = True if validated_data.get('is_purchase_invoice', 1) else False


        if validated_data.get('paid', None) != None and not validated_data.get('owner', None):
            raise serializers.ValidationError({'detail': 'The owner should not be anonymous in case of deferred payment...😵'})

        if not invoice_items_data:
            raise serializers.ValidationError({'detail': 'invoice_items field is required, and can not be an empty array.'})

        with transaction.atomic():
            validated_data['paid'] = validated_data.get('paid', sum([v.get('quantity', 1) * v['unit_price'] for v in invoice_items_data]))
            invoice = super().create(validated_data)
            a = 1 if is_purchase_invoice == True else -1
            for item in invoice_items_data:
                new_item = invoice.items.create(**item)
                stock, created = Stock.objects.get_or_create(repository=validated_data['repository'], item=new_item.item)
                stock.adjust_stock(new_item.quantity * a)
                
        return invoice

    # def update(self, instance, validated_data):
        invoice_items_data = validated_data.pop('items', [])
        is_purchase_invoice = True if validated_data.get('is_purchase_invoice', instance.is_purchase_invoice) else False
        qty_times = 1 if is_purchase_invoice else -1
        repository = validated_data.get('repository', instance.repository)


        if is_purchase_invoice != instance.is_purchase_invoice and not invoice_items_data:
            raise serializers.ValidationError({'detail': 'Can not update invoice type without sending it\'s items...😵'})

        if validated_data.get('paid', instance.paid) != None and validated_data.get('object_id', instance.owner) == None:
            raise serializers.ValidationError({'detail': 'The owner should not be anonymous in case of deferred payment...😵'})

        if repository != instance.repository and invoice_items_data == []:
            raise serializers.ValidationError({'detail': f'repository can\'t be updated without updating items too...'})
        
        with transaction.atomic():
            if invoice_items_data:
                items_to_remove = compare_items(instance.items.all(), invoice_items_data)

                # items to remove
                if items_to_remove:
                    items = instance.items.filter(item_id__in=items_to_remove)
                    for item in items:
                        a = 1 if is_purchase_invoice else -1
                        stock = Stock.objects.get(repository=instance.repository, item=item.item)
                        stock.adjust_stock(-item.quantity * a)
                        item.delete()

                for item_data in invoice_items_data:
                    new_quantity = item_data.get('quantity', 1)
                    item, created = instance.items.get_or_create(
                        item=item_data['item'],
                        defaults={
                            'quantity': new_quantity,
                            'unit_price': item_data['unit_price']
                        }
                    )

                    if created:
                        stock, created = Stock.objects.get_or_create(repository=repository, item=item.item)
                        stock.adjust_stock(item.quantity * qty_times)
                    else:
                        old_quantity = item.quantity
                        item.quantity = new_quantity
                        item.save()
                        if repository == instance.repository:
                            a = [item.quantity, old_quantity]
                            quantity_diff = max(a) - min(a)
                            quantity_diff *= 1 if old_quantity < item.quantity else -1
                            aa = quantity_diff if is_purchase_invoice == instance.is_purchase_invoice else item.quantity+old_quantity

                            stock, created = Stock.objects.get_or_create(repository=repository, item=item.item)
                            stock.adjust_stock(aa * qty_times)
                        else:
                            b = -1 if instance.is_purchase_invoice else 1
                            stock, created = Stock.objects.get_or_create(repository=instance.repository, item=item.item)
                            stock.adjust_stock(old_quantity * b)
                            stock, created = Stock.objects.get_or_create(repository=repository, item=item.item)
                            stock.adjust_stock(item.quantity * qty_times)
            
            if invoice_items_data and not validated_data.get('paid', None):
                paid = [v.get('quantity', 1) * v['unit_price'] for v in invoice_items_data]
                validated_data['paid'] = validated_data.get('paid', sum(paid))
            super().update(instance, validated_data)
            
        return instance
