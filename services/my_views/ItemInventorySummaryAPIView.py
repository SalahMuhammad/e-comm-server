from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import DecimalField, Sum, Subquery, OuterRef, Case, When, F, DecimalField
from items.models import Items, ItemPriceLog, DamagedItems, InitialStock
from repositories.models import Repositories
from invoices.purchase.models import PurchaseInvoiceItems
from invoices.sales.models import SalesInvoiceItem, ReturnInvoiceItem
from finance.debt_settlement.models import DebtSettlement
from finance.expenses.models import Expense
from refillable_items_system.models import (
	ItemTransformer, OreItem, RefundedRefillableItem, RefilledItem
)

from decimal import Decimal
from finance.vault_and_methods.services.calculate_owner_credit_balance import calculate_owner_credit_balance
import os, csv
# from .ItemInventorySummaryAsCSVS.export_item_detailed_csvs import export_item_detailed_csvs
# from .ItemInventorySummaryAsCSVS.get_detailed_item_dataset import get_detailed_item_dataset
from finance.vault_and_methods.services.calculate_owner_credit_balance import calculate_owner_credit_balance, creidt_equation
from django.shortcuts import get_object_or_404
from year_closure.models import ClosurePeriod



class ItemInventorySummaryAPIView(APIView):
	def get(self, request):
		exclude_list_param = request.GET.get('exclude-types')
		exclude_list_filter = ["spare_parts"]
		if exclude_list_param is not None:
			exclude_list_filter = exclude_list_param.lower().split(',')

		order_by = request.GET.get('order-by')
		order_by_sort = ["name", "-id"]
		if order_by is not None:
			order_by_sort = order_by.lower().split(',')

		period_instance = get_object_or_404(ClosurePeriod, pk=request.GET.get('instance_id'))

		items = Items.objects.exclude(type__name__in=exclude_list_filter).order_by(*order_by_sort)
		repositories = Repositories.objects.all()
		response_data = {"detial": {}, "list": []}

		start_date      = period_instance.from_date
		end_date        = period_instance.to_date

		#################### detail ####################

		debt_suttlement = DebtSettlement.objects.filter(date__range=(start_date, end_date)).aggregate(
			total=Sum('amount')
		)['total'] or Decimal('0.00')

		response_data["detial"]["deb_suttlement"] = debt_suttlement

		expense = Expense.objects.filter(date__range=(start_date, end_date)).aggregate(
			total=Sum('amount')
		)['total'] or Decimal('0.00')

		response_data["detial"]["expense"] = expense

		#################### detail ####################

		# # ------------------------- as ccsvs 
		# data = [get_detailed_item_dataset(item_id.id, repository_id=repository_id, start_date=start_date, end_date=end_date, end_date_obj=end_date_obj) for item_id in items]
		# export_item_detailed_csvs(data)


		# transaction based(row)
		initail_stock_details               = row_dataset(InitialStock, start_date, end_date)
		damaged_items_details               = row_dataset(DamagedItems, start_date, end_date)
		refunded_refillable_items_details   = row_dataset(RefundedRefillableItem, start_date, end_date)
		refilled_refillable_items_details   = row_dataset(RefilledItem, start_date, end_date, "refilled_quantity", ("refilled_item_id", "repository_id", ))
		used_refillable_items_details       = row_dataset(RefilledItem, start_date, end_date, "used_quantity", ("used_item_id", "repository_id", ))
		# invoice based(multiple rows)
		purchased_items_details             = invoice_dataset(PurchaseInvoiceItems, None, start_date, end_date)
		sold_items_details                  = invoice_dataset(SalesInvoiceItem, None, start_date, end_date)
		sold_refund_items_details           = invoice_dataset(ReturnInvoiceItem, None, start_date, end_date)

		sales_items_datatset = sold_refund_items(SalesInvoiceItem, start_date, end_date)
		sales_refund_items_dataset = sold_refund_items(ReturnInvoiceItem, start_date, end_date)

		sold_item_profits_details           = invoice_items_profits(sales_items_datatset)
		sold_refund_item_profits_details    = invoice_items_profits(sales_refund_items_dataset)

		price_log = ItemPriceLog.objects.all().order_by('item_id', '-date').distinct('item_id').values_list('item_id', 'price')
		plo = {iii: v for iii, v in price_log}

		ore_items_datatset = OreItem.objects.select_related('item').all()
		oreitem_map = {i.item.id: i.id  for i in ore_items_datatset}

		itf = {}
		iti = {}
		for i in ItemTransformer.objects.select_related('item', 'transform').all():
			# result[i.item] = i.transform
			itf[i.transform.id] = i.item.id
			iti[i.item.id] = i.transform.id

		# should calculate refilled for each refillable item, clarity and v3 etc
		# total_refilled = {}
		# for (item, repo), v in used_refillable_items_details.items():
		# 	total_refilled[item] = total_refilled.get(item, 0) + v[0]
		remaining_credits = 0
		for instance in calculate_owner_credit_balance(None, None, start_date, end_date):
			remaining_credits = remaining_credits + creidt_equation(instance)

		summary = {'items': {}, 'details': {'remaining_items_cost': 0, 'remaining_credits': remaining_credits, 'profits': {}}}
		all_items_cost = {}
		for r in repositories:
			all_items_cost[r.name] = 0
			summary['items'][r.name] = {}
			for item in items:
				isd     = initail_stock_details.get((item.id, r.id, ), [0, 0])
				did     = damaged_items_details.get((item.id, r.id, ), [0, 0])
				pid     = purchased_items_details.get((item.id, r.id, ), [0, 0])
				sid     = sold_items_details.get((item.id, r.id, ), [0, 0])
				sird    = sold_refund_items_details.get((item.id, r.id, ), [0, 0])
				rrid    = refunded_refillable_items_details.get((item.id, r.id, ), [0, 0])
				rriid   = refilled_refillable_items_details.get((itf.get(item.id, item.id), r.id, ), [0, 0])
				urid    = used_refillable_items_details.get((oreitem_map.get(item.id, None), r.id, ), [0, 0])

				if not isd[0] and not did[0] and not pid[0] and not sid[0] and not sird[0] and not rrid[0] and not rriid[0] and not urid[0]: continue 
		
				remaining = (
					isd[0] +
					pid[0] +
					sird[0] -
					sid[0] -
					did[0] -
					urid[0]
				)
				if iti.get(item.id, None) is not None:
					remaining += rrid[0]
					remaining -= rriid[0]
				if itf.get(item.id, None) is not None:
					remaining += rriid[0]

				summary['items'][r.name][item.id] = {
					"item_name": item.name,
					"initail_stock":    { "quantity": isd[0], "transaction_count": isd[1] },
					"purchased":        { "quantity": pid[0], "transaction_count": pid[1] },
					"sold":             { "quantity": sid[0], "transaction_count": sid[1] },
					"sold_refund":      { "quantity": sird[0], "transaction_count": sird[1] },
					"damaged":          { "quantity": did[0], "transaction_count": did[1] },
					"refillable_item_details": {
						"refund":       { "quantity": rrid[0], "transaction_count": rrid[1] },
						"refilled":     { "quantity": rriid[0], "transaction_count": rriid[1] },
						"used_items":   { "quantity": urid[0], "transaction_count": urid[1] },
						# "total_refilled": total_refilled[oreitem_map.get(item.id)] if urid[0] else 0
					},
					"item_profits": {
						'sales':        sold_item_profits_details['items'].get((item.id, r.id)),
						'sales_refund': sold_refund_item_profits_details['items'].get((item.id, r.id))
					},
					"remaing_quantity":     remaining,
					"remaining_items_cost": remaining * plo.get(item.id, 0)
				}
				all_items_cost[r.name] = all_items_cost[r.name] + (remaining * plo.get(item.id, 0))

		summary['details']['profits']['sales']          = sold_item_profits_details['summary']
		summary['details']['profits']['sales_refund']   = sold_refund_item_profits_details['summary']
		summary['details']['remaining_items_cost'] = all_items_cost
		

		return Response(summary)



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

