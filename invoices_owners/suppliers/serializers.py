from rest_framework import serializers
from .models import Suppliers


class SuppliersSerializers(serializers.ModelSerializer):
    by_username = serializers.ReadOnlyField(source='by.username')


    class Meta:
        model = Suppliers
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True}
        }
