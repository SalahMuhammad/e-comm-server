from django.urls import path
from .views import ProfitPercentage

urlpatterns = [
    path('', ProfitPercentage.as_view()),
]