from django.http import Http404
# 
from common.encoder import MixedRadixEncoder
# 
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.generics import GenericAPIView
# 
from .models import Expense, Category
from .serializers import ExpensesSerializers, CategorysSerializers
from .services.filters import ExpensesFilter, CategoryFilter
# django filters
from django_filters.rest_framework import DjangoFilterBackend



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
	filter_backends = [DjangoFilterBackend]
	filterset_class = ExpensesFilter


	def get(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user, last_updated_by=self.request.user)



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

	def patch(self, request, *args, **kwargs):
		instance = self.get_object()
		
		# Handle image deletion
		# Use request.data instead of request.POST to handle both JSON and form-data
		keep_image = request.data.get('keep_image', 'true')
		image_file = request.FILES.get('image')
		
		# If keep_image is 'false' and no new file uploaded, delete the existing image
		if keep_image == 'false' and not image_file and instance.image:
			instance.image = None
			instance.save()
		
		return super().partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		return super().destroy(request, *args, **kwargs)

	def perform_update(self, serializer):
		serializer.save(last_updated_by=self.request.user)




# ---------------------------------------------------------------------




class CategoryListCreateView(
	ListModelMixin,
	CreateModelMixin,
	GenericAPIView
):
	queryset = Category.objects.select_related(
		'created_by',
		'last_updated_by',
	).all()
	serializer_class = CategorysSerializers
	filter_backends = [DjangoFilterBackend]
	filterset_class = CategoryFilter


	def get(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)
	
	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user, last_updated_by=self.request.user)



class CategoryDetailView(
	RetrieveModelMixin,
	UpdateModelMixin,
	DestroyModelMixin,
	GenericAPIView
):
	queryset = Category.objects.select_related(
		'created_by',
		'last_updated_by',
	).all()
	serializer_class = CategorysSerializers


	def get(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		return super().partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		from django.db.models.deletion import ProtectedError
		from rest_framework.response import Response
		from rest_framework import status
		
		try:
			return super().destroy(request, *args, **kwargs)
		except ProtectedError:
			return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا ...'}, status=status.HTTP_400_BAD_REQUEST)


	def perform_update(self, serializer):
		serializer.save(last_updated_by=self.request.user)

