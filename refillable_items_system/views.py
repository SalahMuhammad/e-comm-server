from decimal import Decimal
from rest_framework import generics
from rest_framework.response import Response

from invoices.sales.models import SalesInvoice, ReturnInvoice
from refillable_items_system.models import ItemTransformer, OreItem, RefillableItemsInitialStockClientHas, RefundedRefillableItem, RefilledItem
from items.models import Items, Stock
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from .serializers import RefundedRefillableItemSerializer, RefilledItemSerializer, ItemTransformerSerializer, OreItemSerializer
from django.db import transaction
from common.utilities import get_pagination_class
from invoices.buyer_supplier_party.models import Party
from rest_framework.decorators import api_view



from django.db.models import Sum
def calculateRefillableItemsClientHas(client_id):
    invoices = SalesInvoice.objects.filter(owner_id=client_id)
    refillable_items = Items.objects.filter(is_refillable=True)

    refillable_items_quantities = {}
    for item in refillable_items:
        item_visavis = ItemTransformer.objects.filter(
            transform=item
        ).first()
        initial_stock_client_has = RefillableItemsInitialStockClientHas.objects.filter(
            owner_id=client_id, 
            item=item_visavis.item
        ).aggregate(Sum('quantity'))
        key = item_visavis.item.name

        refunded = RefundedRefillableItem.objects.filter(owner_id=client_id, item=item_visavis.item).aggregate(Sum('quantity'))

        for invoice in invoices:
            q = 0
            ri = None

            if invoice.notes.__contains__('#بدون حساب الفارغ'):
                continue

            if invoice.repository_permit:
                filled_item_qty = invoice.s_invoice_items.filter(item=item_visavis.transform).aggregate(Sum('quantity'))
                ri = ReturnInvoice.objects.filter(
                    original_invoice_id=invoice.id
                ).first()

                if ri:
                    q = ri.s_invoice_items.filter(item=item_visavis.transform).aggregate(Sum('quantity'))

                # idle_item_qty_taken = invoice.s_invoice_items.filter(item=item_visavis.item).aggregate(Sum('quantity'))
                refillable_items_quantities[key] = refillable_items_quantities.get(key, 0)
                refillable_items_quantities[key] += (filled_item_qty['quantity__sum'] or 0)
                if q:
                    refillable_items_quantities[key] -= (q['quantity__sum'] or 0)

                # refillable_items_quantities[key] += (idle_item_qty_taken['quantity__sum'] or 0)

        refillable_items_quantities[key] = refillable_items_quantities.get(key, 0) + (initial_stock_client_has['quantity__sum'] or 0) - (refunded['quantity__sum'] or 0)

        if refillable_items_quantities[key] == 0:
            del refillable_items_quantities[key]
    
    return refillable_items_quantities


@api_view(['GET'])
def ownersHasRefillableItems(request, *args, **kwargs):
    owners = Party.objects.all()

    list = []
    for owner in owners:
        a = calculateRefillableItemsClientHas(client_id=owner.id)

        if a:
            list.append({
                "id": owner.id,
                "owner": owner.name,
                "cylinders": a
            })
    
    return Response({
        "data": list
    })


class ListCreateRefundedRefillableItemsView(
    ListModelMixin,
    CreateModelMixin,
    generics.GenericAPIView
):
    serializer_class = RefundedRefillableItemSerializer
    queryset = RefundedRefillableItem.objects.all()
    
    def get_queryset(self):
        queryset = self.queryset

        name_param = self.request.query_params.get('ownerid')
        if name_param:
            return queryset.filter(owner_id=name_param)
        
        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            stock, cretated = Stock.objects.get_or_create(
                repository_id=serializer.data['repository'],
                item_id=serializer.data['item']
            )
            stock.adjust_stock(Decimal(serializer.data['quantity']))

            return Response(serializer.data, status=201)


class DetialRefundedRefillableItemsView(
    RetrieveModelMixin,
    DestroyModelMixin,
    generics.GenericAPIView
):
    queryset = RefundedRefillableItem.objects.all()
    serializer_class = RefundedRefillableItemSerializer


    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        with transaction.atomic():
            stock = Stock.objects.get(
                repository=instance.repository,
                item=instance.item
            )
            stock.adjust_stock(- Decimal(instance.quantity))

            return super().destroy(request, *args, **kwargs)




class ListCreateRefilledItemsView(
    ListModelMixin,
    CreateModelMixin,
    generics.GenericAPIView
):
    queryset = RefilledItem.objects.all()
    serializer_class = RefilledItemSerializer


    def get_queryset(self):
        self.pagination_class = get_pagination_class(self)
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        if from_date and to_date:
            return self.queryset.filter(date__range=(from_date, to_date))
        
        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            item_transofrmer = ItemTransformer.objects.filter(item=serializer.data['refilled_item']).first()

            filled_stock, cretated = Stock.objects.get_or_create(
                repository_id=serializer.data['repository'],
                item=item_transofrmer.transform
            )
            filled_stock.adjust_stock(Decimal(serializer.data['refilled_quantity']))

            refilled_stock, cretated = Stock.objects.get_or_create(
                repository_id=serializer.data['repository'],
                item=item_transofrmer.item
            )
            refilled_stock.adjust_stock(- Decimal(serializer.data['refilled_quantity']))

            used_stock, cretated = Stock.objects.get_or_create(
                repository_id=serializer.data['repository'],
                item=OreItem.objects.get(id=serializer.data['used_item']).item
            )
            used_stock.adjust_stock(- Decimal(serializer.data['used_quantity']))
            
            return Response(serializer.data, status=201)


class DetialRefilledItemsView(
    RetrieveModelMixin,
    DestroyModelMixin,
    generics.GenericAPIView
):
    queryset = RefilledItem.objects.all()
    serializer_class = RefilledItemSerializer


    def get_queryset(self):
        queryset = self.queryset

        name_param = self.request.query_params.get('employee')
        if name_param:
            return queryset.filter(employee_id=name_param)
        
        return self.queryset
    

    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        with transaction.atomic():
            item_transofrmer = ItemTransformer.objects.get(item=instance.refilled_item)

            filled_stock, cretated = Stock.objects.get_or_create(
                repository=instance.repository,
                item=item_transofrmer.transform
            )
            filled_stock.adjust_stock(- Decimal(instance.refilled_quantity))

            refilled_stock, cretated = Stock.objects.get_or_create(
                repository=instance.repository,
                item=item_transofrmer.item
            )
            refilled_stock.adjust_stock(Decimal(instance.refilled_quantity))

            used_stock, cretated = Stock.objects.get_or_create(
                repository=instance.repository,
                item=instance.used_item.item
            )
            used_stock.adjust_stock(Decimal(instance.used_quantity))
            
            return super().destroy(request, *args, **kwargs)



class ListItemTransformer(
    ListModelMixin,
    generics.GenericAPIView
):
    queryset = ItemTransformer.objects.all()
    serializer_class = ItemTransformerSerializer


    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)



class ListOreItem(
    ListModelMixin,
    generics.GenericAPIView
):
    queryset = OreItem.objects.all()
    serializer_class = OreItemSerializer


    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

