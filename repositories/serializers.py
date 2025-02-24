from rest_framework import serializers
from .models import Repositories


class RepositoriesSerializers(serializers.ModelSerializer):
    by_username = serializers.ReadOnlyField(source='by.username')


    class Meta:
        model = Repositories
        fields = '__all__'

    # def get_by_username(self, obj):
    #     return obj.by.username