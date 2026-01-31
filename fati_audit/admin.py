"""
FATI Audit - Admin Configuration
"""
from django.contrib import admin
from .models import AuditLog, DataQualityCheck, SystemMetric


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Configuration admin pour les journaux d'audit"""
    
    list_display = [
        'user_name', 'action', 'entity_type',
        'entity_name', 'created_at'
    ]
    list_filter = ['action', 'entity_type', 'created_at']
    search_fields = [
        'user_name', 'user_email', 'entity_type',
        'entity_name'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'user_name', 'user_role')
        }),
        ('Action', {
            'fields': ('action', 'entity_type', 'entity_id', 'entity_name')
        }),
        ('Modifications', {
            'fields': ('old_values', 'new_values')
        }),
        ('Technique', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Date', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = [
        'user', 'user_name', 'user_role', 'action',
        'entity_type', 'entity_id', 'entity_name',
        'old_values', 'new_values', 'ip_address',
        'user_agent', 'created_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(DataQualityCheck)
class DataQualityCheckAdmin(admin.ModelAdmin):
    """Configuration admin pour les vérifications de qualité"""
    
    list_display = [
        'indicator_value', 'check_type',
        'status', 'created_at'
    ]
    list_filter = ['check_type', 'status']
    search_fields = ['indicator_value__indicator__name', 'message']
    ordering = ['-created_at']


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    """Configuration admin pour les métriques système"""
    
    list_display = [
        'metric_name', 'metric_value',
        'dimension_1', 'dimension_2', 'timestamp'
    ]
    list_filter = ['metric_name']
    search_fields = ['metric_name', 'dimension_1', 'dimension_2']
    ordering = ['-timestamp']
