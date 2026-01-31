"""
FATI Indicators - Serializers
"""
from rest_framework import serializers
from .models import Indicator, IndicatorValue, IndicatorHistory


class IndicatorSerializer(serializers.ModelSerializer):
    """Serializer pour les indicateurs"""
    
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Indicator
        fields = [
            'id', 'code', 'name', 'description',
            'sector', 'sector_display',
            'category', 'category_display',
            'type', 'type_display',
            'unit', 'formula', 'denominator',
            'target_value', 'alert_threshold',
            'is_active', 'order',
            'created_at', 'updated_at'
        ]


class IndicatorValueSerializer(serializers.ModelSerializer):
    """Serializer pour les valeurs d'indicateurs"""
    
    indicator_name = serializers.CharField(source='indicator.name', read_only=True)
    indicator_code = serializers.CharField(source='indicator.code', read_only=True)
    indicator_type = serializers.CharField(source='indicator.type', read_only=True)
    indicator_unit = serializers.CharField(source='indicator.unit', read_only=True)
    
    geographic_name = serializers.SerializerMethodField()
    geographic_level = serializers.CharField(read_only=True)
    value_formatted = serializers.CharField(read_only=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    validated_by_name = serializers.CharField(
        source='validated_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = IndicatorValue
        fields = [
            'id', 'indicator', 'indicator_name', 'indicator_code',
            'indicator_type', 'indicator_unit',
            'region', 'department', 'commune',
            'geographic_name', 'geographic_level',
            'year', 'period',
            'value', 'value_formatted',
            'previous_value', 'variation',
            'target_value', 'achievement_rate',
            'status', 'status_display',
            'validated_by', 'validated_by_name', 'validated_at',
            'source', 'notes',
            'created_at', 'updated_at'
        ]
    
    def get_geographic_name(self, obj):
        entity = obj.geographic_entity
        return entity.name if entity else None


class IndicatorValueCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de valeurs d'indicateurs"""
    
    class Meta:
        model = IndicatorValue
        fields = [
            'indicator', 'region', 'department', 'commune',
            'year', 'period', 'value', 'previous_value',
            'target_value', 'source', 'notes'
        ]


class IndicatorValueUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour de valeurs d'indicateurs"""
    
    class Meta:
        model = IndicatorValue
        fields = ['value', 'source', 'notes']


class IndicatorHistorySerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des indicateurs"""
    
    changed_by_name = serializers.CharField(
        source='changed_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = IndicatorHistory
        fields = [
            'id', 'old_value', 'new_value',
            'changed_by', 'changed_by_name',
            'change_reason', 'created_at'
        ]


class IndicatorSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des indicateurs"""
    
    indicator_id = serializers.IntegerField()
    indicator_name = serializers.CharField()
    indicator_code = serializers.CharField()
    sector = serializers.CharField()
    latest_value = serializers.FloatField()
    latest_year = serializers.IntegerField()
    target_value = serializers.FloatField()
    achievement_rate = serializers.FloatField()
    trend = serializers.CharField()
