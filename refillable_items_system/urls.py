from django.urls import path
from .views import ListCreateRefundedRefillableItemsView, DetialRefundedRefillableItemsView, ListCreateRefilledItemsView, DetialRefilledItemsView


urlpatterns = [
    path('refunded-items/', ListCreateRefundedRefillableItemsView.as_view(), name='refillable_items'),
    path('refunded-items/<int:pk>/', DetialRefundedRefillableItemsView.as_view(), name='refillable_items'),
    path('refilled-items/', ListCreateRefilledItemsView.as_view(), name='refilled_items'),
    path('refilled-items/<int:pk>/', DetialRefilledItemsView.as_view(), name='refilled_items'),
]
