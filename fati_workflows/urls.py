"""
FATI Workflows - URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowDefinitionViewSet, WorkflowInstanceViewSet, AlertViewSet

router = DefaultRouter()
router.register(r'definitions', WorkflowDefinitionViewSet, basename='workflowdefinition')
router.register(r'instances', WorkflowInstanceViewSet, basename='workflowinstance')
router.register(r'alerts', AlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
]
