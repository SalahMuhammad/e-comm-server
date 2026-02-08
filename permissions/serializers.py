from rest_framework import serializers
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Django Permission model"""
    app_label = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'app_label', 'model_name']
        
    def get_app_label(self, obj):
        return obj.content_type.app_label if obj.content_type else None
        
    def get_model_name(self, obj):
        return obj.content_type.model if obj.content_type else None


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Django Group model with nested permissions"""
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permission_count']
        
    def get_permission_count(self, obj):
        return obj.permissions.count()


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating groups with permission assignment"""
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        required=False
    )
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']
    
    def validate_permissions(self, value):
        """Filter out None values from permissions"""
        if not value:
            return []
        
        # PrimaryKeyRelatedField already converts IDs to Permission objects
        # Just filter out None values
        return [perm for perm in value if perm is not None]
        
    def create(self, validated_data):
        permissions = validated_data.pop('permissions', [])
        group = Group.objects.create(**validated_data)
        group.permissions.set(permissions)
        return group
        
    def update(self, instance, validated_data):
        permissions = validated_data.pop('permissions', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        
        if permissions is not None:
            instance.permissions.set(permissions)
            
        return instance
