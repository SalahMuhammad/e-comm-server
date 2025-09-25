from django.urls import path
from .views import ItemsList, ItemDetail, quantity_errors_corrector_view, quantity_errors_list_view, TypesList, ItemFluctuation


urlpatterns = [
  path('', ItemsList.as_view(), name='items-list'),
  path('<int:pk>/', ItemDetail.as_view(), name='item-detail'),
  path('<int:pk>/fluctuation/', ItemFluctuation.as_view(), name='item-fluctuation'),
  path('quantity-errors-list/', quantity_errors_list_view, name='quantity-errors-list'),
  path('quantity-errors-corrector/', quantity_errors_corrector_view, name='quantity-errors-corrector'),
  path('types/', TypesList.as_view(), name='item-types-list'),
  # path('getbarcode/', handle_barcode_image),
  # path('initial-stock/<int:pk>/', aaaa, name='update-initial-stock'),
]
