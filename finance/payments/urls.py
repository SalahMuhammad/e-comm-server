from django.urls import path
from .views import ListCreateView, DetailPaymentView, ListCreateExpensePaymentView, DetailExpensePaymentView


urlpatterns = [
    path('payments/', ListCreateView.as_view()),
    # path('payments/p/total/', ListCreateView.as_view()),
    path('payments/<str:pk>/', DetailPaymentView.as_view()),
    path('reverse-payment/list/', ListCreateExpensePaymentView.as_view()),
    path('reverse-payment/<str:pk>/', DetailExpensePaymentView.as_view()),
]
