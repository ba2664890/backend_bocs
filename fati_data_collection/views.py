"""
FATI Data Collection - Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import DataCollection, DataSubmission, DataEntry, FormTemplate
from .serializers import (
    DataCollectionSerializer,
    DataCollectionDetailSerializer,
    DataSubmissionSerializer,
    DataEntrySerializer,
    FormTemplateSerializer
)


class DataCollectionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les campagnes de collecte"""
    
    queryset = DataCollection.objects.prefetch_related(
        'indicators', 'regions'
    ).all()
    serializer_class = DataCollectionSerializer
    filterset_fields = ['sector', 'year', 'status']
    filter_backends = [DjangoFilterBackend]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DataCollectionDetailSerializer
        return DataCollectionSerializer
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Récupérer les soumissions d'une collecte"""
        collection = self.get_object()
        submissions = collection.submissions.all()
        serializer = DataSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Démarrer une collecte"""
        collection = self.get_object()
        collection.status = 'ongoing'
        collection.save()
        serializer = DataCollectionSerializer(collection)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Terminer une collecte"""
        collection = self.get_object()
        collection.status = 'completed'
        collection.save()
        serializer = DataCollectionSerializer(collection)
        return Response(serializer.data)


class DataSubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les soumissions de données"""
    
    queryset = DataSubmission.objects.select_related(
        'collection', 'submitted_by'
    ).prefetch_related('entries').all()
    serializer_class = DataSubmissionSerializer
    filterset_fields = ['collection', 'status', 'region', 'department', 'commune']
    filter_backends = [DjangoFilterBackend]
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        user = self.request.user
        queryset = self.queryset
        
        if user.is_contributor or user.is_local_manager:
            if user.assigned_commune:
                queryset = queryset.filter(commune=user.assigned_commune)
            elif user.assigned_department:
                queryset = queryset.filter(department=user.assigned_department)
            elif user.assigned_region:
                queryset = queryset.filter(region=user.assigned_region)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Soumettre une soumission"""
        submission = self.get_object()
        submission.status = 'submitted'
        from django.utils import timezone
        submission.submitted_at = timezone.now()
        submission.save()
        serializer = DataSubmissionSerializer(submission)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Valider une soumission"""
        submission = self.get_object()
        submission.status = 'validated'
        submission.reviewed_by = request.user
        from django.utils import timezone
        submission.reviewed_at = timezone.now()
        submission.save()
        serializer = DataSubmissionSerializer(submission)
        return Response(serializer.data)


class FormTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet pour les modèles de formulaires"""
    
    queryset = FormTemplate.objects.filter(is_active=True)
    serializer_class = FormTemplateSerializer
    filterset_fields = ['sector']
