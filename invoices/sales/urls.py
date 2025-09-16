from django.urls import path
from .views import ListCreateView, DetailView, toggle_repository_permit, ReturnListCreateView, RefundDetailView


urlpatterns = [
    path('', ListCreateView.as_view(), name='list-create'),
    path('<str:pk>/', DetailView.as_view(), name='detail'),
    path('<str:pk>/change-repository-permit/', toggle_repository_permit, name='detail'),
    path('s/refund/', ReturnListCreateView.as_view(), name='return-list-create'),
    path('s/refund/<str:pk>/', RefundDetailView.as_view(), name='refund-detail'),
]
