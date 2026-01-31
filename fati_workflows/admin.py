"""
FATI Workflows - Admin Configuration
"""
from django.contrib import admin
from .models import WorkflowDefinition, WorkflowInstance, WorkflowStep, Alert


class WorkflowStepInline(admin.TabularInline):
    """Inline pour les étapes de workflow"""
    model = WorkflowStep
    extra = 0
    fields = ['name', 'order', 'assigned_role', 'status', 'completed_at']
    readonly_fields = ['created_at']


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    """Configuration admin pour les définitions de workflow"""
    
    list_display = ['name', 'entity_type', 'is_active', 'created_at']
    list_filter = ['entity_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-created_at']


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    """Configuration admin pour les instances de workflow"""
    
    list_display = [
        'workflow_definition', 'entity_type', 'entity_id',
        'current_status', 'current_step', 'initiated_by', 'created_at'
    ]
    list_filter = ['current_status', 'workflow_definition__entity_type']
    search_fields = [
        'workflow_definition__name', 'entity_type', 'entity_id'
    ]
    ordering = ['-created_at']
    inlines = [WorkflowStepInline]


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    """Configuration admin pour les étapes de workflow"""
    
    list_display = [
        'workflow', 'name', 'order',
        'assigned_role', 'status', 'completed_at'
    ]
    list_filter = ['status', 'assigned_role']
    search_fields = ['name', 'workflow__workflow_definition__name']
    ordering = ['workflow', 'order']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Configuration admin pour les alertes"""
    
    list_display = [
        'title', 'type', 'severity', 'sector',
        'is_read', 'created_at'
    ]
    list_filter = ['type', 'severity', 'sector', 'is_read']
    search_fields = ['title', 'message']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations', {
            'fields': ('type', 'severity', 'title', 'message')
        }),
        ('Contexte', {
            'fields': ('sector', 'indicator', 'region', 'value', 'threshold')
        }),
        ('Lecture', {
            'fields': ('is_read', 'read_at', 'read_by')
        }),
        ('Destinataires', {
            'fields': ('recipients',)
        }),
    )
    
    readonly_fields = ['created_at', 'read_at']
    filter_horizontal = ['recipients']
