from django.http import Http404
# 
from common.encoder import MixedRadixEncoder
from common.utilities import get_pagination_class
# 
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.generics import GenericAPIView
# 
from .models import Expense, Category
from .serializers import ExpensesSerializers, CategorysSerializers



class ExpenseListCreateView(
    ListModelMixin,
    CreateModelMixin,
    GenericAPIView
):
    queryset = Expense.objects.select_related(
        'category',
        'business_account',
        'business_account__account_type',
        'created_by',
        'last_updated_by',
    ).all()
    serializer_class = ExpensesSerializers


    def get_queryset(self):
        queryset = self.queryset
        self.pagination_class = get_pagination_class(self)

        expense_no = self.request.query_params.get('nu')
        if expense_no:
            try:
                id = MixedRadixEncoder().decode(expense_no)  # Validate the encoded ID
            except:
                print(f"Invalid encoded ID: {expense_no}")
			
            if id:
                queryset = queryset.filter(pk=id)

        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name__icontains=category)

        return queryset

    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    # def post(self, request, *args, **kwargs):
    #     return self.create(request, *args, **kwargs)


class ExpenseDetailView(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericAPIView
):
    queryset = Expense.objects.select_related(
        'category',
        'business_account',
        'business_account__account_type',
        'created_by',
        'last_updated_by',
    ).all()
    serializer_class = ExpensesSerializers

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

    # def patch(self, request, *args, **kwargs):
    #     return super().partial_update(request, *args, **kwargs)

    # def delete(self, request, *args, **kwargs):
    #     return super().destroy(request, *args, **kwargs)




# ---------------------------------------------------------------------




class CategoryListCreateView(
    ListModelMixin,
    CreateModelMixin,
    GenericAPIView
):
    queryset = Category.objects.select_related(
        'by',
    ).all()
    serializer_class = CategorysSerializers


    def get_queryset(self):
        queryset = self.queryset

        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=id)

        return queryset

    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class CategoryDetailView(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericAPIView
):
    queryset = Category.objects.select_related(
        'by',
    ).all()
    serializer_class = CategorysSerializers


    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
