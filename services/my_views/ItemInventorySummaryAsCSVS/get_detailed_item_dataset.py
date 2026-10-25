from decimal import Decimal
from django.db.models import Sum
from items.models import Items, ItemPriceLog, DamagedItems, InitialStock
from repositories.models import Repositories
from invoices.purchase.models import PurchaseInvoiceItems
from invoices.sales.models import SalesInvoiceItem, ReturnInvoiceItem
from refillable_items_system.models import ItemTransformer, OreItem, RefundedRefillableItem, RefilledItem

from django.db.models import Q


def get_detailed_item_dataset(item_id, permit_filter=None):
    item = Items.objects.get(id=item_id)

    # 0. Price log
    price_log_qs = ItemPriceLog.objects.filter(item=item).order_by('-date', '-id')
    price_log_records = [
        {"price": s.price, "date": s.date, "notes": s.notes}
        for s in price_log_qs
    ]
    
    # 1. Initial Stock Section
    initial_qs = InitialStock.objects.filter(item=item).select_related('repository').order_by("date")
    initial_records = [
        {"repository": s.repository.name, "quantity": s.quantity, "date": s.date, "notes": s.notes}
        for s in initial_qs
    ]

    # 2. Purchase Invoices Section
    p_filters = {'item': item}
    if permit_filter is not None:
        p_filters['invoice__repository_permit'] = permit_filter
    purchases_qs = PurchaseInvoiceItems.objects.filter(**p_filters).select_related('invoice', 'repository').order_by("invoice__issue_date")
    purchase_records = [
        {
            "id": p.invoice.id,
            "issue_date": p.invoice.issue_date,
            "repository_permit": p.invoice.repository_permit,
            "repository": p.repository.name,
            "quantity": p.quantity,
            "unit_price": p.unit_price,
            "discount": p.discount,
            "tax_rate": p.tax_rate,
            "invoice_note": p.invoice.notes,
            "desc": p.description
        } for p in purchases_qs
    ]

    # 3. Sales Invoices & Profit Matching Section
    s_filters = {'item': item}
    if permit_filter is not None:
        s_filters['invoice__repository_permit'] = permit_filter
    sales_qs = SalesInvoiceItem.objects.filter(**s_filters).select_related('invoice', 'repository').order_by("invoice__issue_date")
    sales_records = []
    total_profit = Decimal('0.00')
    total_refund_profit = Decimal('0.00')

    for s in sales_qs:
        price_log = ItemPriceLog.objects.filter(
            item=item, date__lte=s.invoice.issue_date
        ).order_by('-date', '-id').first()

        cost_price = price_log.price if price_log else s.unit_price
        line_profit = (s.unit_price - cost_price) * s.quantity
        total_profit += line_profit

        try:
            refund_total = Decimal('0.00')
            x = s.invoice.return_invoices
            a = x.s_invoice_items.filter(item=item)

            price_log = ItemPriceLog.objects.filter(
                item=item, date__lte=x.issue_date
            ).order_by('-date', '-id').first()
            
            for i in a:
                r_cost_price = price_log.price if price_log else i.unit_price
                r_unit_profit = i.unit_price - r_cost_price
                r_line_profit = r_unit_profit * i.quantity
                refund_total += r_line_profit
            total_refund_profit += refund_total
        except Exception as e:
            pass

        sales_records.append({
            "id": s.invoice.id,
            "issue_date": s.invoice.issue_date,
            "repository_permit": s.invoice.repository_permit,
            "repository": s.repository.name,
            "quantity": s.quantity,
            "unit_price": s.unit_price,
            "cost_price": cost_price,
            "line_profit": line_profit,
            "refund_profit": refund_total,
            "invoice_note": s.invoice.notes,
            "desc": s.description
        })

    # 4. Return Invoices Section
    r_filters = {'item': item}
    if permit_filter is not None:
        r_filters['invoice__repository_permit'] = permit_filter
    returns_qs = ReturnInvoiceItem.objects.filter(**r_filters).select_related('invoice', 'repository').order_by("invoice__issue_date")
    return_records = [
        {
            "id": r.invoice.id,
            "issue_date": r.invoice.issue_date,
            "repository_permit": r.invoice.repository_permit,
            "repository": r.repository.name,
            "quantity": r.quantity,
            "unit_price": r.unit_price,
            "invoice_note": r.invoice.notes,
            "desc": r.description
        } for r in returns_qs
    ]

    # 5. Damaged Items Section
    damaged_qs = DamagedItems.objects.filter(item=item).select_related('repository').order_by("date")
    damaged_records = [
        {"repository": d.repository.name, "quantity": d.quantity, "date": d.date, "notes": d.notes}
        for d in damaged_qs
    ]

    # 6. Refillable Sections
    refill_refunds_qs = RefundedRefillableItem.objects.filter(item=item).select_related('repository').order_by("date")
    refillable_refund_records = [
        {"repository": rf.repository.name, "quantity": rf.quantity, "date": rf.date, "notes": rf.notes}
        for rf in refill_refunds_qs
    ]

    ore_obj = OreItem.objects.filter(item=item).first()

    t = ItemTransformer.objects.filter(Q(transform=item) | Q(item=item)).first()
    refill_ops_qs = RefilledItem.objects.filter(
        refilled_item= t.item if t else None
    ).order_by("date") if not ore_obj else RefilledItem.objects.filter(used_item=ore_obj).order_by("date")

    refillable_ops_records = [
        {
            "repository": op.repository.name,
            "refilled_quantity": op.refilled_quantity,
            "used_quantity": op.used_quantity,
            "used_item": op.used_item.item.name,
            "date": op.date, 
            "notes": op.notes
        } for op in refill_ops_qs.select_related('repository')
    ]

    return {
        "item_name": item.name,
        "initail_stock_qty": sum(r["quantity"] for r in initial_records),
        "purchased_qty": sum(r["quantity"] for r in purchase_records),
        "sold_qty": sum(r["quantity"] for r in sales_records),
        "sold_refund": sum(r["quantity"] for r in return_records),
        "damaged_total": sum(r["quantity"] for r in damaged_records),
        "item_profits": total_profit - total_refund_profit,
        "refillable_item_details": {
            "refund": sum(r["quantity"] for r in refillable_refund_records),
            "refilled": sum(r["refilled_quantity"] for r in refillable_ops_records)
        },
        "refillable_item_used": sum(r["used_quantity"] for r in refillable_ops_records),
        "price_log_records": price_log_records,
        "initial_stock_records": initial_records,
        "purchase_records": purchase_records,
        "sales_records": sales_records,
        "return_records": return_records,
        "damaged_records": damaged_records,
        "refillable_refund_records": refillable_refund_records,
        "refillable_ops_records": refillable_ops_records,
        "remaing_in_repositroies": []  # Populated from repository balance calculation
    }

