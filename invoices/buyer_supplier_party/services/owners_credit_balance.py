from invoices.buyer_supplier_party.models import Party
from finance.payments.services.calculate_owner_credit_balance import calculate_owner_credit_balance
from rest_framework.response import Response

def getOwnersCreditBalance():
    l = []
    for client in Party.objects.all():
        credit = calculate_owner_credit_balance(client.id, None)
        
        if credit != 0:
            l.append({
                "name": client.name,
                "amount": credit
            })

    return {
        'list': l
    }

def getOwnersCreditBalanceAsHttpResponse():
    return Response(
        getOwnersCreditBalance()
    )