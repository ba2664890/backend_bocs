"""
FATI Geography - Modèles géographiques
"""
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class Region(models.Model):
    """Région administrative"""
    
    code = models.CharField(_('code'), max_length=50, unique=True)
    name = models.CharField(_('nom'), max_length=100)
    
    # Géométrie
    geometry = models.MultiPolygonField(_('géométrie'), srid=4326, null=True, blank=True)
    centroid = models.PointField(_('centroïde'), srid=4326, null=True, blank=True)
    
    # Données démographiques
    population = models.PositiveIntegerField(_('population'), null=True, blank=True)
    area_km2 = models.FloatField(_('superficie (km²)'), null=True, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(_('métadonnées'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('région')
        verbose_name_plural = _('régions')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Calculer le centroïde si la géométrie existe
        if self.geometry and not self.centroid:
            self.centroid = self.geometry.centroid
        super().save(*args, **kwargs)
    
    @property
    def departments_count(self):
        return self.departments.count()
    
    @property
    def communes_count(self):
        return Commune.objects.filter(department__region=self).count()


class Department(models.Model):
    """Département administratif"""
    
    code = models.CharField(_('code'), max_length=50, unique=True)
    name = models.CharField(_('nom'), max_length=100)
    
    # Relations
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_('région')
    )
    
    # Géométrie
    geometry = models.MultiPolygonField(_('géométrie'), srid=4326, null=True, blank=True)
    centroid = models.PointField(_('centroïde'), srid=4326, null=True, blank=True)
    
    # Données démographiques
    population = models.PositiveIntegerField(_('population'), null=True, blank=True)
    area_km2 = models.FloatField(_('superficie (km²)'), null=True, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(_('métadonnées'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('département')
        verbose_name_plural = _('départements')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"
    
    def save(self, *args, **kwargs):
        if self.geometry and not self.centroid:
            self.centroid = self.geometry.centroid
        super().save(*args, **kwargs)
    
    @property
    def communes_count(self):
        return self.communes.count()


class Commune(models.Model):
    """Commune administrative"""
    
    code = models.CharField(_('code'), max_length=50, unique=True)
    name = models.CharField(_('nom'), max_length=100)
    
    # Relations
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='communes',
        verbose_name=_('département')
    )
    
    # Géométrie
    geometry = models.MultiPolygonField(_('géométrie'), srid=4326, null=True, blank=True)
    centroid = models.PointField(_('centroïde'), srid=4326, null=True, blank=True)
    
    # Données démographiques
    population = models.PositiveIntegerField(_('population'), null=True, blank=True)
    area_km2 = models.FloatField(_('superficie (km²)'), null=True, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(_('métadonnées'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('commune')
        verbose_name_plural = _('communes')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.department.name})"
    
    def save(self, *args, **kwargs):
        if self.geometry and not self.centroid:
            self.centroid = self.geometry.centroid
        super().save(*args, **kwargs)
    
    @property
    def region(self):
        return self.department.region
