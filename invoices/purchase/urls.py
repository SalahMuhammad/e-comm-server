from django.urls import path
from .views import ListCreateView, DetailView, toggle_repository_permit


urlpatterns = [
    path('', ListCreateView.as_view(), name='list-create'),
    path('<int:pk>/', DetailView.as_view(), name='detail'),
    path('<int:pk>/change-repository-permit/', toggle_repository_permit, name='detail'),
]
