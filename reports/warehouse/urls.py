from django.urls import path
from .views import ItemMovementReportView, ItemRepositoryMovementReport

urlpatterns = [
    # path('item-movement-report/', ItemMovementReportView.as_view()),
    path('item-movement-json/', ItemRepositoryMovementReport.as_view(), name='item_movement_api'),
]
