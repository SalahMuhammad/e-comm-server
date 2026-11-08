from rest_framework import viewsets
from .models import ClosurePeriod
from .serializers import ClosurePeriodSerializer
from .services.lock_logic import locked_year_closure_logic, unlocked_year_closure_logic



class ClosurePeriodViewSet(viewsets.ModelViewSet):
    queryset = ClosurePeriod.objects.all()
    serializer_class = ClosurePeriodSerializer


    def perform_create(self, serializer):
        is_locked = serializer.validated_data.get('is_locked')
        
        if is_locked:
            locked_year_closure_logic(serializer.instance)

        serializer.save(
            created_by=self.request.user,
            last_updated_by=self.request.user
        )

    def perform_update(self, serializer):
        is_locked = serializer.validated_data.get('is_locked')

        unlocked_year_closure_logic(serializer.instance)

        if is_locked:
            locked_year_closure_logic(serializer.instance)

        serializer.save(
            last_updated_by=self.request.user
        )
