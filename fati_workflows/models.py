"""
FATI Workflows - Modèles de workflows et validation
"""
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class WorkflowDefinition(models.Model):
    """Définition d'un workflow de validation"""
    
    class EntityType(models.TextChoices):
        INDICATOR_VALUE = 'indicator_value', _('Valeur d\'indicateur')
        FACILITY = 'facility', _('Structure')
        REPORT = 'report', _('Rapport')
        DATA_SUBMISSION = 'data_submission', _('Soumission de données')
    
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    entity_type = models.CharField(
        _('type d\'entité'),
        max_length=30,
        choices=EntityType.choices
    )
    
    # Configuration du workflow
    steps_config = models.JSONField(
        _('configuration des étapes'),
        default=list,
        help_text=_('Liste ordonnée des étapes avec rôle assigné')
    )
    
    is_active = models.BooleanField(_('actif'), default=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('définition de workflow')
        verbose_name_plural = _('définitions de workflows')
    
    def __str__(self):
        return self.name


class WorkflowInstance(models.Model):
    """Instance d'un workflow en cours"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Brouillon')
        SUBMITTED = 'submitted', _('Soumis')
        UNDER_REVIEW = 'under_review', _('En révision')
        VALIDATED = 'validated', _('Validé')
        REJECTED = 'rejected', _('Rejeté')
        PUBLISHED = 'published', _('Publié')
    
    workflow_definition = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name=_('définition de workflow')
    )
    
    # Entité concernée
    entity_type = models.CharField(_('type d\'entité'), max_length=50)
    entity_id = models.CharField(_('ID de l\'entité'), max_length=100)
    
    # Statut actuel
    current_status = models.CharField(
        _('statut actuel'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Étape actuelle
    current_step = models.PositiveIntegerField(_('étape actuelle'), default=0)
    
    # Initiateur
    initiated_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.CASCADE,
        related_name='initiated_workflows',
        verbose_name=_('initié par')
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    completed_at = models.DateTimeField(_('terminé le'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('instance de workflow')
        verbose_name_plural = _('instances de workflows')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.workflow_definition.name} - {self.entity_type}:{self.entity_id}"


class WorkflowStep(models.Model):
    """Étape d'un workflow"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('En attente')
        IN_PROGRESS = 'in_progress', _('En cours')
        COMPLETED = 'completed', _('Terminée')
        SKIPPED = 'skipped', _('Ignorée')
    
    workflow = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name=_('workflow')
    )
    
    # Configuration de l'étape
    name = models.CharField(_('nom'), max_length=255)
    order = models.PositiveIntegerField(_('ordre'))
    assigned_role = models.CharField(_('rôle assigné'), max_length=50)
    
    # Statut
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Exécution
    completed_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_workflow_steps',
        verbose_name=_('terminé par')
    )
    completed_at = models.DateTimeField(_('terminé le'), null=True, blank=True)
    
    # Commentaires
    comments = models.TextField(_('commentaires'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('étape de workflow')
        verbose_name_plural = _('étapes de workflows')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.workflow} - Étape {self.order}: {self.name}"


class Alert(models.Model):
    """Alerte et notification"""
    
    class Severity(models.TextChoices):
        CRITICAL = 'critical', _('Critique')
        HIGH = 'high', _('Élevée')
        MEDIUM = 'medium', _('Moyenne')
        LOW = 'low', _('Faible')
        INFO = 'info', _('Info')
    
    class AlertType(models.TextChoices):
        THRESHOLD = 'threshold', _('Seuil dépassé')
        TREND = 'trend', _('Tendance')
        ANOMALY = 'anomaly', _('Anomalie')
        DELAY = 'delay', _('Retard')
        VALIDATION = 'validation', _('Validation')
    
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=AlertType.choices
    )
    severity = models.CharField(
        _('gravité'),
        max_length=20,
        choices=Severity.choices
    )
    
    title = models.CharField(_('titre'), max_length=255)
    message = models.TextField(_('message'))
    
    # Secteur concerné
    sector = models.CharField(
        _('secteur'),
        max_length=20,
        choices=[
            ('health', _('Santé')),
            ('education', _('Éducation')),
        ],
        blank=True
    )
    
    # Indicateur concerné
    indicator = models.ForeignKey(
        'fati_indicators.Indicator',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name=_('indicateur')
    )
    
    # Territoire concerné
    region = models.ForeignKey(
        'fati_geography.Region',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name=_('région')
    )
    
    # Valeurs
    value = models.FloatField(_('valeur'), null=True, blank=True)
    threshold = models.FloatField(_('seuil'), null=True, blank=True)
    
    # Statut de lecture
    is_read = models.BooleanField(_('lu'), default=False)
    read_at = models.DateTimeField(_('lu le'), null=True, blank=True)
    read_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_alerts',
        verbose_name=_('lu par')
    )
    
    # Destinataires
    recipients = models.ManyToManyField(
        'fati_accounts.User',
        related_name='alerts',
        verbose_name=_('destinataires')
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('alerte')
        verbose_name_plural = _('alertes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.severity})"
    
    def mark_as_read(self, user):
        """Marquer l'alerte comme lue"""
        self.is_read = True
        self.read_at = timezone.now()
        self.read_by = user
        self.save(update_fields=['is_read', 'read_at', 'read_by'])


from django.utils import timezone
