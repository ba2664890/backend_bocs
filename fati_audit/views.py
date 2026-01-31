"""
FATI Audit - Views
"""
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog, DataQualityCheck, SystemMetric
from .serializers import (
    AuditLogSerializer,
    AuditLogCreateSerializer,
    DataQualityCheckSerializer,
    SystemMetricSerializer,
    DashboardStatsSerializer
)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les journaux d'audit"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'entity_type', 'user', 'user_role']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Récupérer les activités récentes"""
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        logs = self.get_queryset().filter(created_at__gte=since)[:50]
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_entity(self, request):
        """Récupérer les logs groupés par type d'entité"""
        stats = self.get_queryset().values('entity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        return Response(list(stats))
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Récupérer les logs groupés par utilisateur"""
        stats = self.get_queryset().values(
            'user', 'user_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        return Response(list(stats))
    
    @action(detail=False, methods=['post'])
    def log_action(self, request):
        """Créer une entrée de journal"""
        serializer = AuditLogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        log = AuditLog.log(
            user=request.user,
            action=serializer.validated_data['action'],
            entity_type=serializer.validated_data['entity_type'],
            entity_id=serializer.validated_data['entity_id'],
            entity_name=serializer.validated_data.get('entity_name', ''),
            old_values=serializer.validated_data.get('old_values', {}),
            new_values=serializer.validated_data.get('new_values', {}),
            request=request
        )
        
        return Response(
            AuditLogSerializer(log).data,
            status=status.HTTP_201_CREATED
        )


class DataQualityCheckViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les vérifications de qualité"""
    queryset = DataQualityCheck.objects.all()
    serializer_class = DataQualityCheckSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['check_type', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumer la qualité des données"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        passed = queryset.filter(status=DataQualityCheck.Status.PASSED).count()
        warning = queryset.filter(status=DataQualityCheck.Status.WARNING).count()
        failed = queryset.filter(status=DataQualityCheck.Status.FAILED).count()
        
        # Score de qualité
        if total > 0:
            quality_score = (passed * 100 + warning * 50) / total
        else:
            quality_score = 100
        
        return Response({
            'total': total,
            'passed': passed,
            'warning': warning,
            'failed': failed,
            'quality_score': round(quality_score, 2)
        })
    
    @action(detail=False, methods=['get'])
    def by_indicator(self, request):
        """Qualité des données par indicateur"""
        stats = self.get_queryset().values(
            'indicator_value__indicator__name'
        ).annotate(
            total=Count('id'),
            passed=Count('id', filter=Q(status=DataQualityCheck.Status.PASSED)),
            failed=Count('id', filter=Q(status=DataQualityCheck.Status.FAILED))
        )
        return Response(list(stats))


class SystemMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les métriques système"""
    queryset = SystemMetric.objects.all()
    serializer_class = SystemMetricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['metric_name']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Statistiques pour le tableau de bord"""
        from fati_accounts.models import User
        from fati_indicators.models import Indicator, IndicatorValue
        from fati_facilities.models import Facility
        
        # Statistiques de base
        total_users = User.objects.filter(is_active=True).count()
        total_indicators = Indicator.objects.filter(is_active=True).count()
        total_facilities = Facility.objects.filter(is_active=True).count()
        total_data_points = IndicatorValue.objects.count()
        
        # Activités récentes
        recent_activities = AuditLog.objects.all()[:10]
        
        # Score de qualité
        quality_checks = DataQualityCheck.objects.all()
        if quality_checks.exists():
            passed = quality_checks.filter(
                status=DataQualityCheck.Status.PASSED
            ).count()
            quality_score = (passed / quality_checks.count()) * 100
        else:
            quality_score = 100
        
        data = {
            'total_users': total_users,
            'total_indicators': total_indicators,
            'total_facilities': total_facilities,
            'total_data_points': total_data_points,
            'recent_activities': AuditLogSerializer(recent_activities, many=True).data,
            'quality_score': round(quality_score, 2)
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def time_series(self, request):
        """Récupérer les métriques en série temporelle"""
        metric_name = request.query_params.get('metric_name')
        hours = int(request.query_params.get('hours', 24))
        
        since = timezone.now() - timedelta(hours=hours)
        queryset = self.get_queryset().filter(
            timestamp__gte=since
        )
        
        if metric_name:
            queryset = queryset.filter(metric_name=metric_name)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StatsViewSet(viewsets.ViewSet):
    """ViewSet pour les statistiques globales"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Statistiques globales du système"""
        from fati_accounts.models import User
        from fati_indicators.models import Indicator, IndicatorValue
        from fati_facilities.models import Facility
        from fati_geography.models import Region
        from fati_workflows.models import Alert
        
        # Comptages
        stats = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'by_role': list(User.objects.values('role').annotate(
                    count=Count('id')
                ))
            },
            'indicators': {
                'total': Indicator.objects.count(),
                'health': Indicator.objects.filter(sector='health').count(),
                'education': Indicator.objects.filter(sector='education').count()
            },
            'facilities': {
                'total': Facility.objects.count(),
                'health': Facility.objects.filter(type__sector='health').count(),
                'education': Facility.objects.filter(type__sector='education').count()
            },
            'data': {
                'total_points': IndicatorValue.objects.count(),
                'validated': IndicatorValue.objects.filter(
                    validation_status='validated'
                ).count(),
                'pending': IndicatorValue.objects.filter(
                    validation_status='pending'
                ).count()
            },
            'geography': {
                'regions': Region.objects.count()
            },
            'alerts': {
                'total': Alert.objects.count(),
                'unread': Alert.objects.filter(is_read=False).count(),
                'critical': Alert.objects.filter(severity='critical').count()
            }
        }
        
        return Response(stats)
