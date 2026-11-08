from rest_framework import serializers
from .models import ClosurePeriod
from common.serializers.utils.audit_info_dateformatter import audit_info_dateformatter



class ClosurePeriodSerializer(serializers.ModelSerializer):
    _audit_info = serializers.SerializerMethodField()


    class Meta:
        model = ClosurePeriod
        fields = ['id', 'from_date', 'to_date', 'is_locked', '_audit_info']

    def get__audit_info(self, obj):
        return audit_info_dateformatter(obj)
