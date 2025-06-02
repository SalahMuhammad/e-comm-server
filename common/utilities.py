from rest_framework.pagination import PageNumberPagination
from items.models import Stock
from decimal import Decimal, ROUND_HALF_UP


def set_request_items_totals(items):
	total_amount = 0
	for i, item in enumerate(items):
		quantity = item.get('quantity', 1)
		unit_price = item['unit_price'] 
		tax_rate = item.get('tax_rate', 0)
		discount = item.get('discount', 0)

		item['quantity'] = Decimal(str(quantity)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		item['unit_price'] = Decimal(str(unit_price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		item['tax_rate'] = Decimal(str(tax_rate)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		item['discount'] = Decimal(str(discount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		
		item['total'] = Decimal(str((item['quantity'] * item['unit_price']) + item['tax_rate'] - item['discount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

		total_amount += item['total']

	return items, total_amount


def insert_invoice_items(invoice_instance, items_relations_name, items):
	"""
	Insert invoice items and adjust stock accordingly.

	This function creates invoice items for a given invoice instance and adjusts
	the stock levels based on the items' quantities.

	Args:
		invoice_instance: The invoice object to which items will be added.
		items_relations_name (str): The name of the relation for invoice items.
		items (list): A list of dictionaries containing item data.
		adjust_stock_sign (int, optional): Multiplier for stock adjustment. 
			Use -1 for reducing stock (e.g., sales), 1 for increasing (e.g., purchases). 
			Defaults to 1.

	Returns:
		None

	Side effects:
		- Creates new invoice items linked to the invoice_instance.
		- Adjusts stock levels for each item in the Stock model.
	"""
	# Todo: Add validation for items
	for item_data in items:
		getattr(invoice_instance, items_relations_name).create(
			repository_id=item_data['repository'],
			item_id=item_data['item'],
			description=item_data.get('description', ''),
			quantity=item_data.get('quantity', 1),
			unit_price=item_data.get('unit_price', 0),
			tax_rate=item_data.get('tax_rate', 0),
			discount=item_data.get('discount', 0),
			total=item_data.get('total', 0)
		)

def adjust_stock(items, adjust_stock_sign):
	for item in items:
		stock, cretated = Stock.objects.get_or_create(
			repository=item.repository,
			item=item.item
		)
		stock.adjust_stock(item.quantity * adjust_stock_sign)

def get_pagination_class(self):
        if self.request.query_params.get('full_report') == 'true':            
            class CustomPagination(PageNumberPagination):
                page_size = 10000
                
            return CustomPagination
        return self.pagination_class


from invoices.purchase.models import PurchaseInvoices
from invoices.sales.models import SalesInvoice, ReturnInvoiceItem
from repositories.models import Repositories
from transfer_items.models import Transfer
from items.models import Stock
from items.models import Items, InitialStock, DamagedItems
from django.db.models import Sum
from django.db.models import Q
import os, json, datetime
import re
from refillable_items_system.models import ItemTransformer, RefundedRefillableItem, RefilledItem, OreItem


class ValidateItemsStock():
	# def __init__(self, invoice_instance, items_relations_name, items):
		# self.invoice_instance = invoice_instance
		# self.items_relations_name = items_relations_name
		# self.items = items

	def validate_stock(self, items=Items.objects.all()):
		repositories = Repositories.objects.all()
		item_transformer = ItemTransformer.objects.all()

		for item_data in items:
			for repo in repositories:
				initial_stock = self.get_initial_stock_quantities(item_data, repo)
				initial_stock = initial_stock['quantity__sum'] if initial_stock['quantity__sum'] else 0

				purchased_item_qty = self.get_invoices_quantities(
					PurchaseInvoices,
					'p',
					[item_data.id], 
					repo.id
				)

				sold_item_qty = self.get_invoices_quantities(
					SalesInvoice,
					's',
					[item_data.id],
					repo.id
				)

				sales_invoice_refund = self.get_sales_invoice_refund(
					item_data,
					repo
				)

				refunded_refillable_items_qty = 0
				refunded_refilled = 0
				if item_data.id in item_transformer.values_list('item', flat=True):
					refunded_refillable_items_qty = self.get_refunded_refillable_items_quantities(
						item_data,
						repo
					)

					refunded_refilled = self.get_refilled_items_quantities(
						item_data,
						repo
					)

				filled_items_qty = 0
				if item_data.id in item_transformer.values_list('transform', flat=True):
					filled_items_qty = self.get_refilled_items_quantities(
						item_transformer.filter(transform=item_data).first().item,
						repo
					)

				used_items_qty = 0
				if item_data.id in OreItem.objects.all().values_list('item', flat=True):
					used_items_qty = self.get_used_items_quantities(
						item_data,
						repo
					)

				damaged = self.get_quantity_of_damaged_item(
					item_data, 
					repo
				)
				# transfer_from = self.get_transfer_quantities(item_ids=[item_data.id], from_id=repo.id)
				# transfer_to = self.get_transfer_quantities(item_ids=[item_data.id], to_id=repo.id)

				# git first item from the list otherwise return [0, 0]
				purchased_item_qty = purchased_item_qty[0] if purchased_item_qty else [0,0]
				sold_item_qty = sold_item_qty[0] if sold_item_qty else [0,0]
				# transfer_from = transfer_from[0] if transfer_from else [0,0]
				# transfer_to = transfer_to[0] if transfer_to else [0,0]

				exact_qty = 0
				exact_qty += initial_stock
				exact_qty += purchased_item_qty[1]
				exact_qty += refunded_refillable_items_qty
				exact_qty += filled_items_qty
				exact_qty -= sold_item_qty[1]
				exact_qty -= refunded_refilled
				exact_qty -= used_items_qty
				exact_qty += sales_invoice_refund
				exact_qty -= damaged
				
				stock, created = Stock.objects.get_or_create(repository=repo, item=item_data)
				
				if stock.quantity != exact_qty:
					directory = 'quantity-errors'
					os.makedirs(directory, exist_ok=True)

					raw_filename = f"{item_data.name}_{repo.name}_{datetime.datetime.now(datetime.timezone.utc)}.json"
					# Replace unsafe characters with underscores
					safe_filename = re.sub(r'[^\w\-_\.]', '_', raw_filename)
					file_path = os.path.join(directory, safe_filename)

					data = {
						'date': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
						'item_id': item_data.id,
						'item_name': item_data.name,
						'repo_id': repo.id,
						'repo_name': repo.name,
						'stock': str(stock.quantity),
						'accurate_stock': str(exact_qty)
					}

					with open(file_path, 'w', encoding='utf-8') as f:
						json.dump(data, f, indent=4)

					stock.quantity = exact_qty
					stock.save()

	def get_invoices_quantities(
		self,
		invoice_instance=PurchaseInvoices, 
		items_relations_name='p', 
		item_ids=Items.objects.all(), 
		repository_id=1
	):
		relation_name = f"{items_relations_name}_invoice_items"
		items_path = f"{relation_name}__item_id"
		repo_path = f"{relation_name}__repository_id"
		quantity_path = f"{relation_name}__quantity"

		return invoice_instance.objects.filter(
			Q(**{f"{items_path}__in": item_ids}),
			Q(**{f"{repo_path}": repository_id}),
			repository_permit=True,
		).values(
			items_path
		).annotate(
			total_quantity=Sum(quantity_path)
		).values_list(items_path, 'total_quantity')

	def get_refunded_refillable_items_quantities(
		self,
		item,
		repository
	):
		return RefundedRefillableItem.objects.filter(
			item=item,
			repository=repository,
		).aggregate(
			total_quantity=Sum('quantity')
		)['total_quantity'] or 0
	
	def get_refilled_items_quantities(
		self,
		item,
		repository
	):
		return RefilledItem.objects.filter(
			refilled_item=item,
			repository=repository,
		).aggregate(
			total_refilled_quantity=Sum('refilled_quantity'), 
		)['total_refilled_quantity'] or 0
	
	def get_sales_invoice_refund(
		self,
		item,
		repository
	):
		return ReturnInvoiceItem.objects.filter(
			item=item,
			repository=repository,
		).aggregate(
			total=Sum('quantity'), 
		)['total'] or 0

	def get_used_items_quantities(
		self,
		item,
		repository
	):
		return RefilledItem.objects.filter(
			used_item__item=item,
			repository=repository,
		).aggregate(
			total_used_quantity=Sum('used_quantity')
		)['total_used_quantity'] or 0

	def get_quantity_of_damaged_item(
		self,
		item,
		repository
	):
		return DamagedItems.objects.filter(
			item=item,
			repository=repository,
		).aggregate(
			total=Sum('quantity')
		)['total'] or 0

	def get_transfer_quantities(self, item_ids, from_id=False, to_id=False):
		q = Q(fromm_id=from_id) if from_id else Q(too_id=to_id)
		return Transfer.objects.filter(
			q,
			Q(items__item_id__in=item_ids)
		).values(
			'items__item_id'
		).annotate(
			total_quantity=Sum('items__quantity')
		).values_list('items__item_id', 'total_quantity')
	
	def get_initial_stock_quantities(self, item, repo):
		return InitialStock.objects.filter(
			repository=repo,
			item=item,
		).aggregate(Sum('quantity'))
	# .values(
	# 		'item_id'
	# 	).annotate(
	# 		total_quantity=Sum('quantity')
	# 	).values_list('total_quantity')











import hashlib
def short_hash_number(num):
	# Use a short hash: take the integer value of the md5 digest and encode in base36 for compactness
	return hashlib.md5(str(num).encode()).hexdigest()[:8]  # first 8 chars