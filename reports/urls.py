from django.urls import path, include

# Create your views here.
urlpatterns = [
    path('warehouse/', include('reports.warehouse.urls'))
]
