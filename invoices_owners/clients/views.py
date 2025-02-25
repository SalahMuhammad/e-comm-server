from .models import Clients
from .serializers import ClientsSerializers
from common.views import AbstractInvoicesOwnersListCreateView, AbstractInvoicesOwnersDetailView


class ListCreateView(AbstractInvoicesOwnersListCreateView):
    queryset = Clients.objects.all()
    serializer_class = ClientsSerializers


class DetailView(AbstractInvoicesOwnersDetailView):
    queryset = Clients.objects.all()
    serializer_class = ClientsSerializers

