"""
FATI Indicators - URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndicatorViewSet, IndicatorValueViewSet, IndicatorHistoryViewSet

router = DefaultRouter()
router.register(r'indicators', IndicatorViewSet, basename='indicator')
router.register(r'values', IndicatorValueViewSet, basename='indicatorvalue')
router.register(r'history', IndicatorHistoryViewSet, basename='indicatorhistory')

urlpatterns = [
    path('', include(router.urls)),
]
