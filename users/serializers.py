from rest_framework import serializers
from .models import User


class UserSerializers(serializers.ModelSerializer):

  def create(self, validated_data):
    password = validated_data.pop('password', None)
    instance = self.Meta.model(**validated_data)
    
    if password is not None:
      instance.set_password(password)
    instance.save()

    return instance


  class Meta:
    model = User
    fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 'avatar', 'remove_avatar']
    extra_kwargs = {
      'password': {'write_only': True},
      'avatar': {'required': False, 'allow_null': True}
    }

  remove_avatar = serializers.BooleanField(write_only=True, required=False, default=False)

  def update(self, instance, validated_data):
    remove_avatar = validated_data.pop('remove_avatar', False)
    if remove_avatar:
      instance.avatar = None
    
    return super().update(instance, validated_data)
