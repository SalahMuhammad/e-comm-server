from django.urls import path
from .views import FileDownloadView, DirectoryBrowseView

urlpatterns = [
    # # List available file system roots
    # path('', views.FileSystemListView.as_view(), name='filesystem-roots'),
    
    # # Browse directory contents
    # path('browse/', DirectoryBrowseView.as_view(), name='browse-directory'),
    
    # Download file
    path('download/', FileDownloadView.as_view(), name='download-file'),
    
    # # Get file info
    # path('info/', views.FileInfoView.as_view(), name='file-info'),
    
    # # Search files
    # path('search/', views.FileSearchView.as_view(), name='search-files'),
]
