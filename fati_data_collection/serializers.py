"""
FATI Data Collection - Serializers
"""
from rest_framework import serializers
from .models import DataCollection, DataSubmission, DataEntry, FormTemplate


class DataCollectionSerializer(serializers.ModelSerializer):
    """Serializer pour les campagnes de collecte"""
    
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    geographic_scope_display = serializers.CharField(
        source='get_geographic_scope_display',
        read_only=True
    )
    
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    
    indicators_count = serializers.IntegerField(
        source='indicators.count',
        read_only=True
    )
    submissions_count = serializers.IntegerField(
        source='submissions.count',
        read_only=True
    )
    
    class Meta:
        model = DataCollection
        fields = [
            'id', 'name', 'description',
            'sector', 'sector_display',
            'year', 'period',
            'start_date', 'end_date',
            'geographic_scope', 'geographic_scope_display',
            'status', 'status_display',
            'response_rate',
            'indicators_count', 'submissions_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]


class DataCollectionDetailSerializer(DataCollectionSerializer):
    """Serializer détaillé pour les campagnes de collecte"""
    
    indicators = serializers.SerializerMethodField()
    regions = serializers.SerializerMethodField()
    
    class Meta(DataCollectionSerializer.Meta):
        fields = DataCollectionSerializer.Meta.fields + ['indicators', 'regions']
    
    def get_indicators(self, obj):
        from fati_indicators.serializers import IndicatorSerializer
        return IndicatorSerializer(obj.indicators.all(), many=True).data
    
    def get_regions(self, obj):
        from fati_geography.serializers import RegionListSerializer
        return RegionListSerializer(obj.regions.all(), many=True).data


class DataEntrySerializer(serializers.ModelSerializer):
    """Serializer pour les entrées de données"""
    
    indicator_name = serializers.CharField(
        source='indicator.name',
        read_only=True
    )
    indicator_code = serializers.CharField(
        source='indicator.code',
        read_only=True
    )
    
    class Meta:
        model = DataEntry
        fields = [
            'id', 'indicator', 'indicator_name', 'indicator_code',
            'value', 'notes', 'attachments',
            'created_at', 'updated_at'
        ]


class DataSubmissionSerializer(serializers.ModelSerializer):
    """Serializer pour les soumissions de données"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    collection_name = serializers.CharField(
        source='collection.name',
        read_only=True
    )
    submitted_by_name = serializers.CharField(
        source='submitted_by.get_full_name',
        read_only=True
    )
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.get_full_name',
        read_only=True
    )
    
    territory_name = serializers.SerializerMethodField()
    entries_count = serializers.IntegerField(
        source='entries.count',
        read_only=True
    )
    
    class Meta:
        model = DataSubmission
        fields = [
            'id', 'collection', 'collection_name',
            'region', 'department', 'commune',
            'territory_name',
            'submitted_by', 'submitted_by_name',
            'status', 'status_display',
            'submitted_at', 'reviewed_at',
            'reviewed_by', 'reviewed_by_name',
            'reviewer_notes',
            'entries_count',
            'created_at', 'updated_at'
        ]
    
    def get_territory_name(self, obj):
        territory = obj.commune or obj.department or obj.region
        return territory.name if territory else None


class DataSubmissionDetailSerializer(DataSubmissionSerializer):
    """Serializer détaillé pour les soumissions"""
    
    entries = DataEntrySerializer(many=True, read_only=True)
    
    class Meta(DataSubmissionSerializer.Meta):
        fields = DataSubmissionSerializer.Meta.fields + ['entries']


class FormTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les modèles de formulaires"""
    
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = FormTemplate
        fields = [
            'id', 'name', 'description',
            'sector', 'sector_display',
            'schema', 'ui_schema',
            'is_active',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
