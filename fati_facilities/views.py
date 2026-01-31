"""
FATI Facilities - Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import HealthFacility, EducationFacility, Equipment, Staff
from .serializers import (
    HealthFacilitySerializer,
    EducationFacilitySerializer,
    EquipmentSerializer,
    StaffSerializer
)


class HealthFacilityViewSet(viewsets.ModelViewSet):
    """ViewSet pour les structures de santé"""
    
    queryset = HealthFacility.objects.select_related('commune').all()
    serializer_class = HealthFacilitySerializer
    filterset_fields = ['facility_type', 'category', 'commune', 'is_active']
    filter_backends = [DjangoFilterBackend]
    search_fields = ['name', 'code', 'address']
    
    @action(detail=True, methods=['get'])
    def equipment(self, request, pk=None):
        """Récupérer l'équipement d'une structure"""
        facility = self.get_object()
        equipment = facility.equipment.all()
        serializer = EquipmentSerializer(equipment, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def staff(self, request, pk=None):
        """Récupérer le personnel d'une structure"""
        facility = self.get_object()
        staff = facility.staff.all()
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_region(self, request):
        """Récupérer les structures par région"""
        region_code = request.query_params.get('region')
        if not region_code:
            return Response(
                {'error': 'Le paramètre region est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facilities = self.queryset.filter(
            commune__department__region__code=region_code
        )
        serializer = HealthFacilitySerializer(facilities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques des structures de santé"""
        total = self.queryset.count()
        by_type = self.queryset.values('facility_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'total': total,
            'by_type': list(by_type)
        })


class EducationFacilityViewSet(viewsets.ModelViewSet):
    """ViewSet pour les établissements d'enseignement"""
    
    queryset = EducationFacility.objects.select_related('commune').all()
    serializer_class = EducationFacilitySerializer
    filterset_fields = ['facility_type', 'level', 'commune', 'is_active']
    filter_backends = [DjangoFilterBackend]
    search_fields = ['name', 'code', 'address']
    
    @action(detail=True, methods=['get'])
    def staff(self, request, pk=None):
        """Récupérer le personnel d'un établissement"""
        facility = self.get_object()
        staff = facility.staff.all()
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_region(self, request):
        """Récupérer les établissements par région"""
        region_code = request.query_params.get('region')
        if not region_code:
            return Response(
                {'error': 'Le paramètre region est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facilities = self.queryset.filter(
            commune__department__region__code=region_code
        )
        serializer = EducationFacilitySerializer(facilities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques des établissements"""
        total = self.queryset.count()
        by_type = self.queryset.values('facility_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'total': total,
            'by_type': list(by_type)
        })


class EquipmentViewSet(viewsets.ModelViewSet):
    """ViewSet pour l'équipement"""
    
    queryset = Equipment.objects.select_related('health_facility').all()
    serializer_class = EquipmentSerializer
    filterset_fields = ['category', 'health_facility']


class StaffViewSet(viewsets.ModelViewSet):
    """ViewSet pour le personnel"""
    
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    filterset_fields = ['category']


# Import manquant
from django.db.models import Count
