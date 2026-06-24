from .models import Employee
from .serializers import EmployeeSerializers
from rest_framework import mixins, generics
from django_filters.rest_framework import DjangoFilterBackend
from .services.filters import EmployeeFilter


class ListCreate(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset = Employee.objects.select_related('by').all()
    serializer_class = EmployeeSerializers
    # Adding filtering backends
    filter_backends = [DjangoFilterBackend]
    filterset_class = EmployeeFilter


    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
