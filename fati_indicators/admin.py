"""
FATI Indicators - Admin Configuration
"""
from django.contrib import admin
from .models import Indicator, IndicatorValue, IndicatorHistory


class IndicatorValueInline(admin.TabularInline):
    """Inline pour les valeurs d'indicateur"""
    model = IndicatorValue
    extra = 0
    fields = ['region', 'year', 'period', 'value', 'status']
    readonly_fields = ['created_at']


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    """Configuration admin pour les indicateurs"""
    
    list_display = [
        'code', 'name', 'sector', 'category',
        'type', 'unit', 'is_active'
    ]
    list_filter = ['sector', 'category', 'type', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'name', 'description', 'sector')
        }),
        ('Classification', {
            'fields': ('category', 'type', 'unit')
        }),
        ('Configuration', {
            'fields': (
                'formula', 'denominator',
                'target_value', 'alert_threshold'
            )
        }),
        ('Statut', {
            'fields': ('is_active', 'order', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [IndicatorValueInline]


@admin.register(IndicatorValue)
class IndicatorValueAdmin(admin.ModelAdmin):
    """Configuration admin pour les valeurs d'indicateur"""
    
    list_display = [
        'indicator', 'region', 'department', 'commune',
        'year', 'value', 'status', 'created_at'
    ]
    list_filter = [
        'indicator__sector', 'status',
        'year', 'region'
    ]
    search_fields = [
        'indicator__name', 'indicator__code',
        'notes', 'source'
    ]
    ordering = ['-year', '-created_at']
    
    fieldsets = (
        ('Informations', {
            'fields': ('indicator', 'region', 'department', 'commune', 'year', 'period')
        }),
        ('Valeur', {
            'fields': ('value', 'previous_value', 'target_value', 'notes')
        }),
        ('Calculs', {
            'fields': ('variation', 'achievement_rate')
        }),
        ('Validation', {
            'fields': (
                'status', 'validated_by', 'validated_at'
            )
        }),
        ('Métadonnées', {
            'fields': ('source', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'validated_at', 'variation', 'achievement_rate']


@admin.register(IndicatorHistory)
class IndicatorHistoryAdmin(admin.ModelAdmin):
    """Configuration admin pour l'historique des indicateurs"""
    
    list_display = ['indicator_value', 'old_value', 'new_value', 'changed_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['indicator_value__indicator__name', 'change_reason']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
