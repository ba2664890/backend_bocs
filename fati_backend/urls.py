"""
FATI Backend - URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration de la documentation API
schema_view = get_schema_view(
    openapi.Info(
        title="FATI API",
        default_version='v1',
        description="API pour le Fond d'Analyse Territoriale Intégrée (FATI)",
        terms_of_service="https://fati.gov.sn/terms/",
        contact=openapi.Contact(email="support@fati.gov.sn"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Customisation de l'interface d'administration
admin.site.site_header = "FATI - Administration"
admin.site.site_title = "Portail FATI"
admin.site.index_title = "Gestion de la plateforme territoriale"

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/auth/', include('fati_accounts.urls')),
    path('api/geography/', include('fati_geography.urls')),
    path('api/indicators/', include('fati_indicators.urls')),
    path('api/facilities/', include('fati_facilities.urls')),
    path('api/collections/', include('fati_data_collection.urls')),
    path('api/workflows/', include('fati_workflows.urls')),
    path('api/audit/', include('fati_audit.urls')),
    path('api/dashboards/', include('fati_dashboards.urls')),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
