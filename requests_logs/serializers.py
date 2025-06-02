from rest_framework import serializers
from .models import RequestLog


class RequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestLog
        fields = '__all__'
        extra_kwargs = {
            # 'by': {'write_only': True},
            'headers': {'write_only': True},
            'body': {'write_only': True},
        }
