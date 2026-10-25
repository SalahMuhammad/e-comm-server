from decimal import Decimal
from django.db.models import Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response

from items.models import Items, ItemPriceLog, DamagedItems, InitialStock
from repositories.models import Repositories
from invoices.purchase.models import PurchaseInvoiceItems
from invoices.sales.models import SalesInvoiceItem, ReturnInvoiceItem
from refillable_items_system.models import (
    ItemTransformer, OreItem, RefundedRefillableItem, RefilledItem
)

from .ItemInventorySummaryAsCSVS.export_item_detailed_csvs import export_item_detailed_csvs
from .ItemInventorySummaryAsCSVS.get_detailed_item_dataset import get_detailed_item_dataset

# mine
from finance.debt_settlement.models import DebtSettlement
from finance.expenses.models import Expense

from django.db.models import Q

class ItemInventorySummaryAPIView(APIView):
    def get(self, request):
        # Option to filter by repository_permit (True, False, or None/All)
        permit_param = request.GET.get('repository_permit')
        permit_filter = None
        if permit_param is not None:
            permit_filter = permit_param.lower() in ['true', '1', 'yes']

        exclude_list_param = request.GET.get('repository_permit')
        exclude_list_filter = ["spare_parts"]
        if permit_param is not None:
            exclude_list_filter = exclude_list_param.lower().split(',')

        # permit_param = request.GET.get('repository_permit')
        # permit_filter = None
        # if permit_param is not None:
        #     permit_filter = permit_param.lower() in ['true', '1', 'yes']

        items = Items.objects.exclude(type__name__in=exclude_list_filter)#.exclude(name__icontains=)
        repositories = Repositories.objects.all()
        response_data = {"detial": {}, "list": []}

        #################### detail ####################

        debt_suttlement = DebtSettlement.objects.all().aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        response_data["detial"]["deb_suttlement"] = debt_suttlement

        expense = Expense.objects.all().aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        response_data["detial"]["expense"] = expense

        total_profits = Decimal('0.00')
        total_refund_profits = Decimal('0.00')

        #################### detail ####################

        # # ------------------------- as ccsvs 
        data = [get_detailed_item_dataset(item_id.id) for item_id in items]
        export_item_detailed_csvs(data)

        for item in items:
            # --- 1. Global Aggregations ---
            
            # Initial Stock Qty (total across repos)
            initail_stock_qty = InitialStock.objects.filter(item=item).aggregate(
                total=Sum('quantity')
            )['total'] or Decimal('0.00')

            # Purchased Qty
            p_filters = {'item': item}
            if permit_filter is not None:
                p_filters['invoice__repository_permit'] = permit_filter
            purchased_qty = PurchaseInvoiceItems.objects.filter(**p_filters).aggregate(
                total=Sum('quantity')
            )['total'] or Decimal('0.00')

            # Sold Qty
            s_filters = {'item': item}
            if permit_filter is not None:
                s_filters['invoice__repository_permit'] = permit_filter
            sold_qs = SalesInvoiceItem.objects.filter(**s_filters)
            sold_qty = sold_qs.aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')

            # Sold Refund Qty
            r_filters = {'item': item}
            if permit_filter is not None:
                r_filters['invoice__repository_permit'] = permit_filter
            sold_refund = ReturnInvoiceItem.objects.filter(**r_filters).aggregate(
                total=Sum('quantity')
            )['total'] or Decimal('0.00')

            # --- 2. Item Profits Calculation based on ItemPriceLog ---
            item_profits = Decimal('0.00')
            for sale_item in sold_qs.select_related('invoice'):
                sale_date = sale_item.invoice.issue_date
                # Find the latest price log on or before the sale date
                price_log = ItemPriceLog.objects.filter(
                    item=item, date__lte=sale_date
                ).order_by('-date', '-id').first()

                try:
                    item_refund_total = Decimal('0.00')
                    x = sale_item.invoice.return_invoices
                    a = x.s_invoice_items.filter(item=item)

                    price_log_2 = ItemPriceLog.objects.filter(
                        item=item, date__lte=x.issue_date
                    ).order_by('-date', '-id').first()

                    for i in a:
                        r_cost_price = price_log_2.price if price_log_2 else i.unit_price
                        r_unit_profit = i.unit_price - r_cost_price
                        r_line_profit = r_unit_profit * i.quantity
                        item_refund_total += r_line_profit
                    
                    # total_profits -= item_refund_total
                    # total_refund_profits += item_refund_total
                except Exception as e:
                    pass

                cost_price = price_log.price if price_log else sale_item.unit_price
                unit_profit = sale_item.unit_price - cost_price
                line_profit = unit_profit * sale_item.quantity
                item_profits += line_profit - item_refund_total

            # --- 3. Refillable Item Details & Usage ---
            # Refunded refillable items
            refund_qty = RefundedRefillableItem.objects.filter(item=item).aggregate(
                total=Sum('quantity')
            )['total'] or Decimal('0.00')

            refilled_qty = Decimal('0.00')
            # if ItemTransformer.objects.filter(transform=item).exists():
                # Refilled quantity (when item is the transformed result)
                # refilled_qty = RefilledItem.objects.filter(refilled_item=item).aggregate(
            t = ItemTransformer.objects.filter(Q(transform=item) | Q(item=item)).first()
            refilled_qty = RefilledItem.objects.filter(refilled_item=t.item if t else None).aggregate(
                total=Sum('refilled_quantity')
            )['total'] or Decimal('0.00')

            # RefilledItem's total used_quantity (when item acts as the ore/used item)
            ore_item_obj = OreItem.objects.filter(item=item).first()
            refillable_item_used = Decimal('0.00')
            if ore_item_obj:
                refillable_item_used = RefilledItem.objects.filter(used_item=ore_item_obj).aggregate(
                    total=Sum('used_quantity')
                )['total'] or Decimal('0.00')

            # --- 4. Remaining in Repositories Calculation ---
            is_transformer_target = ItemTransformer.objects.filter(transform=item).exists()
            is_transformer_source = ItemTransformer.objects.filter(item=item).exists()

            remaing_in_repositroies = []
            for repo in repositories:
                repo_initial = InitialStock.objects.filter(item=item, repository=repo).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
                
                repo_purchase_filters = {'item': item, 'repository': repo}
                if permit_filter is not None:
                    repo_purchase_filters['invoice__repository_permit'] = permit_filter
                repo_purchased = PurchaseInvoiceItems.objects.filter(**repo_purchase_filters).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')

                repo_sold_filters = {'item': item, 'repository': repo}
                if permit_filter is not None:
                    repo_sold_filters['invoice__repository_permit'] = permit_filter
                repo_sold = SalesInvoiceItem.objects.filter(**repo_sold_filters).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')

                repo_refund_filters = {'item': item, 'repository': repo}
                if permit_filter is not None:
                    repo_refund_filters['invoice__repository_permit'] = permit_filter
                repo_sold_refund = ReturnInvoiceItem.objects.filter(**repo_refund_filters).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')

                repo_damaged = DamagedItems.objects.filter(item=item, repository=repo).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')

                # Refillable repository calculations
                repo_refilled_target = Decimal('0.00')
                if is_transformer_target:
                    repo_refilled_target = RefilledItem.objects.filter(refilled_item=ItemTransformer.objects.filter(transform=item).first().item, repository=repo).aggregate(total=Sum('refilled_quantity'))['total'] or Decimal('0.00')

                repo_refillable_net = Decimal('0.00')
                repo_used_qty = Decimal('0.00')
                if is_transformer_source:# and ore_item_obj:
                    repo_refunded_ore = RefundedRefillableItem.objects.filter(item=item, repository=repo).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
                    # repo_used_ore = RefilledItem.objects.filter(used_item=ore_item_obj, repository=repo).aggregate(total=Sum('used_quantity'))['total'] or Decimal('0.00')
                    repo_used_ore = RefilledItem.objects.filter(refilled_item=item, repository=repo).aggregate(total=Sum('refilled_quantity'))['total'] or Decimal('0.00')
                    repo_refillable_net = repo_refunded_ore - repo_used_ore
                    repo_used_qty = repo_used_ore

                # RefilledItem's total used_quantity (when item acts as the ore/used item)
                ore_item_obj = OreItem.objects.filter(item=item).first()
                refillable_item_used_2 = Decimal('0.00')
                if ore_item_obj:
                    refillable_item_used_2 = RefilledItem.objects.filter(used_item=ore_item_obj, repository=repo).aggregate(
                        total=Sum('used_quantity')
                    )['total'] or Decimal('0.00')

                # Final Repository Quantity Formula
                repo_remaining = (
                    repo_initial +
                    repo_purchased +
                    repo_refilled_target +
                    repo_refillable_net +
                    repo_sold_refund -
                    repo_sold -
                    # repo_used_qty -
                    repo_damaged 
                     -                    refillable_item_used_2
                )

                if repo_remaining != 0 or repo_initial > 0 or repo_purchased > 0 or repo_sold > 0:
                    remaing_in_repositroies.append({
                        "repo_name": repo.name,
                        "qty": repo_remaining
                    })

            damaged_22 = DamagedItems.objects.filter(item=item).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')

            total_profits += item_profits
            print(total_refund_profits)

            price_log_3 = ItemPriceLog.objects.filter(
                item__name=item, date__lte=timezone.now().date()
            ).order_by('-date', '-id').first()
            price_value = price_log_3.price if price_log_3 else 0

            response_data["list"].append({
                "item_name": item.name,
                "initail_stock_qty": initail_stock_qty,
                "purchased_qty": purchased_qty,
                "sold_qty": sold_qty,
                "sold_refund": sold_refund,
                "damaged": damaged_22,
                "item_profits": item_profits,
                "refillable_item_details": {
                    "refund": refund_qty,
                    "refilled": refilled_qty
                },
                "refillable_item_used": refillable_item_used,
                "remaing_in_repositroies": remaing_in_repositroies,
                "remaining_items_cost": sum(i.get("qty", 0) for i in remaing_in_repositroies) * price_value
            })


        export_inventory_data_to_csv(response_data["list"])
        response_data['detial']['profits'] = total_profits - debt_suttlement - expense
        response_data['detial']['notes'] = []
        response_data['detial']['notes'].append("the repository is not includes outside refillable items")
        response_data['detial']['notes'].append("profits = profits - debt_suttlement - expense")

        return Response(response_data)
        # return Response({"fds"})


