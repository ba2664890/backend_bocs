"""
FATI Dashboards - URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardViewSet,
    WidgetViewSet,
    ReportTemplateViewSet,
    GeneratedReportViewSet,
    DashboardDataViewSet
)

router = DefaultRouter()
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'widgets', WidgetViewSet, basename='widget')
router.register(r'templates', ReportTemplateViewSet, basename='reporttemplate')
router.register(r'reports', GeneratedReportViewSet, basename='generatedreport')
router.register(r'data', DashboardDataViewSet, basename='dashboarddata')

urlpatterns = [
    path('', include(router.urls)),
]
