from .serializers import PaymentMethodSerializer
from rest_framework import generics, mixins, status
from rest_framework.response import Response
from .models import PaymentMethod


class PaymentMethodListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer


    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class PaymentMethodDetailView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


def balance_correction(request, pk):
    try:
        money_vault = PaymentMethod.objects.get(pk=pk)
    except PaymentMethod.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    money_vault.balance = 0
    money_vault.save()
    return Response(status=status.HTTP_200_OK)