from django.urls import path
from .views import ListCreateView


urlpatterns = [
    path('', ListCreateView.as_view()),
]
