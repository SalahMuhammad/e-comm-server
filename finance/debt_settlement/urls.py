from django.urls import path
from .views import ListCreateDebtSettlementView, DetailDebtSettlementView


urlpatterns = [
    path('', ListCreateDebtSettlementView.as_view()),
    path('<str:pk>/', DetailDebtSettlementView.as_view()),
]
