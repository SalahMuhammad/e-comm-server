from django.urls import path
from .views import ExpenseListCreateView, ExpenseDetailView , CategoryListCreateView, CategoryDetailView 


urlpatterns = [
    path('', ExpenseListCreateView.as_view()),
    path('<str:pk>/', ExpenseDetailView.as_view()),
    path('category/list/', CategoryListCreateView.as_view()),
    path('category/<int:pk>/', CategoryDetailView.as_view()),
]
