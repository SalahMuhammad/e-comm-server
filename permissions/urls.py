from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PermissionViewSet, GroupViewSet

router = DefaultRouter()
# Register groups first, then permissions with a specific prefix
# This prevents the empty string from catching all routes
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'permissions', PermissionViewSet, basename='permission')


urlpatterns = [
    path('', include(router.urls)),
]
