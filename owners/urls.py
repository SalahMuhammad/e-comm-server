from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import OwnersViewset
from .views import ListCreateView, DetailView


# route1 = DefaultRouter()
# route1.register(r'', OwnersViewset, basename='owners')


urlpatterns = [
    # path('customers/', include(route1.urls)),
    path('', ListCreateView().as_view()),
    path('<int:pk>/', DetailView().as_view()),
]