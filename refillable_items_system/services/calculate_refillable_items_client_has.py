from invoices.sales.models import ReturnInvoiceItem as SalesRefundItem, ReturnInvoice, SalesInvoiceItem, SalesInvoice
from items.models import DamagedItems, Items
from refillable_items_system.models import ItemTransformer, RefillableItemsInitialStockClientHas, RefundedRefillableItem
# 
from django.db.models import Sum, Q, F, Case, When, F, IntegerField


def calculateRefillableItemsClientHas(client_id):
    invoices = SalesInvoice.objects.filter(owner_id=client_id)
    refillable_items = Items.objects.filter(is_refillable=True)

    transformer = ItemTransformer.objects.select_related('item', 'transform').all()
    # Build ID lists
    empty_item_ids = [t.item_id for t in transformer]
    filled_item_ids = [t.transform_id for t in transformer]

    initial_stock_client_has = get_refillable_items_totals(
        RefillableItemsInitialStockClientHas, 
        client_id, 
        empty_item_ids
    )

    refunded = get_refillable_items_totals(
        RefundedRefillableItem, 
        client_id, 
        empty_item_ids
    )

    damaged_items = get_refillable_items_totals(
        DamagedItems,
        client_id,
        [*empty_item_ids, *filled_item_ids]
    )

    empty_refillable_sales_data = get_sales_refillable_items_totals(SalesInvoiceItem, client_id, empty_item_ids=empty_item_ids)
    filled_refillable_sales_data = get_sales_refillable_items_totals(SalesInvoiceItem, client_id, filled_item_ids=filled_item_ids)

    empty_refillable_sales_refund_data = get_sales_refillable_items_totals(SalesRefundItem, client_id, empty_item_ids=empty_item_ids)
    filled_refillable_sales_refund_data = get_sales_refillable_items_totals(SalesRefundItem, client_id, filled_item_ids=filled_item_ids)

    obj = {}

    for transform_obj in transformer:
        empty = transform_obj.item
        filled = transform_obj.transform

        total = next((item['total'] for item in initial_stock_client_has if item['item_id'] == empty.id), 0)
        total -= next((item['total'] for item in refunded if item['item_id'] == empty.id), 0)
        total += next((item['total'] for item in empty_refillable_sales_data if item['item_id'] == empty.id), 0)
        total -= next((item['total'] for item in empty_refillable_sales_refund_data if item['item_id'] == empty.id), 0)
        total += next((item['total'] for item in filled_refillable_sales_data if item['item_id'] == filled.id), 0)
        total -= next((item['total'] for item in filled_refillable_sales_refund_data if item['item_id'] == filled.id), 0)
        total += next((item['total'] for item in damaged_items if item['item_id'] == empty.id), 0)
        total += next((item['total'] for item in damaged_items if item['item_id'] == filled.id), 0)

        if total != 0:
            obj[empty.name] = total



    refillable_items_quantities = {}
    for item in refillable_items:
        transformer = ItemTransformer.objects.filter(
            transform=item
        ).first()
        empty = transformer.item
        filled = transformer.transform

        initial_stock_client_has = RefillableItemsInitialStockClientHas.objects.filter(
            owner_id=client_id, 
            item=empty
        ).aggregate(Sum('quantity'))
        key_name = empty.name

        refunded = RefundedRefillableItem.objects.filter(
            owner_id=client_id, 
            item=empty
        ).aggregate(Sum('quantity'))

        for invoice in invoices:
            q = 0
            ri = None

            if invoice.notes.__contains__('#بدون حساب الفارغ'):
                continue

            if invoice.repository_permit:
                filled_item_qty = invoice.s_invoice_items.filter(item=filled).aggregate(Sum('quantity'))
                ri = ReturnInvoice.objects.filter(
                    original_invoice_id=invoice.id
                ).first()

                if ri:
                    q = ri.s_invoice_items.filter(item=filled).aggregate(Sum('quantity'))

                # idle_item_qty_taken = invoice.s_invoice_items.filter(item=empty).aggregate(Sum('quantity'))
                refillable_items_quantities[key_name] = refillable_items_quantities.get(key_name, 0)
                refillable_items_quantities[key_name] += (filled_item_qty['quantity__sum'] or 0)

                if q:
                    refillable_items_quantities[key_name] -= (q['quantity__sum'] or 0)

                # refillable_items_quantities[key_name] += (idle_item_qty_taken['quantity__sum'] or 0)

        refillable_items_quantities[key_name] = refillable_items_quantities.get(key_name, 0) + (initial_stock_client_has['quantity__sum'] or 0) - (refunded['quantity__sum'] or 0)

        if refillable_items_quantities[key_name] == 0:
            del refillable_items_quantities[key_name]
    refillable_items_quantities['enhanced'] = obj
    return refillable_items_quantities


def get_refillable_items_totals(model, client_id, item_ids):
    """Get totals for refillable items - returns aggregated results."""
    return model.objects.filter(
        owner_id=client_id,
        item_id__in=item_ids
    ).values(
        'item_id'
    ).annotate(
        total=Sum('quantity')
    )

def get_sales_refillable_items_totals(model, client_id, empty_item_ids=None, filled_item_ids=None):
    """Get sales totals with conditional aggregation based on #coo description."""
    if not empty_item_ids and not filled_item_ids:
        raise Exception({
            'detail': 'get_sales_refillable_items_totals(): empty item ids or filled item ids should be provided'
        })
    
    is_empty_items = True if empty_item_ids else False

    return model.objects.filter(
        invoice__owner_id=client_id,
        invoice__repository_permit=True,
        item_id__in=empty_item_ids if is_empty_items else filled_item_ids
    ).values(
        'item_id'
    ).annotate(
        total=Sum(
            Case(
                When(
                    Q(description__icontains='#coo') if is_empty_items else ~Q(description__icontains='#coo'), 
                    then=F('quantity')
                ),
                default=0,
                output_field=IntegerField(),
            )
        ),
    )
