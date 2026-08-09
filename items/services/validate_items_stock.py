from invoices.purchase.models import PurchaseInvoiceItems 
from invoices.sales.models import SalesInvoiceItem, ReturnInvoiceItem 
from repositories.models import Repositories
from invoices.maintenance.models import TransactionSpareParts
# from transfer_items.models import Transfer, TransferItem
 
from refillable_items_system.models import ItemTransformer, RefundedRefillableItem, RefilledItem, OreItem 
from rest_framework.serializers import ValidationError 
from collections import defaultdict 
from decimal import Decimal

from django.db import transaction
from django.conf import settings
from django.db.models import Sum
from django.apps import apps
import os, json, datetime, re



class ValidateItemsStock():

	def stock_validation(self, item_ids=None, repository_ids=None, log_mismatches=True, raise_on_negative=False):
		Items = apps.get_model('items', 'Items')
		Stock = apps.get_model('items', 'Stock')

		items = (
			list(Items.objects.all()) if item_ids is None 
			else list(Items.objects.filter(pk__in=item_ids))
		)
		repositories = (
			list(Repositories.objects.all()) if repository_ids is None
			else list(Repositories.objects.filter(pk__in=repository_ids))
		)

		self.item_ids = [i.id for i in items]
		self.repo_ids = [r.id for r in repositories]
		item_id_set = set(self.item_ids)

		item_transformer = ItemTransformer.objects.all()
		transformer_item_ids = set(item_transformer.values_list('item', flat=True))
		transformer_transform_ids = set(item_transformer.values_list('transform', flat=True))
		ore_item_ids = set(OreItem.objects.all().values_list('item', flat=True))

		if any(i in self.item_ids for i in transformer_transform_ids):
			self.item_ids.extend(transformer_item_ids)

		# filled item id -> its paired refillable (empty) item id
		transform_to_item = {}
		for row in item_transformer.values('transform', 'item'):
			transform_to_item.setdefault(row['transform'], row['item'])

		initial_stock_lookup = self._as_lookup(
			self._get_quantities(apps.get_model('items', 'InitialStock'))
		)
		purchase_lookup = self._as_lookup(
			self._get_quantities(PurchaseInvoiceItems, extra_filters={'invoice__repository_permit': True})
		)
		sales_lookup = self._as_lookup(
			self._get_quantities(SalesInvoiceItem, extra_filters={'invoice__repository_permit': True})
		)
		# NOTE: original get_sales_invoice_refund() did NOT filter by repository_permit —
		# this adds it, matching your draft. Drop extra_filters here if that was accidental.
		sales_refund_lookup = self._as_lookup(
			self._get_quantities(ReturnInvoiceItem, extra_filters={'invoice__repository_permit': True})
		)
		maintenance_lookup = self._as_lookup(
            self._get_quantities(TransactionSpareParts, item_field='spare_part_id', extra_filters={'maintenance__maintenance_date__isnull': False}),
			item_field='spare_part_id'
        )
		damaged_lookup = self._as_lookup(
			self._get_quantities(apps.get_model('items', 'DamagedItems'))
		)

		refunded_refillable_lookup = {}
		refilled_lookup = {}
		if (item_id_set & transformer_item_ids) or (item_id_set & transformer_transform_ids):
			# One query serves both directions:
			#  - looked up directly by item id for refillable (empty) items -> subtracted
			#  - looked up via transform_to_item for filled items -> added
			refilled_lookup = self._as_lookup(
				self._get_quantities(RefilledItem, item_field='refilled_item', quantity_field='refilled_quantity'),
				item_field='refilled_item',
			)

		if item_id_set & transformer_item_ids:
			refunded_refillable_lookup = self._as_lookup(
				self._get_quantities(RefundedRefillableItem)
			)

		used_lookup = {}
		if item_id_set & ore_item_ids:
			used_lookup = self._as_lookup(
				self._get_quantities(RefilledItem, item_field='used_item__item', quantity_field='used_quantity'),
				item_field='used_item__item',
			)

		existing_stocks = {
			(s.item_id, s.repository_id): s
			for s in Stock.objects.filter(item_id__in=self.item_ids, repository_id__in=self.repo_ids)
		}

		to_update, to_create, mismatches, negative = [], [], [], []

		for item in items:
			for repo in repositories:
				key = (item.id, repo.id)

				exact_qty = 0
				exact_qty += initial_stock_lookup.get(key, 0)
				exact_qty += purchase_lookup.get(key, 0)
				exact_qty -= sales_lookup.get(key, 0)
				exact_qty -= maintenance_lookup.get(key, 0)
				exact_qty += sales_refund_lookup.get(key, 0)
				exact_qty -= damaged_lookup.get(key, 0)
				
				if item.id in transformer_item_ids:
					exact_qty += refunded_refillable_lookup.get(key, 0)
					exact_qty -= refilled_lookup.get(key, 0)

				if item.id in transformer_transform_ids:
					paired_item_id = transform_to_item.get(item.id)
					if paired_item_id is not None:
						exact_qty += refilled_lookup.get((paired_item_id, repo.id), 0)

				if item.id in ore_item_ids:
					exact_qty -= used_lookup.get(key, 0)

				stock = existing_stocks.get(key)
				if stock is None:
					stock = Stock(item=item, repository=repo)
					previous_qty = stock.quantity  # model default, e.g. 0
					stock.quantity = exact_qty
					to_create.append(stock)
				else:
					previous_qty = stock.quantity
					if previous_qty != exact_qty:
						stock.quantity = exact_qty
						to_update.append(stock)

				if log_mismatches and previous_qty != exact_qty:
					mismatches.append({
						'item_id': item.id,
						'item_name': item.name,
						'repo_id': repo.id,
						'repo_name': repo.name,
						'stock': str(previous_qty),
						'accurate_stock': str(exact_qty),
					})

				if exact_qty < 0:
					negative.append(f'{item.name} @ {repo.name} @ {exact_qty}')

		with transaction.atomic():
			if raise_on_negative and negative:
				raise ValidationError({
					'detail': f"Not enough stock for: {', '.join(sorted(set(negative)))}"
				})

			if to_update:
				Stock.objects.bulk_update(to_update, ['quantity'], batch_size=500)
			if to_create:
				Stock.objects.bulk_create(to_create, batch_size=500)

		if log_mismatches and mismatches:
			self._write_mismatch_files(mismatches)

		return {
			'checked': len(items) * len(repositories),
			'updated': len(to_update),
			'created': len(to_create),
			'mismatches': len(mismatches),
		}

	def _as_lookup(self, rows, item_field='item_id', repo_field='repository_id'):
		"""Turn get_quantities()'s grouped rows into a {(item_id, repo_id): total_quantity} dict."""
		if not rows:
			return {}
		return {(row[item_field], row[repo_field]): row['total_quantity'] for row in rows}

	def _write_mismatch_files(self, mismatches):
		directory = os.path.join(settings.MEDIA_ROOT, 'quantity-errors')
		os.makedirs(directory, exist_ok=True)
		timestamp = datetime.datetime.now(datetime.timezone.utc)
		for row in mismatches:
			raw_filename = f"{row['item_name']}_{row['repo_name']}_{timestamp}.json"
			safe_filename = re.sub(r'[^\w\-_\.]', '_', raw_filename)
			file_path = os.path.join(directory, safe_filename)
			with open(file_path, 'w', encoding='utf-8') as f:
				json.dump({**row, 'date': timestamp.strftime('%Y-%m-%d %H:%M:%S')}, f, indent=4)

	def _get_quantities(
		self,
		model,
		repo_field='repository_id',
		item_field='item_id',
		group_by=None,
		quantity_field='quantity',
		extra_filters=None
	):
		"""
		Fetches and aggregates quantities with dynamic filter field names
		and optional extra filters (e.g., related model fields).
		Assumes self.item_ids / self.repo_ids are already resolved to concrete
		(possibly empty) id lists before this is called.
		"""
		queryset = model.objects.all()

		filters = {}
		if self.repo_ids is not None:
			filters[f"{repo_field}__in"] = self.repo_ids
		if self.item_ids is not None:
			filters[f"{item_field}__in"] = self.item_ids

		if extra_filters:
			filters.update(extra_filters)

		if filters:
			queryset = queryset.filter(**filters)

		if group_by is None:
			group_by = [repo_field, item_field]

		return (
			queryset.values(*group_by)
			.annotate(total_quantity=Sum(quantity_field))
		)
	
	def _aggregate_item_quantities_for_validation(self, rows, values_keys):
		"""Aggregate item quantities grouped by repository and item for validation.

		Args:
			rows: Iterable of item data rows, each row may include a nested '_row'.
			values_keys: A sequence of keys for item, repository, and quantity values.

		Returns:
			A mapping of (repository, item, row_index) to accumulated quantity.
		"""
		filtered_objects = [
			{
				'index': index,
				# Fallback to item itself if '_row' key doesn't exist
				'item':         item.get('_row', item).get(values_keys[0]),
				'repository':   item.get('_row', item).get(values_keys[1]),
				'quantity':     item.get('_row', item).get(values_keys[2])
			}
			for index, item in enumerate(rows)
		]

		accumulated_data = defaultdict(Decimal)

		for obj in filtered_objects:
			key = (obj['repository'], obj['item'], obj['index'])
			accumulated_data[key] += obj['quantity']

		return accumulated_data
