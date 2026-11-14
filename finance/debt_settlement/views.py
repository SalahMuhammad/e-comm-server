from django.http import Http404
from common.encoder import MixedRadixEncoder
from common.views.CustomQuerysetManager import CustomQuerysetManager
from .models import DebtSettlement
from .serializers import DebtSettlementSerializer
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from .services.filters import DebtSettlementFilter



class ListCreateDebtSettlementView(CustomQuerysetManager, generics.ListCreateAPIView, ):
    CUSTOME_QUERYSET_MANAGER_CONFIG = {
        "model": 					DebtSettlement,
        "select_related_fields": 	('owner', 'by', ),
        "prefetch_related_fields":	(),
    }

    serializer_class = DebtSettlementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DebtSettlementFilter

    
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class DetailDebtSettlementView(CustomQuerysetManager, generics.RetrieveUpdateDestroyAPIView, ):
    CUSTOME_QUERYSET_MANAGER_CONFIG = {
        "model": 					DebtSettlement,
        "select_related_fields": 	('owner', 'by', ),
        "prefetch_related_fields":	(),
    }

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
