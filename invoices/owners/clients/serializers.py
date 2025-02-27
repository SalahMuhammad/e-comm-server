from rest_framework import serializers
from .models import Clients


class ClientsSerializers(serializers.ModelSerializer):
    by_username = serializers.ReadOnlyField(source='by.username')


    class Meta:
        model = Clients
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True}
        }
