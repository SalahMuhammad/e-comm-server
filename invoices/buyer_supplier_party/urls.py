from django.urls import path
from .views import ListCreateView, DetailView, ownerView, customerAccountStatement, listClientCredits


urlpatterns = [
    path('', ListCreateView().as_view(), name='list'),
    path('<int:pk>/', DetailView().as_view(), name='detail'),
    path('owner/view/<int:pk>/', ownerView),
    path('list-of-clients-that-has-credit-balance/', listClientCredits),
    path('customer-account-statement/<int:pk>/', customerAccountStatement),
]
