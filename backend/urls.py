import json
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# 
from django.http import JsonResponse
# 
from debug_toolbar.toolbar import debug_toolbar_urls



# def abc(request):
#     return render(request=request, template_name='index.html', context={})

def companyDetails(request):
    with open('media/companyDetails.json', 'r') as file:
        return JsonResponse(json.load(file))


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/company-details/', companyDetails),

    path('api/items/', include('items.urls')),
    path('api/users/', include('users.urls')),
    path('api/permissions/', include('permissions.urls')),
    path('api/user-management/', include('user_management.urls')),
    path('api/repositories/', include('repositories.urls')),
    # path('api/transfer-items/', include('transfer_items.urls')),
    ###################################################
    path('api-auth/', include('rest_framework.urls')),
    path('api/pp/', include('pp.urls')),
    ###################################################
    ################ finance #########################
    ###################################################
    # path('api/payment/methods/', include('finance.payment_method.urls')),
    path('api/finance/payment/', include('finance.payment.urls')),
    path('api/finance/reverse-payment/', include('finance.reverse_payment.urls')),
    path('api/finance/debt-settlement/', include('finance.debt_settlement.urls')),
    path('api/finance/expenses/', include('finance.expenses.urls')),
    path('api/finance/internal-money-transfer/', include('finance.transfer.urls')),
    path('api/finance/account-vault/', include('finance.vault_and_methods.urls')),
    # path('admin/finance/payment/', include('finance.payment.urls')),
    ###################### services #############################
    path('api/services/', include('services.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
  	###################################################
    ################ invoices #########################
    ###################################################
    path('api/buyer-supplier-party/', include('invoices.buyer_supplier_party.urls')),
    ###################################################
    path('api/purchases/', include('invoices.purchase.urls')),
    path('api/sales/', include('invoices.sales.urls')),



    path('api/refillable-sys/', include('refillable_items_system.urls')),





    path('api/employees/', include('employees.urls')),





    path('api/requests-logs/', include('requests_logs.urls')),


    path('api/reports/', include('reports.urls')),
    
    
    # path('__debug__/', include('debug_toolbar.urls')),
# ] + debug_toolbar_urls()
]


from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods


# @ensure_csrf_cookie
# @require_http_methods(["GET"])
# def get_csrf_token(request, *args, **kwargs):
#     return JsonResponse({'csrfToken': get_token(request)})

# # In your urls.py
# urlpatterns += [
#     path('auth/csrf/', get_csrf_token, name='csrf'),
# ]

urlpatterns += [
  # re_path(r'^(?:.*)/?$', abc),
    # re_path(r'^(?!api/).*$', abc),
]

