from items.models import InitialStock, ItemPriceLog
from invoices.buyer_supplier_party.models import InitialCreditBalance
from common.utility.date.time_timezone_format import get_formatted_time
from datetime import timedelta
from django.utils import timezone
from year_closure.models import ClosurePeriod
from items.services.validate_items_stock import ValidateItemsStock as V
from finance.vault_and_methods.services.calculate_owner_credit_balance import calculate_owner_credit_balance
from invoices.buyer_supplier_party.models import Party


def locked_year_closure_logic(closure_perido_instance):
	tomorrow = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
	
	price_log_set = set()
	initialstock_instances  = []
	pricelog_instances      = []
	for (i, r), value in V().stock_validation(option=1).items():
		if value > 0:
			initialstock_instances.append(
				InitialStock(
					item_id=i, 
					repository_id=r, 
					quantity=value, 
					date=tomorrow, 
					notes=f"new-year-auto-insertion {closure_perido_instance.from_date}-{closure_perido_instance.to_date}",
					created_at=get_formatted_time(),
					updated_at=get_formatted_time(),
					by_id=10000,
					year_closure=closure_perido_instance
				)
			)

		if not i in price_log_set:
			ipl = ItemPriceLog.objects.filter(item_id=i).order_by('-date').first()

			if ipl is not None and ipl.price > 0:
				pricelog_instances.append(
					ItemPriceLog(
						item_id=i,
						price=ipl.price,
						date=tomorrow,
						notes=f"new-year-auto-insertion {closure_perido_instance.from_date}-{closure_perido_instance.to_date}",
						created_at=get_formatted_time(),
						updated_at=get_formatted_time(),
						by_id=10000
					)
				)

		price_log_set.add(i)
	InitialStock.objects.bulk_create(initialstock_instances)
	ItemPriceLog.objects.bulk_create(pricelog_instances)

	initalcreditbalance_instances = []
	for client in Party.objects.all():
		credit = calculate_owner_credit_balance(client.id, None)
		
		if not credit == 0:
			initalcreditbalance_instances.append(
				InitialCreditBalance(
					party=client,
					amount=credit,
					date=tomorrow,
					notes=f"new-year-auto-insertion {closure_perido_instance.from_date}-{closure_perido_instance.to_date}",
					created_at=get_formatted_time(),
					updated_at=get_formatted_time(),
					by_id=10000,
					year_closure=closure_perido_instance
				)
			)
	InitialCreditBalance.objects.bulk_create(initalcreditbalance_instances)


def unlocked_year_closure_logic(closure_perido_instance):
	period = ClosurePeriod.objects.get(id=closure_perido_instance.id)

	period.ycis.all().delete()
	period.ycicb.all().delete()

	ItemPriceLog.objects.filter(notes=f"new-year-auto-insertion {closure_perido_instance.from_date}-{closure_perido_instance.to_date}").delete()
