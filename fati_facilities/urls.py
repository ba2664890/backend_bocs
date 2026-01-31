"""
FATI Facilities - URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthFacilityViewSet, EducationFacilityViewSet, EquipmentViewSet, StaffViewSet

router = DefaultRouter()
router.register(r'health', HealthFacilityViewSet, basename='healthfacility')
router.register(r'education', EducationFacilityViewSet, basename='educationfacility')
router.register(r'equipment', EquipmentViewSet, basename='equipment')
router.register(r'staff', StaffViewSet, basename='staff')

urlpatterns = [
    path('', include(router.urls)),
]
