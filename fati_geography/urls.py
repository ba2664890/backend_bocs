"""
FATI Geography - URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegionViewSet, DepartmentViewSet, CommuneViewSet

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'communes', CommuneViewSet, basename='commune')

urlpatterns = [
    path('', include(router.urls)),
]
