from django.urls import path
from .views import ListCreateRefundedRefillableItemsView, DetialRefundedRefillableItemsView, ListCreateRefilledItemsView, DetialRefilledItemsView, ListItemTransformer, ListOreItem, ownersHasRefillableItems


urlpatterns = [
    path('refunded-items/', ListCreateRefundedRefillableItemsView.as_view(), name='refillable_items'),
    path('refunded-items/<int:pk>/', DetialRefundedRefillableItemsView.as_view(), name='refillable_items'),
    path('refilled-items/', ListCreateRefilledItemsView.as_view(), name='refilled_items'),
    path('refilled-items/<int:pk>/', DetialRefilledItemsView.as_view(), name='refilled_items'),
    
    path('item-transformer/', ListItemTransformer.as_view()),
    path('ore-item/', ListOreItem.as_view()),

    path('refillable-items-owners-has/', ownersHasRefillableItems),
]
