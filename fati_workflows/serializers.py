"""
FATI Workflows - Serializers
"""
from rest_framework import serializers
from .models import WorkflowDefinition, WorkflowInstance, WorkflowStep, Alert


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    """Serializer pour les définitions de workflow"""
    
    class Meta:
        model = WorkflowDefinition
        fields = [
            'id', 'name', 'description', 'entity_type',
            'steps_config', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WorkflowStepSerializer(serializers.ModelSerializer):
    """Serializer pour les étapes de workflow"""
    completed_by_name = serializers.CharField(
        source='completed_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = WorkflowStep
        fields = [
            'id', 'name', 'order', 'assigned_role', 'status',
            'completed_by', 'completed_by_name', 'completed_at',
            'comments', 'created_at'
        ]
        read_only_fields = ['created_at']


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    """Serializer pour les instances de workflow"""
    workflow_definition_name = serializers.CharField(
        source='workflow_definition.name',
        read_only=True
    )
    initiated_by_name = serializers.CharField(
        source='initiated_by.get_full_name',
        read_only=True
    )
    steps = WorkflowStepSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkflowInstance
        fields = [
            'id', 'workflow_definition', 'workflow_definition_name',
            'entity_type', 'entity_id', 'current_status', 'current_step',
            'initiated_by', 'initiated_by_name', 'steps',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'completed_at']


class WorkflowInstanceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'instances de workflow"""
    
    class Meta:
        model = WorkflowInstance
        fields = ['workflow_definition', 'entity_type', 'entity_id']


class WorkflowTransitionSerializer(serializers.Serializer):
    """Serializer pour les transitions de workflow"""
    action = serializers.ChoiceField(
        choices=['submit', 'validate', 'reject', 'publish']
    )
    comments = serializers.CharField(required=False, allow_blank=True)


class AlertSerializer(serializers.ModelSerializer):
    """Serializer pour les alertes"""
    indicator_name = serializers.CharField(
        source='indicator.name',
        read_only=True
    )
    region_name = serializers.CharField(
        source='region.name',
        read_only=True
    )
    
    class Meta:
        model = Alert
        fields = [
            'id', 'type', 'severity', 'title', 'message',
            'sector', 'indicator', 'indicator_name',
            'region', 'region_name', 'value', 'threshold',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['read_at', 'created_at']


class AlertMarkReadSerializer(serializers.Serializer):
    """Serializer pour marquer une alerte comme lue"""
    pass
