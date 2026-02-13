"""
FATI Accounts - Serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Permission

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    assigned_region_name = serializers.CharField(
        source='assigned_region.name',
        read_only=True
    )
    assigned_department_name = serializers.CharField(
        source='assigned_department.name',
        read_only=True
    )
    assigned_commune_name = serializers.CharField(
        source='assigned_commune.name',
        read_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'status', 'status_display',
            'organization', 'department', 'phone', 'avatar',
            'assigned_region', 'assigned_region_name',
            'assigned_department', 'assigned_department_name',
            'assigned_commune', 'assigned_commune_name',
            'last_login_at', 'created_at', 'updated_at',
            'is_staff', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'utilisateurs"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password',
            'role', 'status', 'organization', 'department', 'phone',
            'assigned_region', 'assigned_department', 'assigned_commune'
        ]

    def validate_role(self, value):
        # Backward compatibility for legacy frontend payloads.
        if value == 'viewers':
            return User.Role.VIEWER
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'utilisateurs"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'role', 'status',
            'organization', 'department', 'phone',
            'assigned_region', 'assigned_department', 'assigned_commune',
            'is_active'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                "Les mots de passe ne correspondent pas."
            )
        return data


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class TokenSerializer(serializers.Serializer):
    """Serializer pour le token d'authentification"""
    
    token = serializers.CharField()
    user = UserSerializer()


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer pour les permissions"""
    
    class Meta:
        model = Permission
        fields = ['id', 'role', 'resource', 'actions']
