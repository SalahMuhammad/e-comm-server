from django.urls import path
from .views import ItemsList, ItemDetail, aaaa#, handle_barcode_image


urlpatterns = [
  path('', ItemsList.as_view(), name='items-list'),
  path('<int:pk>/', ItemDetail.as_view(), name='item-detail'),
  # path('getbarcode/', handle_barcode_image),
  # path('initial-stock/<int:pk>/', aaaa, name='update-initial-stock'),
]
