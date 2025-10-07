from django.http import Http404
from common.encoder import MixedRadixEncoder
from .models import DebtSettlement
from .serializers import DebtSettlementSerializer
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.generics import GenericAPIView



class ListCreateDebtSettlementView(
    ListModelMixin,
    CreateModelMixin,
    GenericAPIView
):
    queryset = DebtSettlement.objects.select_related(
        'owner',
        'by',
    ).all()
    serializer_class = DebtSettlementSerializer


    def get_queryset(self):
        queryset = self.queryset

        name_param = self.request.query_params.get('owner')
        if name_param:
            queryset = queryset.filter(owner__name__icontains=name_param)

        return queryset
    
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class DetailDebtSettlementView(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericAPIView
):
    queryset = DebtSettlement.objects.select_related(
        'owner',
        'by',
    ).all()
    serializer_class = DebtSettlementSerializer

    def get_object(self):
        encoded_pk = self.kwargs.get('pk')
        try:
            # Decode the encoded ID from URL parameter
            decoded_id = MixedRadixEncoder().decode(str(encoded_pk))
            # Use the decoded ID to get the object
            return self.get_queryset().get(id=decoded_id)
        except Exception as e:
            print(f"Invalid encoded ID: {self.kwargs['pk']}")
            raise Http404("Object not found")

    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
