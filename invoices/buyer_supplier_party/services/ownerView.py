# services
from finance.vault_and_methods.services.calculate_owner_credit_balance import calculate_owner_credit_balance
from refillable_items_system.services.calculate_refillable_items_client_has import calculateRefillableItemsClientHas
# models
from invoices.buyer_supplier_party.models import Party
from finance.payment.models import Payment2
from django.db.models import Sum
from django.http import Http404
# 
from rest_framework.response import Response
# 
import json
from common.views.CustomQuerysetManager import CustomQuerysetManager


CQM = CustomQuerysetManager()



def ownerView(datee, client_id):
    credit = calculate_owner_credit_balance(client_id, datee)
    refillable_items = calculateRefillableItemsClientHas(client_id)
    paid = CQM.get_manager(Payment2).filter(date__range=[datee, datee], status=2, owner_id=client_id).aggregate(total=Sum('amount'),)['total'] or 0
    owner = Party.objects.filter(id=client_id).first()

    if not owner:
        raise Http404('route dose not exsists...')
    
    owner_detail_json = None
    try:
        owner_detail_json = json.loads(owner.detail)
    except (TypeError, ValueError):
        pass

    if owner_detail_json:
        owner_details = owner_detail_json
    else:
        owner_details = { 'details': owner.detail }

    return {
        "owner_name": owner.name,
        'credit': credit,
        'paid': paid,
        'refillable_items_client_has': refillable_items,
        **owner_details,
    }

def ownerViewAsHttpResponse(datee, client_id):
    return Response(
        ownerView(
            datee, 
            client_id
        )
    )