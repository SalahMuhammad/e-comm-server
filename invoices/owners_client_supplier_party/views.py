from .models import Owner
from .serializers import OwnerSerializers
from rest_framework import generics, mixins


class ListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializers

    def get_queryset(self):
        name_param = self.request.query_params.get('s')

        if name_param:
            q = self.queryset.filter(name__contains=name_param)
            return q

        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class DetailView(
    mixins.RetrieveModelMixin, 
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializers


    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request,*args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        # try:
        return super().destroy(request, *args, **kwargs)
        # except ProtectedError as e:
        #     return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
  

