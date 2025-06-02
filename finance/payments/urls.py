from django.urls import path
from .views import ListCreateView, DetailPaymentView, ListCreateExpensePaymentView, DetailExpensePaymentView


urlpatterns = [
    path('payments/', ListCreateView.as_view()),
    path('payments/<int:pk>/', DetailPaymentView.as_view()),
    path('expenses/', ListCreateExpensePaymentView.as_view()),
    path('expenses/<int:pk>/', DetailExpensePaymentView.as_view()),
]
