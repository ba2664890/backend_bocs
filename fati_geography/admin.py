"""
FATI Geography - Admin Configuration
"""
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Region, Department, Commune


@admin.register(Region)
class RegionAdmin(GISModelAdmin):
    """Configuration admin pour les régions"""
    
    list_display = ['code', 'name', 'population', 'created_at']
    search_fields = ['code', 'name']
    ordering = ['code']
    
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 6,
            'default_lon': -14.5,
            'default_lat': 14.5,
        }
    }


@admin.register(Department)
class DepartmentAdmin(GISModelAdmin):
    """Configuration admin pour les départements"""
    
    list_display = ['code', 'name', 'region', 'population', 'created_at']
    list_filter = ['region']
    search_fields = ['code', 'name', 'region__name']
    ordering = ['region__code', 'code']
    
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 8,
            'default_lon': -14.5,
            'default_lat': 14.5,
        }
    }


@admin.register(Commune)
class CommuneAdmin(GISModelAdmin):
    """Configuration admin pour les communes"""
    
    list_display = ['code', 'name', 'department', 'population', 'created_at']
    list_filter = ['department__region', 'department']
    search_fields = ['code', 'name', 'department__name', 'department__region__name']
    ordering = ['department__region__code', 'department__code', 'code']
    
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 10,
            'default_lon': -14.5,
            'default_lat': 14.5,
        }
    }
