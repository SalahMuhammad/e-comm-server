from django.urls import path
from .views import ListCreate


urlpatterns = [
    path('', ListCreate.as_view()),
]