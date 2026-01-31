"""
FATI Geography - Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Region, Department, Commune
from .serializers import (
    RegionSerializer,
    RegionListSerializer,
    DepartmentSerializer,
    DepartmentListSerializer,
    CommuneSerializer,
    CommuneListSerializer
)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les régions"""
    
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    lookup_field = 'code'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RegionListSerializer
        return RegionSerializer
    
    @action(detail=True, methods=['get'])
    def departments(self, request, code=None):
        """Récupérer les départements d'une région"""
        region = self.get_object()
        departments = region.departments.all()
        serializer = DepartmentListSerializer(departments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def communes(self, request, code=None):
        """Récupérer les communes d'une région"""
        region = self.get_object()
        communes = Commune.objects.filter(department__region=region)
        serializer = CommuneListSerializer(communes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """Récupérer la hiérarchie géographique complète"""
        regions = Region.objects.prefetch_related(
            'departments__communes'
        ).all()
        
        data = []
        for region in regions:
            region_data = {
                'id': region.id,
                'code': region.code,
                'name': region.name,
                'departments': []
            }
            for dept in region.departments.all():
                dept_data = {
                    'id': dept.id,
                    'code': dept.code,
                    'name': dept.name,
                    'communes': [
                        {
                            'id': c.id,
                            'code': c.code,
                            'name': c.name
                        }
                        for c in dept.communes.all()
                    ]
                }
                region_data['departments'].append(dept_data)
            data.append(region_data)
        
        return Response(data)


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les départements"""
    
    queryset = Department.objects.select_related('region').all()
    serializer_class = DepartmentSerializer
    lookup_field = 'code'
    filterset_fields = ['region']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DepartmentListSerializer
        return DepartmentSerializer
    
    @action(detail=True, methods=['get'])
    def communes(self, request, code=None):
        """Récupérer les communes d'un département"""
        department = self.get_object()
        communes = department.communes.all()
        serializer = CommuneListSerializer(communes, many=True)
        return Response(serializer.data)


class CommuneViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les communes"""
    
    queryset = Commune.objects.select_related(
        'department__region'
    ).all()
    serializer_class = CommuneSerializer
    lookup_field = 'code'
    filterset_fields = ['department', 'department__region']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CommuneListSerializer
        return CommuneSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Rechercher des communes par nom"""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response(
                {'error': 'La recherche doit contenir au moins 2 caractères'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        communes = self.queryset.filter(name__icontains=query)[:20]
        serializer = CommuneListSerializer(communes, many=True)
        return Response(serializer.data)
