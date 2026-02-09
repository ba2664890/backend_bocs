"""
FATI Facilities - Serializers
"""
from rest_framework import serializers
from rest_framework_gis.serializers import GeoModelSerializer
from .models import HealthFacility, EducationFacility, Equipment, Staff


class HealthFacilitySerializer(GeoModelSerializer):
    """Serializer pour les structures de santé"""
    
    facility_type_display = serializers.CharField(
        source='get_facility_type_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    
    commune_name = serializers.CharField(source='commune.name', read_only=True)
    department_id = serializers.CharField(source='commune.department.id', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    region_id = serializers.CharField(source='commune.department.region.id', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        model = HealthFacility
        fields = [
            'id', 'code', 'name',
            'facility_type', 'facility_type_display',
            'category', 'category_display',
            'commune', 'commune_name',
            'department_id', 'department_name',
            'region_id', 'region_name',
            'location', 'address',
            'phone', 'email', 'manager_name',
            'bed_capacity', 'services',
            'is_active',
            'created_at', 'updated_at'
        ]


class EducationFacilitySerializer(GeoModelSerializer):
    """Serializer pour les établissements d'enseignement"""
    
    facility_type_display = serializers.CharField(
        source='get_facility_type_display',
        read_only=True
    )
    level_display = serializers.CharField(
        source='get_level_display',
        read_only=True
    )
    
    commune_name = serializers.CharField(source='commune.name', read_only=True)
    department_id = serializers.CharField(source='commune.department.id', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    region_id = serializers.CharField(source='commune.department.region.id', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        model = EducationFacility
        fields = [
            'id', 'code', 'name',
            'facility_type', 'facility_type_display',
            'level', 'level_display',
            'commune', 'commune_name',
            'department_id', 'department_name',
            'region_id', 'region_name',
            'location', 'address',
            'phone', 'email', 'principal_name',
            'student_capacity',
            'is_active',
            'created_at', 'updated_at'
        ]


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer pour l'équipement"""
    
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    facility_name = serializers.CharField(
        source='health_facility.name',
        read_only=True
    )
    
    class Meta:
        model = Equipment
        fields = [
            'id', 'health_facility', 'facility_name',
            'name', 'category', 'category_display',
            'quantity', 'functional', 'non_functional',
            'last_updated'
        ]


class StaffSerializer(serializers.ModelSerializer):
    """Serializer pour le personnel"""
    
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    facility_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = [
            'id', 'category', 'category_display',
            'total', 'filled', 'vacant',
            'last_updated', 'facility_name'
        ]
    
    def get_facility_name(self, obj):
        facility = obj.health_facility or obj.education_facility
        return facility.name if facility else None
