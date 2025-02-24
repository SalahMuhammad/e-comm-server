from rest_framework import serializers
from .models import Invoice, InvoiceItem
from django.db import transaction
from owners.models import Owner
from .utilities import compare_items
from items.models import Stock
from django.db.models import Q


class InvoiceItemSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')


    class Meta:
        model = InvoiceItem
        fields = ['id', 'item', 'item_name', 'quantity', 'unit_price']
        # exclude = ['invoice']


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
    items = InvoiceItemSerializer(many=True, required=False)
    by_username = serializers.ReadOnlyField(source='by.username')
    repository_name = serializers.ReadOnlyField(source='repository.name')
    owner_name = serializers.ReadOnlyField(source='owner.name')


    class Meta: 
        model = Invoice
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
            'repository': {'write_only': True},
            'owner': {'write_only': True},
        }


    def __init__(self, *args, **kwargs):
        fieldss = kwargs.pop('fieldss', None)
        super(InvoiceSerializer, self).__init__(*args, **kwargs)
        if fieldss:
            allowed = set(fieldss.split(','))
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def validate_items(self, value):
        item_ids = [item['item'].id for item in value]
        if len(item_ids) != len(set(item_ids)):
            raise serializers.ValidationError("Duplicate items are not allowed in the invoice...😵")
        return value

    def create(self, validated_data):
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

    def update(self, instance, validated_data):
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
