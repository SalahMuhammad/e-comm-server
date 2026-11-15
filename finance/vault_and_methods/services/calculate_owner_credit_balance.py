from invoices.buyer_supplier_party.models import PartySubModelsUtils



def creidt_equation(instance): 
	total = 0
	total -= instance.purchaseinvoices_total
	total -= instance.returninvoice_total
	total -= instance.payment2_total
	total -= instance.debtsettlement_total
	total += instance.initialcreditbalance_total
	total += instance.salesinvoice_total
	total += instance.maintenance_transactions_total
	total += instance.reversepayment2_total 
	return total

def calculate_owner_credit_balance(client_id, date, start_date=None, end_date=None):
	party = [client_id] if client_id else None
	instances = PartySubModelsUtils()._get_total_credit(start_date, end_date, party, 1, 2)

	if len(instances) == 1:
		return creidt_equation(instances[0])
	return instances
