from django.urls import path
from .views import ListCreateView, DetailView


urlpatterns = [
    path('', ListCreateView.as_view(), name='list-create'),
    path('<int:pk>/', DetailView.as_view(), name='detail'),
]
