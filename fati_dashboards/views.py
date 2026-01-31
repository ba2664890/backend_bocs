"""
FATI Dashboards - Views
"""
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Dashboard, Widget, ReportTemplate, GeneratedReport
from .serializers import (
    DashboardSerializer,
    DashboardCreateSerializer,
    WidgetSerializer,
    WidgetCreateSerializer,
    DashboardShareSerializer,
    ReportTemplateSerializer,
    GeneratedReportSerializer,
    ReportGenerateSerializer,
    DashboardDataSerializer
)


class DashboardViewSet(viewsets.ModelViewSet):
    """ViewSet pour les tableaux de bord"""
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type', 'is_default', 'is_active']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les dashboards visibles par l'utilisateur"""
        user = self.request.user
        
        # Superusers voient tout
        if user.is_superuser:
            return Dashboard.objects.all()
        
        # Dashboards de l'utilisateur ou partagés
        return Dashboard.objects.filter(
            Q(owner=user) | Q(is_shared=True) | Q(shared_with=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DashboardCreateSerializer
        return DashboardSerializer
    
    def perform_create(self, serializer):
        """Créer un dashboard avec l'utilisateur comme propriétaire"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Partager un dashboard avec d'autres utilisateurs"""
        dashboard = self.get_object()
        serializer = DashboardShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        dashboard.shared_with.add(*user_ids)
        dashboard.is_shared = True
        dashboard.save()
        
        return Response({
            'message': f'Dashboard partagé avec {len(user_ids)} utilisateur(s)'
        })
    
    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """Retirer le partage d'un dashboard"""
        dashboard = self.get_object()
        dashboard.shared_with.clear()
        dashboard.is_shared = False
        dashboard.save()
        
        return Response({'message': 'Partage retiré'})
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Dupliquer un dashboard"""
        original = self.get_object()
        
        # Créer une copie
        new_dashboard = Dashboard.objects.create(
            name=f"{original.name} (Copie)",
            description=original.description,
            type=original.type,
            layout_config=original.layout_config,
            default_filters=original.default_filters,
            owner=request.user
        )
        
        # Copier les widgets
        for widget in original.widgets.all():
            Widget.objects.create(
                dashboard=new_dashboard,
                name=widget.name,
                type=widget.type,
                position_x=widget.position_x,
                position_y=widget.position_y,
                width=widget.width,
                height=widget.height,
                config=widget.config,
                data_source=widget.data_source,
                filters=widget.filters,
                refresh_interval=widget.refresh_interval
            )
        
        return Response(
            DashboardSerializer(new_dashboard).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """Récupérer les données pour le dashboard"""
        dashboard = self.get_object()
        
        # Récupérer les filtres
        filters = dashboard.default_filters.copy()
        filters.update(request.query_params.dict())
        
        # Collecter les données de tous les widgets
        widgets_data = []
        for widget in dashboard.widgets.filter(is_active=True):
            widget_data = self._get_widget_data(widget, filters)
            widgets_data.append({
                'widget_id': widget.id,
                'widget_name': widget.name,
                'widget_type': widget.type,
                'data': widget_data
            })
        
        return Response({
            'dashboard_id': dashboard.id,
            'dashboard_name': dashboard.name,
            'widgets_data': widgets_data
        })
    
    def _get_widget_data(self, widget, filters):
        """Récupérer les données pour un widget spécifique"""
        from fati_indicators.models import Indicator, IndicatorValue
        from fati_workflows.models import Alert
        from fati_facilities.models import Facility
        
        widget_type = widget.type
        
        if widget_type == 'kpi':
            # KPI simple
            indicator_id = widget.config.get('indicator_id')
            if indicator_id:
                try:
                    indicator = Indicator.objects.get(id=indicator_id)
                    values = IndicatorValue.objects.filter(
                        indicator=indicator,
                        validation_status='validated'
                    )
                    if filters.get('region'):
                        values = values.filter(region_id=filters['region'])
                    
                    latest = values.order_by('-period').first()
                    if latest:
                        return {
                            'value': latest.value,
                            'period': latest.period,
                            'trend': self._calculate_trend(values)
                        }
                except Indicator.DoesNotExist:
                    pass
            return {'value': None}
        
        elif widget_type == 'alert_list':
            # Liste d'alertes
            alerts = Alert.objects.filter(is_read=False)
            if filters.get('severity'):
                alerts = alerts.filter(severity=filters['severity'])
            if filters.get('region'):
                alerts = alerts.filter(region_id=filters['region'])
            
            return {
                'alerts': list(alerts.values(
                    'id', 'title', 'severity', 'created_at'
                )[:10]),
                'total': alerts.count()
            }
        
        elif widget_type == 'facility_list':
            # Liste de structures
            facilities = Facility.objects.filter(is_active=True)
            if filters.get('region'):
                facilities = facilities.filter(region_id=filters['region'])
            if filters.get('type'):
                facilities = facilities.filter(type_id=filters['type'])
            
            return {
                'facilities': list(facilities.values(
                    'id', 'name', 'type__name', 'region__name'
                )[:20]),
                'total': facilities.count()
            }
        
        return {}
    
    def _calculate_trend(self, values_qs):
        """Calculer la tendance d'un indicateur"""
        values = list(values_qs.order_by('-period')[:2])
        if len(values) < 2:
            return 'stable'
        
        if values[0].value > values[1].value:
            return 'up'
        elif values[0].value < values[1].value:
            return 'down'
        return 'stable'


