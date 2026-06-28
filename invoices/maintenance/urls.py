from django.urls import path
from .views import MaintenanceView, MaintenanceDetailView

urlpatterns = [
    path('', MaintenanceView.as_view(), name='maintenance-list-create'),
    # path('', MaintenanceView.as_view(), name='transactionspareparts-list'),
    path('<str:pk>/', MaintenanceDetailView.as_view(), name='maintenance-detail'),
]
