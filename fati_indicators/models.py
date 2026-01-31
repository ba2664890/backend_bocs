"""
FATI Indicators - Modèles d'indicateurs
"""
from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Indicator(models.Model):
    """Définition d'un indicateur"""
    
    class Sector(models.TextChoices):
        HEALTH = 'health', _('Santé')
        EDUCATION = 'education', _('Éducation')
    
    class Category(models.TextChoices):
        ACCESS = 'access', _('Accès')
        QUALITY = 'quality', _('Qualité')
        RESOURCES = 'resources', _('Ressources')
        OUTCOMES = 'outcomes', _('Résultats')
        INFRASTRUCTURE = 'infrastructure', _('Infrastructure')
        PERSONNEL = 'personnel', _('Personnel')
        FINANCE = 'finance', _('Finance')
    
    class Type(models.TextChoices):
        NUMBER = 'number', _('Nombre')
        PERCENTAGE = 'percentage', _('Pourcentage')
        RATIO = 'ratio', _('Ratio')
        CURRENCY = 'currency', _('Monnaie')
        COUNT = 'count', _('Comptage')
    
    code = models.CharField(_('code'), max_length=50, unique=True)
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    sector = models.CharField(
        _('secteur'),
        max_length=20,
        choices=Sector.choices
    )
    category = models.CharField(
        _('catégorie'),
        max_length=20,
        choices=Category.choices
    )
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=Type.choices,
        default=Type.NUMBER
    )
    
    unit = models.CharField(_('unité'), max_length=50, blank=True)
    formula = models.TextField(_('formule'), blank=True)
    denominator = models.CharField(_('dénominateur'), max_length=255, blank=True)
    
    # Objectifs
    target_value = models.FloatField(_('valeur cible'), null=True, blank=True)
    alert_threshold = models.FloatField(_('seuil d\'alerte'), null=True, blank=True)
    
    # Configuration
    is_active = models.BooleanField(_('actif'), default=True)
    order = models.PositiveIntegerField(_('ordre'), default=0)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('indicateur')
        verbose_name_plural = _('indicateurs')
        ordering = ['sector', 'category', 'order', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class IndicatorValue(models.Model):
    """Valeur d'un indicateur pour un territoire et une période"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Brouillon')
        PENDING = 'pending', _('En attente')
        VALIDATED = 'validated', _('Validé')
        REJECTED = 'rejected', _('Rejeté')
    
    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_('indicateur')
    )
    
    # Territoire
    region = models.ForeignKey(
        'fati_geography.Region',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='indicator_values',
        verbose_name=_('région')
    )
    department = models.ForeignKey(
        'fati_geography.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='indicator_values',
        verbose_name=_('département')
    )
    commune = models.ForeignKey(
        'fati_geography.Commune',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='indicator_values',
        verbose_name=_('commune')
    )
    
    # Période
    year = models.PositiveIntegerField(_('année'))
    period = models.CharField(_('période'), max_length=20, blank=True)
    
    # Valeur
    value = models.FloatField(_('valeur'))
    previous_value = models.FloatField(_('valeur précédente'), null=True, blank=True)
    target_value = models.FloatField(_('valeur cible'), null=True, blank=True)
    
    # Calcul automatique
    variation = models.FloatField(_('variation (%)'), null=True, blank=True)
    achievement_rate = models.FloatField(
        _('taux de réalisation (%)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1000)]
    )
    
    # Statut et validation
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    validated_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_indicators',
        verbose_name=_('validé par')
    )
    validated_at = models.DateTimeField(_('validé le'), null=True, blank=True)
    
    # Source et notes
    source = models.CharField(_('source'), max_length=255, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # Métadonnées
    created_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_indicator_values',
        verbose_name=_('créé par')
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('valeur d\'indicateur')
        verbose_name_plural = _('valeurs d\'indicateurs')
        ordering = ['-year', 'indicator__sector', 'indicator__name']
        unique_together = [
            ['indicator', 'region', 'department', 'commune', 'year', 'period']
        ]
    
    def __str__(self):
        territory = self.commune or self.department or self.region
        return f"{self.indicator.name} - {territory} ({self.year})"
    
    def save(self, *args, **kwargs):
        # Calculer la variation
        if self.previous_value and self.previous_value != 0:
            self.variation = ((self.value - self.previous_value) / self.previous_value) * 100
        
        # Calculer le taux de réalisation
        target = self.target_value or self.indicator.target_value
        if target and target != 0:
            self.achievement_rate = (self.value / target) * 100
        
        super().save(*args, **kwargs)
    
    @property
    def value_formatted(self):
        """Formater la valeur selon le type d'indicateur"""
        indicator_type = self.indicator.type
        unit = self.indicator.unit or ''
        
        if indicator_type == Indicator.Type.PERCENTAGE:
            return f"{self.value:.1f}%"
        elif indicator_type == Indicator.Type.RATIO:
            return f"{self.value:.1f}{unit}"
        elif indicator_type == Indicator.Type.CURRENCY:
            return f"{self.value:,.0f} {unit}"
        elif indicator_type == Indicator.Type.COUNT:
            return f"{self.value:,.0f}"
        else:
            return f"{self.value:.2f} {unit}"
    
    @property
    def geographic_level(self):
        if self.commune:
            return 'commune'
        elif self.department:
            return 'department'
        elif self.region:
            return 'region'
        return 'national'
    
    @property
    def geographic_entity(self):
        return self.commune or self.department or self.region


class IndicatorHistory(models.Model):
    """Historique des modifications d'une valeur d'indicateur"""
    
    indicator_value = models.ForeignKey(
        IndicatorValue,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('valeur d\'indicateur')
    )
    
    old_value = models.FloatField(_('ancienne valeur'), null=True, blank=True)
    new_value = models.FloatField(_('nouvelle valeur'))
    
    changed_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('modifié par')
    )
    change_reason = models.TextField(_('raison de la modification'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('historique d\'indicateur')
        verbose_name_plural = _('historiques d\'indicateurs')
        ordering = ['-created_at']
