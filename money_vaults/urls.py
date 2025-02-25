from django.urls import path
from .views import MoneyVaultListCreateView, MoneyVaultDetailView


urlpatterns = [
    path('', MoneyVaultListCreateView.as_view(), name='money_vault_list'),
    path('<int:pk>/', MoneyVaultDetailView.as_view(), name='money_vault_detail'),
]