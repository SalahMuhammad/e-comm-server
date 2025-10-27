from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.mixins import (
    ListModelMixin, 
    CreateModelMixin, 
    UpdateModelMixin,
    RetrieveModelMixin, 
    DestroyModelMixin
)
# 
from refillable_items_system.models import ItemTransformer, OreItem, RefundedRefillableItem, RefilledItem
from invoices.buyer_supplier_party.models import Party
from items.models import Stock
# 
from .serializers import RefundedRefillableItemSerializer, RefilledItemSerializer, ItemTransformerSerializer, OreItemSerializer, CustomDataSerializer
# 
from .management.commands.generateCansClientHasReport import get_cans_data_list
# 
from .services.calculate_refillable_items_client_has import calculateRefillableItemsClientHas
# 
from common.utilities import get_pagination_class
# 
from django.db import transaction
from django.db.models.deletion import ProtectedError
from decimal import Decimal
# 
import logging

logger = logging.getLogger(__name__)



@api_view(['GET'])
def ownersHasRefillableItems(request, *args, **kwargs):
    owners = Party.objects.all()

    list = []
    for owner in owners:
        a = calculateRefillableItemsClientHas(client_id=owner.id)

        if a:
            list.append({
                "id": owner.id,
                "owner": owner.name,
                "cylinders": a
            })
    
    return Response({
        "data": list
    })


class GetCansClientHasReport(generics.ListAPIView):
    # serializer_class = CustomDataSerializer


    def get_queryset(self):
            self.request
            id = self.kwargs.get('pk')
            try:
                owner = Party.objects.get(pk=id)
            except Exception as e:
                return []
            data = get_cans_data_list(id)
            # Replace this with your actual data retrieval logic
            return {
                "owner_name": owner.name,
                "results": data
            }

    
    def get(self, request, *args, **kwargs):
        return Response(self.get_queryset())
        # def get(self, request, *args, **kwargs):
        #     id = kwargs['pk']
        #     try:
        #         owner = Party.objects.get(pk=id)
        #     except Party.DoesNotExist:
        #         return Response({"detail": "invalid owner id."}, status=404)

        #     try:
        #         command = ["python3", "manage.py", "generateCansClientHasReport", str(id)]
                
        #         result = subprocess.run(
        #             command, 
        #             # cwd=settings.BASE_DIR, 
        #             capture_output=True, 
        #             text=True, 
        #             timeout=300  # 5 minute timeout
        #         )
                
        #         # Log the output for debugging
        #         logger.info(f"Command stdout: {result.stdout}")
        #         if result.stderr:
        #             logger.error(f"Command stderr: {result.stderr}")
                
        #         # Check if command was successful
        #         if result.returncode != 0:
        #             error_msg = f"Report generation failed: {result.stderr}"
        #             logger.error(error_msg)
        #             return Response({
        #                 "detail": "Report generation failed",
        #                 "error": result.stderr
        #             }, status=500)
                
        #         # Assuming your command outputs the PDF file path
        #         file_name = result.stdout.strip().split('\n')[-1] # Get last line
        #         pdf_file_path = os.path.join(f'media/reports/{owner.name}', file_name)
                
        #         # Check if PDF file exists
        #         if not os.path.exists(pdf_file_path):
        #             return Response({
        #                 "detail": "PDF file was not generated"
        #             }, status=500)
                
        #         # Return the PDF file
        #         response = FileResponse(
        #             open(pdf_file_path, 'rb'),
        #             content_type='application/pdf',
        #             filename=file_name
        #         )
        #         return response
                
        #     except subprocess.TimeoutExpired:
        #         return Response({
        #             "detail": "Report generation timed out"
        #         }, status=500)
                
        #     except Exception as e:
        #         logger.error(f"Unexpected error: {str(e)}")
        #         return Response({
        #             "detail": "An unexpected error occurred",
        #             "error": str(e)
        #         }, status=500)




# ------------------------------------




class ListCreateRefundedRefillableItemsView(
    ListModelMixin,
    CreateModelMixin,
    generics.GenericAPIView
):
    serializer_class = RefundedRefillableItemSerializer
    queryset = RefundedRefillableItem.objects.select_related(
        'item',
        'repository',
        'owner',
        'by'
    ).all()
    
    def get_queryset(self):
        queryset = self.queryset

        name_param = self.request.query_params.get('ownerid')
        if name_param:
            return queryset.filter(owner_id=name_param)
        
        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            stock, cretated = Stock.objects.get_or_create(
                repository_id=serializer.data['repository'],
                item_id=serializer.data['item']
            )
            stock.adjust_stock(Decimal(serializer.data['quantity']))

            return Response(serializer.data, status=201)


