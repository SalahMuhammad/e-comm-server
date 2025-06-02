from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
# 
from django.shortcuts import render


def abc(request):
  return render(request=request, template_name='index.html', context={})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/items/', include('items.urls')),
    path('api/users/', include('users.urls')),
    path('api/repositories/', include('repositories.urls')),
    # path('api/transfer-items/', include('transfer_items.urls')),
    ###################################################
    path('api-auth/', include('rest_framework.urls')),
    path('api/pp/', include('pp.urls')),
    ###################################################
    ################ payment #########################
    ###################################################
    path('api/payment/methods/', include('finance.payment_method.urls')),
    path('api/payment/', include('finance.payments.urls')),
    ###################################################
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
]

urlpatterns += [
  # re_path(r'^(?:.*)/?$', abc),
    re_path(r'', abc),
]