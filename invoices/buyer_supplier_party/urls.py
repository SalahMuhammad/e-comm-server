from django.urls import path
from .views import ListCreateView, DetailView, OwnerView, customerAccountStatement, ListClientCredits


urlpatterns = [
    path('', ListCreateView().as_view(), name='list'),
    path('<int:pk>/', DetailView().as_view(), name='detail'),
    path('owner/view/<int:pk>/', OwnerView.as_view()),
    path('list-of-clients-that-has-credit-balance/', ListClientCredits.as_view()),
    path('customer-account-statement/<int:pk>/', customerAccountStatement),
]