def invoice_dataset(model, repository_permit, start_date, end_date):
	p_filters = {}
	if repository_permit is not None:
		p_filters['invoice__repository_permit'] = repository_permit
	return model.objects.date_range(
		start_date=start_date, 
		end_date=end_date,
		field_name='invoice__issue_date'
	).accumulate_by(
		'quantity',
		("item_id", "repository_id", ),
		distinct_field="invoice_id"
	)

def row_dataset(model, start_date, end_date, accmulate="quantity", group_by=("item_id", "repository_id", )):
	return model.objects.date_range(
		start_date=start_date, 
		end_date=end_date
	).accumulate_by(
		accmulate,
		group_by,
		distinct_field="id"
	)

def sold_refund_items(model, start_date, end_date_obj, ):
	# 1. Define the dynamic end date using conditional logic
	# This mimics: min(end_date_obj, invoice__issue_date)
	effective_end_date_expression = Case(
		When(invoice__issue_date__gt=end_date_obj, then=end_date_obj),
		default=F('invoice__issue_date')
	)

	# 2. Build the Subquery referencing the outer SalesInvoiceItem fields
	price_log_subquery = ItemPriceLog.objects.filter(
		item=OuterRef('item_id'),
	).date_range(
		start_date, 
		OuterRef('effective_end_date')
	).order_by(
		'-date', 
		'-id'
	).values('price')[:1]

	# 3. Apply both annotations to your main QuerySet
	return model.objects.select_related('invoice', 'item').date_range(
		start_date=start_date,
		end_date=end_date_obj,
		field_name='invoice__issue_date',
	).annotate(
		# First, calculate the row-specific date ceiling
		effective_end_date=effective_end_date_expression,
		# Second, execute the subquery using that calculated date
		unit_cost=Subquery(price_log_subquery, output_field=DecimalField()),
		# transaction_count=Count('invoice_id', distinct=True)
	).values(
		'invoice_id',
		'invoice__issue_date',
		'item_id',
		'repository_id', 
		'effective_end_date', 
		'quantity',
		'unit_price',
		'discount',
		'tax_rate',
		'unit_cost', 
		# 'transaction_count',
	)

def invoice_items_profits(dataset):
	summary_obj = {
		'items': {},
		'summary': {
			'total_taxes': Decimal('0'), 
			'total_discounts': Decimal('0'),
			'lose_invoices': []
		}
	}

	for i in dataset:
		summary_obj['summary']['total_taxes']         += i['tax_rate']
		summary_obj['summary']['total_discounts']     += i['discount']

		# 1. Safely resolve unit_cost (default to 0 if None)
		unit_cost = 0 if i['unit_cost'] is None else i['unit_cost']

		# 2. Correctly calculate profit: (Price - Cost) * Quantity - Discount
		line_profit = ((i['unit_price'] - unit_cost) * i['quantity']) - i['discount']

		# 3. Fix dictionary lookup to target summary_obj['items']
		summary_obj['items'][(i['item_id'], i['repository_id'])] = summary_obj['items'].get(i['item_id'], 0) + line_profit

		# if line_profit <= 0:
		# 	summary_obj['summary']['lose_invoices'].append((i['invoice_id'], line_profit))

	return summary_obj
