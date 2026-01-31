"""
FATI Data Collection - URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataCollectionViewSet, DataSubmissionViewSet, FormTemplateViewSet

router = DefaultRouter()
router.register(r'collections', DataCollectionViewSet, basename='datacollection')
router.register(r'submissions', DataSubmissionViewSet, basename='datasubmission')
router.register(r'forms', FormTemplateViewSet, basename='formtemplate')

urlpatterns = [
    path('', include(router.urls)),
]
