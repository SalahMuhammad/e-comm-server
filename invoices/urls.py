from django.urls import path, include
from .views import InvoicesListView, ListCreateView, DetailView


urlpatterns = [
    # path('', InvoicesListView.as_view()),
    path('', ListCreateView.as_view()),
    path('<int:pk>/', DetailView.as_view()),
]