from rest_framework import serializers
from .models import AppConfiguration



class ConfigSerializer(serializers.ModelSerializer):


    class Meta:
        model = AppConfiguration
        fields = '__all__'