import os
import csv
from django.utils import timezone

def export_inventory_data_to_csv(data, output_dir="media/year-closure/inventory_csv_export"):
    """
    Exports inventory API response data into CSV files:
    1. A summary CSV containing all items (`inventory_summary.csv`).
    2. A directory named `items/` containing individual CSV files for each item.
    """
    # Ensure output directories exist
    os.makedirs(output_dir, exist_ok=True)
    items_dir = os.path.join(output_dir, "items")
    os.makedirs(items_dir, exist_ok=True)

    # --- 1. Generate Combined Summary CSV ---
    summary_file_path = os.path.join(output_dir, "inventory_summary.csv")
    summary_headers = [
        "item_name",
        "initail_stock_qty",
        "purchased_qty",
        "sold_qty",
        "sold_refund",
        "refillable_refund",
        "refillable_refilled",
        "refillable_item_used",
        "total_remaining_qty",
        "remaining quantity cost",
        "item_profits",
    ]

    with open(summary_file_path, mode="w", newline="", encoding="utf-8") as summary_file:
        writer = csv.writer(summary_file)
        writer.writerow(summary_headers)

        for item in data:
            refill_details = item.get("refillable_item_details", {})
            repos = item.get("remaing_in_repositroies", [])
            total_remaining = sum(r.get("qty", 0) for r in repos)

            writer.writerow([
                item.get("item_name", ""),
                item.get("initail_stock_qty", 0),
                item.get("purchased_qty", 0),
                item.get("sold_qty", 0),
                item.get("sold_refund", 0),
                refill_details.get("refund", 0),
                refill_details.get("refilled", 0),
                item.get("refillable_item_used", 0),
                total_remaining,
                item.get("remaining_items_cost", 0),
                item.get("item_profits", 0),
            ])

    # --- 2. Generate Individual Item CSV Files ---
    # for item in data:
    #     item_name = item.get("item_name", "unnamed_item")
        
    #     # Sanitize filename to replace/remove illegal filesystem characters
    #     safe_item_name = "".join(c for c in item_name if c.isalnum() or c in (" ", "_", "-")).rstrip()
    #     item_file_path = os.path.join(items_dir, f"{safe_item_name}.csv")

    #     refill_details = item.get("refillable_item_details", {})

    #     with open(item_file_path, mode="w", newline="", encoding="utf-8") as item_file:
    #         writer = csv.writer(item_file)

    #         # Metrics Breakdown Section
    #         writer.writerow(["Metric", "Value"])
    #         writer.writerow(["Item Name", item_name])
    #         writer.writerow(["Initial Stock Qty", item.get("initail_stock_qty", 0)])
    #         writer.writerow(["Purchased Qty", item.get("purchased_qty", 0)])
    #         writer.writerow(["Sold Qty", item.get("sold_qty", 0)])
    #         writer.writerow(["Sold Refund", item.get("sold_refund", 0)])
    #         writer.writerow(["Item Profits", item.get("item_profits", 0)])
    #         writer.writerow(["Refillable Refund", refill_details.get("refund", 0)])
    #         writer.writerow(["Refillable Refilled", refill_details.get("refilled", 0)])
    #         writer.writerow(["Refillable Item Used", item.get("refillable_item_used", 0)])
    #         writer.writerow([])  # Blank separator line

    #         # Repository Distribution Section
    #         writer.writerow(["Repository Breakdown"])
    #         writer.writerow(["Repository Name", "Remaining Qty"])
            
    #         repos = item.get("remaing_in_repositroies", [])
    #         if repos:
    #             for repo in repos:
    #                 writer.writerow([repo.get("repo_name", ""), repo.get("qty", 0)])
    #         else:
    #             writer.writerow(["No repository records found", 0])

    print(f"Export successful!\nSummary file: {summary_file_path}\nItem files folder: {items_dir}")
