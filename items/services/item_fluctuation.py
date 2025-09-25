from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from datetime import timedelta
from items.models import Items
from django.db.models import Sum, Q


# Calculate the date ranges
thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
def get_item_fluctuation(item_id):
    # item = get_object_or_404(Items, pk=item_id)
# 4
    # a = Items.objects.filter(
    #     pk=item_id, 
    # ).prefetch_related(
    #     'salesinvoiceitem_set', 
    #     'salesinvoiceitem_set__invoice', 
    #     'returninvoiceitem_set', 
    #     'returninvoiceitem_set__invoice'
    # ).annotate(   
    #     # Annotate total quantity for the last 30 days
    #     last_30_days_qty=Sum(
    #         'salesinvoiceitem__quantity',
    #         filter=Q(
    #             salesinvoiceitem__unit_price__gt=0,
    #             salesinvoiceitem__invoice__repository_permit=True,
    #             salesinvoiceitem__invoice__issue_date__gte=thirty_days_ago,
    #         )
    #     ),
    #     # Annotate total quantity for the last 60 days
    #     last_60_to_30_days_qty=Sum(
    #         'salesinvoiceitem__quantity',
    #         filter=Q(
    #             salesinvoiceitem__unit_price__gt=0,
    #             salesinvoiceitem__invoice__repository_permit=True,
    #             salesinvoiceitem__invoice__issue_date__range=(sixty_days_ago, thirty_days_ago),
    #         )
    #     )
    # )

    # previous =SalesInvoiceItem.objects.filter(
    #     item=item,
    #     unit_price__gt=0,
    #     invoice__issue_date__range=(sixty_days_ago, thirty_days_ago),
    #     invoice__repository_permit=True
    # ).aggregate(
    #     total=Sum('quantity')
    # )['total'] or 0

    # current = SalesInvoiceItem.objects.filter(
    #     item=item,
    #     unit_price__gt=0,
    #     # invoice__issue_date__range=(sixty_days_ago, datetime.now().strftime("%Y-%m-%d")),
    #     invoice__repository_permit=True
    # ).annotate(
    # # .aggregate(
    # #     total=Sum('quantity')
    # # )['total'] or 0
    
    #     # Annotate total quantity for the last 30 days
    #     last_30_days_qty=Sum(
    #         'quantity',
    #         filter=Q(
    #             invoice__issue_date__gte=thirty_days_ago,
    #         )
    #     ),
    #     # Annotate total quantity for the last 60 days
    #     last_60_to_30_days_qty=Sum(
    #         'quantity',
    #         # filter=Q(
    #         #     invoice__issue_date__range=(sixty_days_ago, thirty_days_ago),
    #         # )
    #     )
    # )

    sale_result = Items.objects.filter(pk=item_id).annotate(
        # Annotate total quantity for the last 30 days
        last_30_days_qty=Sum(
            'salesinvoiceitem__quantity',
            filter=Q(
                salesinvoiceitem__unit_price__gt=0,
                salesinvoiceitem__invoice__issue_date__gte=thirty_days_ago,
                salesinvoiceitem__invoice__repository_permit=True
            )
        ),
        # Annotate total quantity between 30 and 60 days ago
        last_60_to_30_days_qty=Sum(
            'salesinvoiceitem__quantity',
            filter=Q(
                salesinvoiceitem__unit_price__gt=0,
                salesinvoiceitem__invoice__issue_date__range=(sixty_days_ago, thirty_days_ago),
                salesinvoiceitem__invoice__repository_permit=True
            )
        )
    ).first()

    refund_result = Items.objects.filter(pk=item_id).annotate(
        # Annotate total quantity for the last 30 days
        last_30_days_refund_qty=Sum(
            'returninvoiceitem__quantity',
            filter=Q(
                returninvoiceitem__unit_price__gt=0,
                returninvoiceitem__invoice__issue_date__gte=thirty_days_ago,
                returninvoiceitem__invoice__repository_permit=True
            )
        ),
        # Annotate total quantity between 30 and 60 days ago
        last_60_days_refund_qty=Sum(
            'returninvoiceitem__quantity',
            filter=Q(
                returninvoiceitem__unit_price__gt=0,
                returninvoiceitem__invoice__issue_date__range=(sixty_days_ago, thirty_days_ago),
                returninvoiceitem__invoice__repository_permit=True
            )
        )
    ).first()

    # print(sale_result.net_30_days_qty, sale_result.net_60_days_qty)
    # print(current)
    # .aggregate(
    #     total=Sum('quantity')
    # )['total'] or 0

    # current_refund = ReturnInvoiceItem.objects.filter(
    #     item=item,
    #     unit_price__gt=0,
    #     invoice__issue_date__range=((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")),
    #     invoice__repository_permit=True
    # ).aggregate(
    #     total=Sum('quantity')
    # )['total'] or 0

    # previous_refund = ReturnInvoiceItem.objects.filter(
    #     item=item,
    #     unit_price__gt=0,
    #     invoice__issue_date__range=((datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")),
    #     invoice__repository_permit=True
    # ).aggregate(
    #     total=Sum('quantity')
    # )['total'] or 0

    if sale_result == None and refund_result == None: return { "detail": 'no data found' }

    return {
        "from_60_to_30_dayes": (sale_result.last_60_to_30_days_qty or 0) - (refund_result.last_60_days_refund_qty or 0),
        "last_30_dayes": (sale_result.last_30_days_qty or 0) - (refund_result.last_30_days_refund_qty or 0)
    }
