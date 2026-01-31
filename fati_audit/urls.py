"""
FATI Audit - URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, DataQualityCheckViewSet, SystemMetricViewSet, StatsViewSet

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='auditlog')
router.register(r'quality', DataQualityCheckViewSet, basename='dataqualitycheck')
router.register(r'metrics', SystemMetricViewSet, basename='systemmetric')
router.register(r'stats', StatsViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]
