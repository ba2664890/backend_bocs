"""
FATI Dashboards - Serializers
"""
from rest_framework import serializers
from .models import Dashboard, Widget, ReportTemplate, GeneratedReport


class WidgetSerializer(serializers.ModelSerializer):
    """Serializer pour les widgets"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Widget
        fields = [
            'id', 'name', 'type', 'type_display',
            'position_x', 'position_y', 'width', 'height',
            'config', 'data_source', 'filters',
            'refresh_interval', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WidgetCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un widget"""
    
    class Meta:
        model = Widget
        fields = [
            'name', 'type', 'position_x', 'position_y',
            'width', 'height', 'config', 'data_source',
            'filters', 'refresh_interval'
        ]


class DashboardSerializer(serializers.ModelSerializer):
    """Serializer pour les tableaux de bord"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    widgets = WidgetSerializer(many=True, read_only=True)
    widget_count = serializers.IntegerField(source='widgets.count', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'type', 'type_display',
            'layout_config', 'default_filters',
            'owner', 'owner_name', 'is_shared', 'is_default',
            'is_active', 'widgets', 'widget_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DashboardCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un tableau de bord"""
    
    class Meta:
        model = Dashboard
        fields = [
            'name', 'description', 'type',
            'layout_config', 'default_filters'
        ]


class DashboardShareSerializer(serializers.Serializer):
    """Serializer pour partager un tableau de bord"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text='Liste des IDs utilisateurs'
    )


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les modèles de rapport"""
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'sector', 'sector_display',
            'template_config', 'available_formats', 'parameters',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class GeneratedReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports générés"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    generated_by_name = serializers.CharField(
        source='generated_by.get_full_name',
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GeneratedReport
        fields = [
            'id', 'template', 'template_name', 'name',
            'parameters', 'file', 'file_url', 'format',
            'generated_by', 'generated_by_name',
            'generated_at', 'status', 'status_display',
            'error_message'
        ]
        read_only_fields = ['generated_at']
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class ReportGenerateSerializer(serializers.Serializer):
    """Serializer pour générer un rapport"""
    template_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    parameters = serializers.JSONField(default=dict)
    format = serializers.ChoiceField(
        choices=ReportTemplate.ReportFormat.choices,
        default='pdf'
    )


class DashboardDataSerializer(serializers.Serializer):
    """Serializer pour les données de tableau de bord"""
    kpis = serializers.ListField(child=serializers.DictField())
    charts = serializers.ListField(child=serializers.DictField())
    alerts = serializers.ListField(child=serializers.DictField())
    map_data = serializers.DictField()
    recent_activity = serializers.ListField(child=serializers.DictField())
