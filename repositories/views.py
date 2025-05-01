from rest_framework import viewsets, mixins, generics, status
from rest_framework.response import Response

from auth.permissions import RepositoryPermission
from .models import Repositories
from .serializers import RepositoriesSerializers
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError





# class RepositoriesViewset(viewsets.ModelViewSet):
#     queryset = Repositories.objects.all()
#     serializer_class = RepositoriesSerializers


class ListCreateView(mixins.ListModelMixin, 
               mixins.CreateModelMixin,
               generics.GenericAPIView):
    permission_classes = (RepositoryPermission, )
    queryset = Repositories.objects.all()
    serializer_class = RepositoriesSerializers


    def get_queryset(self):
        name_param = self.request.query_params.get('s')

        if name_param:
            q = Repositories.objects.filter(name__icontains=name_param)
            return q

        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return self.create(request, *args, **kwargs)
        except IntegrityError as e:
            print(e)
            return Response({'name': 'هذا الصنف موجود بالفعل...'}, status=status.HTTP_400_BAD_REQUEST)


class DetailView(mixins.RetrieveModelMixin, 
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 generics.GenericAPIView):
    permission_classes = (RepositoryPermission, )
    queryset = Repositories.objects.all()
    serializer_class = RepositoriesSerializers

    def get(self, request, *args, **kwargs):
        # import time
        # from itertools import count
        # from multiprocessing import Process
        # def inc_forever():
        #     print('Starting function inc_forever()...')
        #     while True:
        #         time.sleep(1)
        #         print(next(counter))
        # def return_zero():
        #     print('Starting function return_zero()...')
        #     return 0

        # counter = count(0)
        # p1 = Process(target=inc_forever, name='Process_inc_forever')
        # p2 = Process(target=return_zero, name='Process_return_zero')
        # p1.start()
        # p2.start()
        # p1.join(timeout=2)
        # p2.join(timeout=2)
        # p1.terminate()
        # p2.terminate()
        # if p1.exitcode is None:
        #     print(f'Oops, {p1} timeouts!')
        # if p2.exitcode == 0:
        #     print(f'{p2} is luck and finishes in 5 seconds!')
        return self.retrieve(request, *args, **kwargs)

    def put(self, request,*args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            return super(DetailView, self).destroy(request, *args, **kwargs)
        except ProtectedError as e:
            return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
  