class WidgetViewSet(viewsets.ModelViewSet):
    """ViewSet pour les widgets"""
    queryset = Widget.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WidgetCreateSerializer
        return WidgetSerializer
    
    def get_queryset(self):
        """Filtrer par dashboard si spécifié"""
        queryset = Widget.objects.all()
        dashboard_id = self.request.query_params.get('dashboard')
        if dashboard_id:
            queryset = queryset.filter(dashboard_id=dashboard_id)
        return queryset


class ReportTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les modèles de rapport"""
    queryset = ReportTemplate.objects.filter(is_active=True)
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['sector']
    search_fields = ['name', 'description']


class GeneratedReportViewSet(viewsets.ModelViewSet):
    """ViewSet pour les rapports générés"""
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['template', 'status', 'format']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']
    
    def get_queryset(self):
        """Filtrer les rapports de l'utilisateur"""
        user = self.request.user
        if user.is_superuser:
            return GeneratedReport.objects.all()
        return GeneratedReport.objects.filter(generated_by=user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Générer un nouveau rapport"""
        serializer = ReportGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        template_id = serializer.validated_data['template_id']
        
        try:
            template = ReportTemplate.objects.get(id=template_id)
        except ReportTemplate.DoesNotExist:
            return Response(
                {'error': 'Modèle de rapport non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Créer le rapport en attente
        report = GeneratedReport.objects.create(
            template=template,
            name=serializer.validated_data['name'],
            parameters=serializer.validated_data['parameters'],
            format=serializer.validated_data['format'],
            generated_by=request.user,
            status=GeneratedReport.Status.PENDING
        )
        
        # TODO: Lancer la génération asynchrone (Celery)
        # Pour l'instant, on simule la génération
        report.status = GeneratedReport.Status.COMPLETED
        report.save()
        
        return Response(
            GeneratedReportSerializer(report).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Régénérer un rapport"""
        report = self.get_object()
        report.status = GeneratedReport.Status.PENDING
        report.save()
        
        # TODO: Lancer la régénération asynchrone
        report.status = GeneratedReport.Status.COMPLETED
        report.save()
        
        return Response(GeneratedReportSerializer(report).data)


class DashboardDataViewSet(viewsets.ViewSet):
    """ViewSet pour les données de dashboard"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Récupérer les données pour le dashboard principal"""
        from fati_indicators.models import Indicator, IndicatorValue
        from fati_workflows.models import Alert
        from fati_facilities.models import Facility
        from fati_accounts.models import User
        from fati_geography.models import Region
        from fati_audit.models import AuditLog
        
        # Filtres
        sector = request.query_params.get('sector')
        region_id = request.query_params.get('region')
        
        # KPIs globaux
        indicators_qs = Indicator.objects.filter(is_active=True)
        if sector:
            indicators_qs = indicators_qs.filter(sector=sector)
        
        values_qs = IndicatorValue.objects.filter(
            validation_status='validated'
        )
        if sector:
            values_qs = values_qs.filter(indicator__sector=sector)
        if region_id:
            values_qs = values_qs.filter(region_id=region_id)
        
        # Statistiques
        kpis = [
            {
                'title': 'Indicateurs',
                'value': indicators_qs.count(),
                'icon': 'chart-bar'
            },
            {
                'title': 'Points de données',
                'value': values_qs.count(),
                'icon': 'database'
            },
            {
                'title': 'Structures',
                'value': Facility.objects.filter(is_active=True).count(),
                'icon': 'building'
            },
            {
                'title': 'Alertes',
                'value': Alert.objects.filter(is_read=False).count(),
                'icon': 'bell',
                'alert': True
            }
        ]
        
        # Données de carte
        regions_data = []
        for region in Region.objects.all():
            region_values = values_qs.filter(region=region)
            regions_data.append({
                'region_id': region.id,
                'region_name': region.name,
                'data_points': region_values.count(),
                'value': region_values.order_by('-period').first().value if region_values.exists() else None
            })
        
        # Activité récente
        recent_activity = AuditLog.objects.all()[:10]
        activity_data = [
            {
                'user': log.user_name,
                'action': log.action,
                'entity': log.entity_name or log.entity_type,
                'time': log.created_at
            }
            for log in recent_activity
        ]
        
        data = {
            'kpis': kpis,
            'map_data': {
                'regions': regions_data
            },
            'recent_activity': activity_data
        }
        
        return Response(data)
