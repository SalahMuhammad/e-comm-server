from django.urls import path
from .views import ListCreateView, DetailView


urlpatterns = [
    path('', ListCreateView().as_view(), name='clients'),
    path('<int:pk>/', DetailView().as_view(), name='client'),
]
