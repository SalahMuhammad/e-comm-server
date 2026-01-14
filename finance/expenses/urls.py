from django.urls import path
from .views import ExpenseListCreateView, ExpenseDetailView , CategoryListCreateView, CategoryDetailView 


urlpatterns = [
    # Category routes must come before the generic <str:pk> route
    path('category/', CategoryListCreateView.as_view()),
    path('category/list/', CategoryListCreateView.as_view()),
    path('category/<int:pk>/', CategoryDetailView.as_view()),
    # Expense routes
    path('', ExpenseListCreateView.as_view()),
    path('<str:pk>/', ExpenseDetailView.as_view()),
]
