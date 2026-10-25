from django.urls import path
from .views import MediaBrowser, CreateDbBackup, CreateItemsAsXLSX, RestoreDbBackup, BackupConfigView, ConfigurationRetrieveUpdateAPIView#, RequestLogManagerView
from services.my_views.RequestLogManagerView import RequestLogManagerView
from services.my_views.ItemInventorySummaryAPIView import ItemInventorySummaryAPIView
from services.my_views.ItemInventorySummaryAPIViewFromCSV.InventorySummaryAPIView import InventorySummaryAPIView, InventoryDetailAPIView


urlpatterns = [
    path('inventory-summary/', ItemInventorySummaryAPIView.as_view(), name='inventory-summary'),
    path('inventory-summary-from-csvs/', InventorySummaryAPIView.as_view(), name='inventory-summary'),
    path('inventory/detailed/<path:safe_item_name>/', InventoryDetailAPIView.as_view(), name='inventory-detail-api'),

	path('media-browser/', MediaBrowser().as_view()),
    path('create-db-backup/', CreateDbBackup().as_view()),
    path('restore-db-backup/', RestoreDbBackup().as_view()),
    path('create-items-as-xlsx/', CreateItemsAsXLSX().as_view()),
    path('backup-config/', BackupConfigView().as_view()),

    path(
        "configuration/",
        ConfigurationRetrieveUpdateAPIView.as_view(),
        {'___view_id': 'services_configuration'},
        name="app-configuration",
    ),



    path('logs/', RequestLogManagerView.as_view(), name='request-log-list'),
    
    # Retrieve single file content or Delete a specific file (e.g., /api/logs/post/salah_2026-03-30_...json/)
    path('logs/<str:method>/<str:filename>/', RequestLogManagerView.as_view(), name='request-log-detail'),
]
