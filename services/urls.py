from django.urls import path
from .views import MediaBrowser, CreateDbBackup, CreateItemsAsXLSX



urlpatterns = [
	path('media-browser/', MediaBrowser().as_view()),
    path('create-db-backup/', CreateDbBackup().as_view()),
    path('create-items-as-xlsx/', CreateItemsAsXLSX().as_view()),
]
