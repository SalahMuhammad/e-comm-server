from django.urls import path
# from .views import get_sales_for_owner
from .views import ListCreateView, DetailView

urlpatterns = [
    # path('get_sales_for_owner/', get_sales_for_owner, name='get_sales_for_owner'),
    path('', ListCreateView.as_view()),
    path('<str:pk>/', DetailView.as_view())
]
