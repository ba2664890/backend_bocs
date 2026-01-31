"""
FATI Data Collection - Modèles de collecte de données
"""
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class DataCollection(models.Model):
    """Campagne de collecte de données"""
    
    class Status(models.TextChoices):
        PLANNED = 'planned', _('Planifiée')
        ONGOING = 'ongoing', _('En cours')
        COMPLETED = 'completed', _('Terminée')
        CLOSED = 'closed', _('Clôturée')
    
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    # Secteur ciblé
    sector = models.CharField(
        _('secteur'),
        max_length=20,
        choices=[
            ('health', _('Santé')),
            ('education', _('Éducation')),
            ('both', _('Les deux')),
        ]
    )
    
    # Période
    year = models.PositiveIntegerField(_('année'))
    period = models.CharField(_('période'), max_length=50, blank=True)
    start_date = models.DateField(_('date de début'))
    end_date = models.DateField(_('date de fin'))
    
    # Portée géographique
    geographic_scope = models.CharField(
        _('portée géographique'),
        max_length=20,
        choices=[
            ('national', _('National')),
            ('regional', _('Régional')),
            ('department', _('Départemental')),
            ('commune', _('Communal')),
        ]
    )
    regions = models.ManyToManyField(
        'fati_geography.Region',
        blank=True,
        related_name='data_collections',
        verbose_name=_('régions')
    )
    
    # Indicateurs à collecter
    indicators = models.ManyToManyField(
        'fati_indicators.Indicator',
        related_name='data_collections',
        verbose_name=_('indicateurs')
    )
    
    # Statut
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )
    
    # Taux de réponse
    response_rate = models.FloatField(
        _('taux de réponse (%)'),
        default=0,
        help_text=_('Pourcentage de territoires ayant soumis des données')
    )
    
    # Créateur
    created_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.CASCADE,
        related_name='created_collections',
        verbose_name=_('créé par')
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('collecte de données')
        verbose_name_plural = _('collectes de données')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.year})"
    
    def calculate_response_rate(self):
        """Calculer le taux de réponse"""
        total = self.submissions.count()
        submitted = self.submissions.filter(status='submitted').count()
        if total > 0:
            self.response_rate = (submitted / total) * 100
            self.save(update_fields=['response_rate'])


class DataSubmission(models.Model):
    """Soumission de données pour une collecte"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Brouillon')
        SUBMITTED = 'submitted', _('Soumis')
        UNDER_REVIEW = 'under_review', _('En révision')
        VALIDATED = 'validated', _('Validé')
        REJECTED = 'rejected', _('Rejeté')
    
    collection = models.ForeignKey(
        DataCollection,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('collecte')
    )
    
    # Territoire
    region = models.ForeignKey(
        'fati_geography.Region',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='data_submissions',
        verbose_name=_('région')
    )
    department = models.ForeignKey(
        'fati_geography.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='data_submissions',
        verbose_name=_('département')
    )
    commune = models.ForeignKey(
        'fati_geography.Commune',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='data_submissions',
        verbose_name=_('commune')
    )
    
    # Contributeur
    submitted_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.CASCADE,
        related_name='data_submissions',
        verbose_name=_('soumis par')
    )
    
    # Statut
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Dates
    submitted_at = models.DateTimeField(_('soumis le'), null=True, blank=True)
    reviewed_at = models.DateTimeField(_('révisé le'), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions',
        verbose_name=_('révisé par')
    )
    
    # Commentaires
    reviewer_notes = models.TextField(_('notes du réviseur'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('soumission de données')
        verbose_name_plural = _('soumissions de données')
        unique_together = ['collection', 'region', 'department', 'commune']
    
    def __str__(self):
        territory = self.commune or self.department or self.region
        return f"{self.collection.name} - {territory}"


class DataEntry(models.Model):
    """Entrée de données individuelle"""
    
    submission = models.ForeignKey(
        DataSubmission,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name=_('soumission')
    )
    
    indicator = models.ForeignKey(
        'fati_indicators.Indicator',
        on_delete=models.CASCADE,
        related_name='data_entries',
        verbose_name=_('indicateur')
    )
    
    # Valeur
    value = models.FloatField(_('valeur'))
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    # Fichiers joints
    attachments = models.JSONField(_('pièces jointes'), default=list, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('entrée de données')
        verbose_name_plural = _('entrées de données')
        unique_together = ['submission', 'indicator']
    
    def __str__(self):
        return f"{self.indicator.name}: {self.value}"


class FormTemplate(models.Model):
    """Modèle de formulaire de collecte"""
    
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    # Secteur
    sector = models.CharField(
        _('secteur'),
        max_length=20,
        choices=[
            ('health', _('Santé')),
            ('education', _('Éducation')),
        ]
    )
    
    # Structure du formulaire (JSON Schema)
    schema = models.JSONField(_('schéma'), default=dict)
    
    # UI Schema pour la présentation
    ui_schema = models.JSONField(_('schéma UI'), default=dict, blank=True)
    
    # Actif
    is_active = models.BooleanField(_('actif'), default=True)
    
    created_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.CASCADE,
        related_name='created_forms',
        verbose_name=_('créé par')
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('modèle de formulaire')
        verbose_name_plural = _('modèles de formulaires')
    
    def __str__(self):
        return self.name
