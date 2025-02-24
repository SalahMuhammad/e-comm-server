from rest_framework import serializers
from .models import Owner


class CustomerSerializers(serializers.ModelSerializer):
    by_username = serializers.ReadOnlyField(source='by.username')


    class Meta:
        model = Owner
        fields = '__all__'