class DetialRefundedRefillableItemsView(
    RetrieveModelMixin,
    DestroyModelMixin,
    generics.GenericAPIView
):
    queryset = RefundedRefillableItem.objects.select_related(
        'item',
        'repository',
        'owner',
        'by'
    ).all()
    serializer_class = RefundedRefillableItemSerializer


    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        with transaction.atomic():
            stock = Stock.objects.get(
                repository=instance.repository,
                item=instance.item
            )
            stock.adjust_stock(- Decimal(instance.quantity))

            return super().destroy(request, *args, **kwargs)




# ------------------------------------




class ListCreateRefilledItemsView(
    ListModelMixin,
    CreateModelMixin,
    generics.GenericAPIView
):
    queryset = RefilledItem.objects.select_related(
        'refilled_item',
        'used_item__item',
        'repository',
        'by',
        'employee'
    ).all()
    serializer_class = RefilledItemSerializer


    def get_queryset(self):
        self.pagination_class = get_pagination_class(self)
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        if from_date and to_date:
            return self.queryset.filter(date__range=(from_date, to_date))
        
        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            item_transofrmer = ItemTransformer.objects.filter(item=serializer.data['refilled_item']).first()

            filled_stock, cretated = Stock.objects.get_or_create(
                repository_id=serializer.data['repository'],
                item=item_transofrmer.transform
            )
            filled_stock.adjust_stock(Decimal(serializer.data['refilled_quantity']))

            refilled_stock, cretated = Stock.objects.get_or_create(
                repository_id=serializer.data['repository'],
                item=item_transofrmer.item
            )
            refilled_stock.adjust_stock(- Decimal(serializer.data['refilled_quantity']))

            used_stock, cretated = Stock.objects.get_or_create(
                repository_id=serializer.data['repository'],
                item=OreItem.objects.get(id=serializer.data['used_item']).item
            )
            used_stock.adjust_stock(- Decimal(serializer.data['used_quantity']))
            
            return Response(serializer.data, status=201)


class DetialRefilledItemsView(
    RetrieveModelMixin,
    DestroyModelMixin,
    generics.GenericAPIView
):
    queryset = RefilledItem.objects.select_related(
        'refilled_item',
        'used_item__item',
        'repository',
        'by',
        'employee'
    ).all()
    serializer_class = RefilledItemSerializer


    def get_queryset(self):
        queryset = self.queryset

        name_param = self.request.query_params.get('employee')
        if name_param:
            return queryset.filter(employee_id=name_param)
        
        return self.queryset
    

    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        with transaction.atomic():
            item_transofrmer = ItemTransformer.objects.get(item=instance.refilled_item)

            filled_stock, cretated = Stock.objects.get_or_create(
                repository=instance.repository,
                item=item_transofrmer.transform
            )
            filled_stock.adjust_stock(- Decimal(instance.refilled_quantity))

            refilled_stock, cretated = Stock.objects.get_or_create(
                repository=instance.repository,
                item=item_transofrmer.item
            )
            refilled_stock.adjust_stock(Decimal(instance.refilled_quantity))

            used_stock, cretated = Stock.objects.get_or_create(
                repository=instance.repository,
                item=instance.used_item.item
            )
            used_stock.adjust_stock(Decimal(instance.used_quantity))
            
            return super().destroy(request, *args, **kwargs)




# ------------------------------------




class ListItemTransformer(
    ListModelMixin,
    generics.GenericAPIView
):
    queryset = ItemTransformer.objects.select_related(
        'item',
        'transform'
    ).all()
    serializer_class = ItemTransformerSerializer


    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)




# ------------------------------------




class ListCreateOreItem(
    ListModelMixin,
    CreateModelMixin,
    generics.GenericAPIView
):
    queryset = OreItem.objects.select_related(
        'item',
        'by',
    ).all()
    serializer_class = OreItemSerializer


    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class OreItemDetailView(
    RetrieveModelMixin, 
    UpdateModelMixin,
    DestroyModelMixin,
    generics.GenericAPIView
):
    queryset = OreItem.objects.select_related(
        'item',
        'by',
    ).all()
    serializer_class = OreItemSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request,*args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            return super(OreItemDetailView, self).destroy(request, *args, **kwargs)
        except ProtectedError as e:
            return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
  
