"""
FATI Workflows - Views
"""
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import WorkflowDefinition, WorkflowInstance, WorkflowStep, Alert
from .serializers import (
    WorkflowDefinitionSerializer,
    WorkflowInstanceSerializer,
    WorkflowInstanceCreateSerializer,
    WorkflowStepSerializer,
    AlertSerializer,
    WorkflowTransitionSerializer,
    AlertMarkReadSerializer
)


class WorkflowDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les définitions de workflow"""
    queryset = WorkflowDefinition.objects.filter(is_active=True)
    serializer_class = WorkflowDefinitionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['entity_type']
    search_fields = ['name', 'description']


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les instances de workflow"""
    queryset = WorkflowInstance.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['current_status', 'entity_type', 'workflow_definition']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WorkflowInstanceCreateSerializer
        return WorkflowInstanceSerializer
    
    def perform_create(self, serializer):
        """Créer une instance et initialiser les étapes"""
        instance = serializer.save(initiated_by=self.request.user)
        
        # Créer les étapes du workflow
        steps_config = instance.workflow_definition.steps_config
        for i, step_config in enumerate(steps_config):
            WorkflowStep.objects.create(
                workflow=instance,
                name=step_config.get('name', f'Étape {i + 1}'),
                order=i,
                assigned_role=step_config.get('role', 'contributor')
            )
    
    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Transitionner le workflow vers un nouveau statut"""
        instance = self.get_object()
        serializer = WorkflowTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_name = serializer.validated_data['action']
        comments = serializer.validated_data.get('comments', '')
        
        # Mapping des actions vers les statuts
        status_mapping = {
            'submit': WorkflowInstance.Status.SUBMITTED,
            'validate': WorkflowInstance.Status.VALIDATED,
            'reject': WorkflowInstance.Status.REJECTED,
            'publish': WorkflowInstance.Status.PUBLISHED
        }
        
        new_status = status_mapping.get(action_name)
        if not new_status:
            return Response(
                {'error': 'Action non valide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour le statut
        old_status = instance.current_status
        instance.current_status = new_status
        
        # Marquer l'étape actuelle comme complétée
        current_step = instance.steps.filter(
            order=instance.current_step,
            status=WorkflowStep.Status.PENDING
        ).first()
        
        if current_step:
            current_step.status = WorkflowStep.Status.COMPLETED
            current_step.completed_by = request.user
            current_step.completed_at = timezone.now()
            current_step.comments = comments
            current_step.save()
            
            # Passer à l'étape suivante si validation
            if action_name == 'validate':
                instance.current_step += 1
        
        # Si rejeté ou publié, marquer comme terminé
        if action_name in ['reject', 'publish']:
            instance.completed_at = timezone.now()
        
        instance.save()
        
        return Response({
            'message': f'Transition effectuée: {old_status} -> {new_status}',
            'instance': WorkflowInstanceSerializer(instance).data
        })
    
    @action(detail=True, methods=['get'])
    def steps(self, request, pk=None):
        """Récupérer les étapes d'un workflow"""
        instance = self.get_object()
        steps = instance.steps.all()
        serializer = WorkflowStepSerializer(steps, many=True)
        return Response(serializer.data)


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet pour les alertes"""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type', 'severity', 'sector', 'is_read', 'region']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les alertes pour l'utilisateur connecté"""
        user = self.request.user
        
        # Superusers voient tout
        if user.is_superuser:
            return Alert.objects.all()
        
        # Filtrer par région assignée ou destinataire
        return Alert.objects.filter(
            models.Q(recipients=user) |
            models.Q(region=user.assigned_region)
        ).distinct()
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Récupérer les alertes non lues"""
        alerts = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(alerts, many=True)
        return Response({
            'count': alerts.count(),
            'alerts': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_severity(self, request):
        """Récupérer les alertes groupées par sévérité"""
        queryset = self.get_queryset()
        result = {}
        for severity in Alert.Severity.values:
            count = queryset.filter(severity=severity).count()
            result[severity] = count
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marquer une alerte comme lue"""
        alert = self.get_object()
        alert.mark_as_read(request.user)
        return Response({'message': 'Alerte marquée comme lue'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marquer toutes les alertes comme lues"""
        alerts = self.get_queryset().filter(is_read=False)
        for alert in alerts:
            alert.mark_as_read(request.user)
        return Response({
            'message': f'{alerts.count()} alertes marquées comme lues'
        })


# Import manquant
from django.db import models
