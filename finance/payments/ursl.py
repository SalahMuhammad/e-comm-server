from django.urls import path
from .views import ListCreateView


urlpatterns = [
    path('', ListCreateView.as_view(), name='ursl-list-create'),
    # path('ursl/<int:pk>/', ListCreateView.as_view(), name='ursl-detail'),
]