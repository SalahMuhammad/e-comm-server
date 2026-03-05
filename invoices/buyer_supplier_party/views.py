from .serializers import PartySerializers
# 
from rest_framework.decorators import api_view
from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
# models
from .models import Party
# services 
from .services.owner_account_statement import getOwnerAccountStatementAsHttpResponse
from .services.owners_credit_balance import getOwnersCreditBalanceAsHttpResponse
from .services.ownerView import ownerViewAsHttpResponse
# 
from django.db.models import ProtectedError



class OwnerView(APIView):
    permission_classes = (AllowAny, )


    def get(self, request, *args, **kwargs):
        return ownerViewAsHttpResponse(
            request.GET.get('date', None),
            kwargs['pk'],
        )


class ListClientCredits(APIView):
    permission_classes = (AllowAny, )

    
    def get(self, request, *args, **kwargs):
        return getOwnersCreditBalanceAsHttpResponse()



@api_view(['GET'])
def customerAccountStatement(request, *args, **kwargs):
    return getOwnerAccountStatementAsHttpResponse(kwargs['pk'])



class ListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset = Party.objects.select_related(
        'by'
    ).all()
    serializer_class = PartySerializers

    def get_queryset(self):
        name_param = self.request.query_params.get('s')
        pk_param = self.request.query_params.get('pk')

        if name_param:
            q = self.queryset.filter(name__icontains=name_param)
            return q
        if pk_param:
            q = self.queryset.filter(id=pk_param)
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
    queryset = Party.objects.select_related(
        'by'
    ).all()
    serializer_class = PartySerializers


    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request,*args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as e:
            return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
  

