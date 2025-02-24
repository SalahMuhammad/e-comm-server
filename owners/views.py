from rest_framework.viewsets import ModelViewSet
from rest_framework import status, mixins, generics
from rest_framework.response import Response
from .models import Owner
from .serializers import CustomerSerializers
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from auth.permissions import OwnersPermission



class OwnersViewset(ModelViewSet):
    queryset = Owner.objects.all()
    serializer_class = CustomerSerializers



class ListCreateView(mixins.ListModelMixin, 
               mixins.CreateModelMixin,
               generics.GenericAPIView):
    permission_classes = (OwnersPermission, )
    queryset = Owner.objects.all()
    serializer_class = CustomerSerializers


    def get_queryset(self):
        name_param = self.request.query_params.get('s')

        if name_param:
            q = Owner.objects.filter(name__contains=name_param)
            return q

        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return self.create(request, *args, **kwargs)
        except IntegrityError as e:
            return Response({'name': 'هذا العنصر موجود بالفعل...'}, status=status.HTTP_400_BAD_REQUEST)


class DetailView(mixins.RetrieveModelMixin, 
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 generics.GenericAPIView):
    permission_classes = (OwnersPermission, )
    queryset = Owner.objects.all()
    serializer_class = CustomerSerializers

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request,*args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            return super(DetailView, self).destroy(request, *args, **kwargs)
        except ProtectedError as e:
            return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
  
