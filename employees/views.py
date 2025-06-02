from .models import Employee
from .serializers import EmployeeSerializers
from rest_framework import mixins, generics


class ListCreate(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializers


    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
