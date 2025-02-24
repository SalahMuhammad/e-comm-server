from django.urls import path, include
# from rest_framework.routers import DefaultRouter
from .views import ListCreateView, DetailView


# route = DefaultRouter()
# route.register(r'', RepositoriesViewset, basename='repositories')


urlpatterns = [
	# path('', include(route.urls)),
	path('', ListCreateView().as_view()),
	path('<int:pk>/', DetailView().as_view()),
]
