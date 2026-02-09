"""
FATI Geography - Serializers
"""
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Region, Department, Commune


class RegionSerializer(GeoFeatureModelSerializer):
    """Serializer pour les régions"""
    
    departments_count = serializers.IntegerField(source='departments.count', read_only=True)
    communes_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Region
        geo_field = 'geometry'
        fields = [
            'id', 'code', 'name', 'geometry', 'centroid',
            'population', 'area_km2', 'metadata',
            'departments_count', 'communes_count',
            'created_at', 'updated_at'
        ]


class RegionListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de régions"""
    
    departments_count = serializers.IntegerField(source='departments.count', read_only=True)
    
    class Meta:
        model = Region
        fields = [
            'id', 'code', 'name', 'centroid', 'geometry',
            'population', 'departments_count'
        ]


class DepartmentSerializer(GeoFeatureModelSerializer):
    """Serializer pour les départements"""
    
    region_name = serializers.CharField(source='region.name', read_only=True)
    communes_count = serializers.IntegerField(source='communes.count', read_only=True)
    
    class Meta:
        model = Department
        geo_field = 'geometry'
        fields = [
            'id', 'code', 'name', 'region', 'region_name',
            'geometry', 'centroid',
            'population', 'area_km2', 'metadata',
            'communes_count',
            'created_at', 'updated_at'
        ]


class DepartmentListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de départements"""
    
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'code', 'name', 'region', 'region_name',
            'centroid', 'geometry', 'population'
        ]


class CommuneSerializer(GeoFeatureModelSerializer):
    """Serializer pour les communes"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    region_name = serializers.CharField(source='department.region.name', read_only=True)
    
    class Meta:
        model = Commune
        geo_field = 'geometry'
        fields = [
            'id', 'code', 'name', 'department', 'department_name',
            'region_name', 'geometry', 'centroid',
            'population', 'area_km2', 'metadata',
            'created_at', 'updated_at'
        ]


class CommuneListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de communes"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Commune
        fields = [
            'id', 'code', 'name', 'department', 'department_name',
            'centroid', 'geometry', 'population'
        ]


class GeographicHierarchySerializer(serializers.Serializer):
    """Serializer pour la hiérarchie géographique complète"""
    
    regions = RegionListSerializer(many=True)
