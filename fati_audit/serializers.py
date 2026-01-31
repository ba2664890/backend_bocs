"""
FATI Audit - Serializers
"""
from rest_framework import serializers
from .models import AuditLog, DataQualityCheck, SystemMetric


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer pour les journaux d'audit"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'user_name', 'user_role',
            'action', 'entity_type', 'entity_id', 'entity_name',
            'old_values', 'new_values', 'ip_address', 'created_at'
        ]
        read_only_fields = ['created_at']


class AuditLogCreateSerializer(serializers.Serializer):
    """Serializer pour créer une entrée d'audit"""
    action = serializers.ChoiceField(choices=AuditLog.Action.choices)
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    entity_name = serializers.CharField(required=False, allow_blank=True)
    old_values = serializers.JSONField(required=False, default=dict)
    new_values = serializers.JSONField(required=False, default=dict)


class DataQualityCheckSerializer(serializers.ModelSerializer):
    """Serializer pour les vérifications de qualité"""
    indicator_value_details = serializers.SerializerMethodField()
    
    class Meta:
        model = DataQualityCheck
        fields = [
            'id', 'indicator_value', 'indicator_value_details',
            'check_type', 'status', 'message', 'details', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_indicator_value_details(self, obj):
        return {
            'indicator_name': obj.indicator_value.indicator.name,
            'region': obj.indicator_value.region.name,
            'value': obj.indicator_value.value,
            'period': obj.indicator_value.period
        }


class SystemMetricSerializer(serializers.ModelSerializer):
    """Serializer pour les métriques système"""
    
    class Meta:
        model = SystemMetric
        fields = [
            'id', 'metric_name', 'metric_value',
            'dimension_1', 'dimension_2', 'timestamp'
        ]


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du tableau de bord"""
    total_users = serializers.IntegerField()
    total_indicators = serializers.IntegerField()
    total_facilities = serializers.IntegerField()
    total_data_points = serializers.IntegerField()
    recent_activities = AuditLogSerializer(many=True)
    quality_score = serializers.FloatField()
