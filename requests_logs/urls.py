from django.urls import path
from .views import RequestLogViewSet
from rest_framework.routers import DefaultRouter

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'', RequestLogViewSet, basename='requestlog')
urlpatterns = [
    # The API URLs are now determined automatically by the router.
]
urlpatterns += router.urls # type: ignore
