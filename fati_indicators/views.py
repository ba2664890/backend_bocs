"""
FATI Indicators - Views
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Max, Min, Count, Q
from .models import Indicator, IndicatorValue, IndicatorHistory
from .serializers import (
    IndicatorSerializer,
    IndicatorValueSerializer,
    IndicatorValueCreateSerializer,
    IndicatorValueUpdateSerializer,
    IndicatorHistorySerializer,
    IndicatorSummarySerializer
)


class IndicatorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les indicateurs"""
    
    queryset = Indicator.objects.filter(is_active=True)
    serializer_class = IndicatorSerializer
    filterset_fields = ['sector', 'category', 'type']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['sector', 'category', 'order', 'name']
    
    @action(detail=False, methods=['get'])
    def by_sector(self, request):
        """Récupérer les indicateurs groupés par secteur"""
        health_indicators = self.queryset.filter(sector='health')
        education_indicators = self.queryset.filter(sector='education')
        
        return Response({
            'health': IndicatorSerializer(health_indicators, many=True).data,
            'education': IndicatorSerializer(education_indicators, many=True).data
        })
    
    @action(detail=True, methods=['get'])
    def values(self, request, pk=None):
        """Récupérer les valeurs d'un indicateur"""
        indicator = self.get_object()
        values = indicator.values.all()
        
        # Filtrer par année
        year = request.query_params.get('year')
        if year:
            values = values.filter(year=year)
        
        # Filtrer par région
        region = request.query_params.get('region')
        if region:
            values = values.filter(region__code=region)
        
        # Filtrer par statut
        status = request.query_params.get('status')
        if status:
            values = values.filter(status=status)
        
        serializer = IndicatorValueSerializer(values, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Récupérer un résumé de l'indicateur"""
        indicator = self.get_object()
        
        # Dernière valeur
        latest = indicator.values.filter(status='validated').order_by('-year').first()
        
        # Valeurs par année pour la tendance
        yearly_values = indicator.values.filter(
            status='validated'
        ).values('year').annotate(
            avg_value=Avg('value')
        ).order_by('year')
        
        # Calculer la tendance
        trend = 'stable'
        if len(yearly_values) >= 2:
            recent = yearly_values[-1]['avg_value']
            previous = yearly_values[-2]['avg_value']
            if previous > 0:
                change = ((recent - previous) / previous) * 100
                if change > 5:
                    trend = 'increasing'
                elif change < -5:
                    trend = 'decreasing'
        
        return Response({
            'indicator': IndicatorSerializer(indicator).data,
            'latest_value': latest.value if latest else None,
            'latest_year': latest.year if latest else None,
            'achievement_rate': latest.achievement_rate if latest else None,
            'yearly_data': list(yearly_values),
            'trend': trend
        })


class IndicatorValueViewSet(viewsets.ModelViewSet):
    """ViewSet pour les valeurs d'indicateurs"""
    
    queryset = IndicatorValue.objects.select_related(
        'indicator', 'region', 'department', 'commune', 'validated_by'
    ).all()
    serializer_class = IndicatorValueSerializer
    filterset_fields = [
        'indicator', 'indicator__sector',
        'region', 'department', 'commune',
        'year', 'period', 'status'
    ]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['year', 'value', 'created_at']
    ordering = ['-year', 'indicator__name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return IndicatorValueCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return IndicatorValueUpdateSerializer
        return IndicatorValueSerializer
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        user = self.request.user
        queryset = self.queryset
        
        # Filtrer par territoire assigné pour les contributeurs
        if user.is_contributor or user.is_local_manager:
            if user.assigned_commune:
                queryset = queryset.filter(commune=user.assigned_commune)
            elif user.assigned_department:
                queryset = queryset.filter(department=user.assigned_department)
            elif user.assigned_region:
                queryset = queryset.filter(region=user.assigned_region)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Valider une valeur d'indicateur"""
        value = self.get_object()
        
        # Vérifier les permissions
        if not (request.user.is_admin or request.user.is_institution or 
                request.user.role in ['sector_health', 'sector_education']):
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        value.status = 'validated'
        value.validated_by = request.user
        from django.utils import timezone
        value.validated_at = timezone.now()
        value.save()
        
        serializer = IndicatorValueSerializer(value)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejeter une valeur d'indicateur"""
        value = self.get_object()
        
        # Vérifier les permissions
        if not (request.user.is_admin or request.user.is_institution):
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        value.status = 'rejected'
        value.save()
        
        serializer = IndicatorValueSerializer(value)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Récupérer les valeurs en attente de validation"""
        values = self.get_queryset().filter(status='pending')
        serializer = IndicatorValueSerializer(values, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques globales des indicateurs"""
        
        # Par secteur
        health_stats = IndicatorValue.objects.filter(
            indicator__sector='health',
            status='validated'
        ).aggregate(
            count=Count('id'),
            avg_achievement=Avg('achievement_rate')
        )
        
        education_stats = IndicatorValue.objects.filter(
            indicator__sector='education',
            status='validated'
        ).aggregate(
            count=Count('id'),
            avg_achievement=Avg('achievement_rate')
        )
        
        # Par statut
        status_counts = IndicatorValue.objects.values('status').annotate(
            count=Count('id')
        )
        
        return Response({
            'health': health_stats,
            'education': education_stats,
            'by_status': list(status_counts)
        })
    
    @action(detail=False, methods=['get'])
    def compare(self, request):
        """Comparer les valeurs entre territoires"""
        indicator_id = request.query_params.get('indicator')
        year = request.query_params.get('year')
        
        if not indicator_id or not year:
            return Response(
                {'error': 'Les paramètres indicator et year sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        values = self.queryset.filter(
            indicator_id=indicator_id,
            year=year,
            status='validated'
        ).select_related('region')
        
        data = []
        for value in values:
            data.append({
                'region_id': value.region.id if value.region else None,
                'region_name': value.region.name if value.region else None,
                'value': value.value,
                'achievement_rate': value.achievement_rate
            })
        
        return Response(data)


class IndicatorHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour l'historique des indicateurs"""
    
    queryset = IndicatorHistory.objects.select_related(
        'indicator_value', 'changed_by'
    ).all()
    serializer_class = IndicatorHistorySerializer
    
    def get_queryset(self):
        indicator_value_id = self.request.query_params.get('indicator_value')
        if indicator_value_id:
            return self.queryset.filter(indicator_value_id=indicator_value_id)
        return self.queryset
