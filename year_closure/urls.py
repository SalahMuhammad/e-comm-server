from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClosurePeriodViewSet



router = DefaultRouter()
router.register(r'closure-periods', ClosurePeriodViewSet, basename='closureperiod')

urlpatterns = [
    path('', include(router.urls)),
]
