"""
FATI Accounts - Admin Configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Permission


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Configuration admin pour les utilisateurs"""
    
    list_display = [
        'email', 'first_name', 'last_name', 'role',
        'assigned_region', 'is_active', 'last_login'
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Rôle et territoire'), {
            'fields': ('role', 'assigned_region', 'assigned_department')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Configuration admin pour les permissions"""
    
    list_display = ['role', 'resource', 'actions']
    list_filter = ['role', 'resource']
    search_fields = ['role', 'resource']
