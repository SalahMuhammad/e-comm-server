from rest_framework import serializers
from users.models import User
from django.contrib.auth.models import Group, Permission


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for user list view"""
    groups = serializers.StringRelatedField(many=True)
    permission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar', 'is_active', 'is_staff', 'is_superuser', 'groups', 'permission_count', 'date_joined']
        
    def get_permission_count(self, obj):
        """Get total permission count (groups + user permissions)"""
        group_perms = obj.groups.values_list('permissions', flat=True)
        user_perms = obj.user_permissions.values_list('id', flat=True)
        return len(set(list(group_perms) + list(user_perms)))


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user retrieval"""
    groups = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'avatar', 'is_active', 'is_superuser', 'is_staff',
            'groups', 'user_permissions', 'date_joined', 'last_login',
            'password_change_required'
        ]
        
    def get_groups(self, obj):
        """Get groups with their permissions"""
        return [
            {
                'id': group.id,
                'name': group.name,
                'permission_count': group.permissions.count()
            }
            for group in obj.groups.all()
        ]
        
    def get_user_permissions(self, obj):
        """Get direct user permissions"""
        return [
            {
                'id': perm.id,
                'name': perm.name,
                'codename': perm.codename
            }
            for perm in obj.user_permissions.all()
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users with groups and permissions"""
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False
    )
    user_permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        required=False
    )
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'first_name', 'last_name', 'avatar', 'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions'
        ]
        extra_kwargs = {
             'avatar': {'required': False, 'allow_null': True}
        }
        


    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        user_permissions = validated_data.pop('user_permissions', [])
        password = validated_data.pop('password')
        
        # Create user with password_change_required=True
        user = User.objects.create(
            **validated_data,
            password_change_required=True
        )
        user.set_password(password)
        user.save()
        
        # Set groups and permissions
        user.groups.set(groups)
        user.user_permissions.set(user_permissions)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False
    )
    user_permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        required=False
    )
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'first_name', 'last_name', 'avatar', 'remove_avatar', 
            'clear_groups', 'clear_permissions', 'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions'
        ]
        extra_kwargs = {
             'avatar': {'required': False, 'allow_null': True}
        }

    remove_avatar = serializers.BooleanField(write_only=True, required=False, default=False)
    clear_groups = serializers.BooleanField(write_only=True, required=False, default=False)
    clear_permissions = serializers.BooleanField(write_only=True, required=False, default=False)
        
    def update(self, instance, validated_data):
        groups = validated_data.pop('groups', None)
        user_permissions = validated_data.pop('user_permissions', None)
        password = validated_data.pop('password', None)
        remove_avatar = validated_data.pop('remove_avatar', False)
        clear_groups = validated_data.pop('clear_groups', False)
        clear_permissions = validated_data.pop('clear_permissions', False)

        if remove_avatar:
            instance.avatar = None
        
        # Update basic fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
            
        # Update password if provided
        if password:
            instance.set_password(password)
            instance.password_change_required = True
            
        instance.save()
        
        # Update groups and permissions if provided
        if clear_groups:
             instance.groups.clear()
        elif groups is not None:
            instance.groups.set(groups)

        if clear_permissions:
            instance.user_permissions.clear()
        elif user_permissions is not None:
            instance.user_permissions.set(user_permissions)
            
        return instance
