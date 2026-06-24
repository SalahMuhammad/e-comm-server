from rest_framework import serializers
from .models import Employee


class EmployeeSerializers(serializers.ModelSerializer):
    obj_representation = serializers.SerializerMethodField()


    class Meta:
        model = Employee
        fields = '__all__'

    def get_obj_representation(self, obj):
        return obj.first_name + ' ' + obj.last_name
