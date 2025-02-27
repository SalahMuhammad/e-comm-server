from .models import Suppliers
from .serializers import SuppliersSerializers
from common.views import AbstractInvoicesOwnersListCreateView, AbstractInvoicesOwnersDetailView


class ListCreateView(AbstractInvoicesOwnersListCreateView):
    queryset = Suppliers.objects.all()
    serializer_class = SuppliersSerializers


class DetailView(AbstractInvoicesOwnersDetailView):
    queryset = Suppliers.objects.all()
    serializer_class = SuppliersSerializers

