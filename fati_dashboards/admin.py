"""
FATI Dashboards - Admin Configuration
"""
from django.contrib import admin
from .models import Dashboard, Widget, ReportTemplate, GeneratedReport


class WidgetInline(admin.TabularInline):
    """Inline pour les widgets"""
    model = Widget
    extra = 0
    fields = [
        'name', 'type', 'position_x', 'position_y',
        'width', 'height', 'is_active'
    ]


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Configuration admin pour les tableaux de bord"""
    
    list_display = [
        'name', 'type', 'owner', 'is_default',
        'is_shared', 'is_active', 'created_at'
    ]
    list_filter = ['type', 'is_default', 'is_shared', 'is_active']
    search_fields = ['name', 'description', 'owner__email']
    ordering = ['-created_at']
    inlines = [WidgetInline]


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    """Configuration admin pour les widgets"""
    
    list_display = [
        'name', 'dashboard', 'type',
        'position_x', 'position_y', 'is_active'
    ]
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'dashboard__name']


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Configuration admin pour les modèles de rapport"""
    
    list_display = ['name', 'sector', 'is_active', 'created_at']
    list_filter = ['sector', 'is_active']
    search_fields = ['name', 'description']


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    """Configuration admin pour les rapports générés"""
    
    list_display = [
        'name', 'template', 'format',
        'status', 'generated_by', 'generated_at'
    ]
    list_filter = ['status', 'format', 'generated_at']
    search_fields = ['name', 'template__name', 'generated_by__email']
    ordering = ['-generated_at']
    
    readonly_fields = ['generated_at']
