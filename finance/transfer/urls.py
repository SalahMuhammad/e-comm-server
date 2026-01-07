from django.urls import path
from .views import ListCreateView, DetailView


urlpatterns = [
    path('', ListCreateView.as_view()),
    path('<str:pk>/', DetailView.as_view())
]
