from django.urls import path
from .views import MediaBrowser, CreateDbBackup, CreateItemsAsXLSX, RestoreDbBackup, BackupConfigView



urlpatterns = [
	path('media-browser/', MediaBrowser().as_view()),
    path('create-db-backup/', CreateDbBackup().as_view()),
    path('restore-db-backup/', RestoreDbBackup().as_view()),
    path('create-items-as-xlsx/', CreateItemsAsXLSX().as_view()),
    path('backup-config/', BackupConfigView().as_view()),
]
