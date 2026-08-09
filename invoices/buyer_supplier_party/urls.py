from django.urls import path
from .views import ListCreateView, DetailView, OwnerView, AccountStatement, ListClientCredits


urlpatterns = [
    path('', ListCreateView().as_view(), name='party-list'),
    path('<int:pk>/', DetailView().as_view(), name='detail'),
    path(
        'owner/view/<int:pk>/', 
        OwnerView.as_view(),
        {'___view_id': 'buyerSupplier_view'},
    ),
    path(
        'list-of-clients-that-has-credit-balance/', 
        ListClientCredits.as_view(), 
        {'___view_id': 'buyerSupplier_creditBalanceList'},
    ),
    path(
        'customer-account-statement/<int:pk>/', 
        AccountStatement.as_view(),
        {'___view_id': 'buyerSupplier_accountStatement'},
    ),
]
