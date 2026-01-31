"""
FATI Audit - Modèles d'audit et journalisation
"""
from django.contrib.gis.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """Journal d'audit des actions utilisateurs"""
    
    class Action(models.TextChoices):
        CREATE = 'create', _('Créer')
        UPDATE = 'update', _('Modifier')
        DELETE = 'delete', _('Supprimer')
        VALIDATE = 'validate', _('Valider')
        REJECT = 'reject', _('Rejeter')
        EXPORT = 'export', _('Exporter')
        LOGIN = 'login', _('Connexion')
        LOGOUT = 'logout', _('Déconnexion')
        VIEW = 'view', _('Consultation')
    
    # Utilisateur
    user = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name=_('utilisateur')
    )
    user_name = models.CharField(_('nom utilisateur'), max_length=255)
    user_role = models.CharField(_('rôle utilisateur'), max_length=50)
    
    # Action
    action = models.CharField(
        _('action'),
        max_length=20,
        choices=Action.choices
    )
    
    # Entité concernée
    entity_type = models.CharField(_('type d\'entité'), max_length=100)
    entity_id = models.CharField(_('ID de l\'entité'), max_length=100)
    entity_name = models.CharField(_('nom de l\'entité'), max_length=255, blank=True)
    
    # Modifications
    old_values = models.JSONField(_('anciennes valeurs'), default=dict, blank=True)
    new_values = models.JSONField(_('nouvelles valeurs'), default=dict, blank=True)
    
    # Informations techniques
    ip_address = models.GenericIPAddressField(_('adresse IP'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('journal d\'audit')
        verbose_name_plural = _('journaux d\'audit')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user_name} - {self.action} {self.entity_type}"
    
    @classmethod
    def log(cls, user, action, entity_type, entity_id, entity_name='',
            old_values=None, new_values=None, request=None):
        """Créer une entrée de journal"""
        ip_address = None
        user_agent = ''
        
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            user_name=user.get_full_name() if user else 'Anonymous',
            user_role=user.role if user else '',
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            entity_name=entity_name,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DataQualityCheck(models.Model):
    """Vérification de qualité des données"""
    
    class Status(models.TextChoices):
        PASSED = 'passed', _('Réussi')
        WARNING = 'warning', _('Avertissement')
        FAILED = 'failed', _('Échec')
    
    class CheckType(models.TextChoices):
        COMPLETENESS = 'completeness', _('Complétude')
        CONSISTENCY = 'consistency', _('Cohérence')
        VALIDITY = 'validity', _('Validité')
        TIMELINESS = 'timeliness', _('Ponctualité')
    
    indicator_value = models.ForeignKey(
        'fati_indicators.IndicatorValue',
        on_delete=models.CASCADE,
        related_name='quality_checks',
        verbose_name=_('valeur d\'indicateur')
    )
    
    check_type = models.CharField(
        _('type de vérification'),
        max_length=20,
        choices=CheckType.choices
    )
    
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices
    )
    
    message = models.TextField(_('message'), blank=True)
    details = models.JSONField(_('détails'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('vérification de qualité')
        verbose_name_plural = _('vérifications de qualité')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.indicator_value} - {self.check_type}: {self.status}"


class SystemMetric(models.Model):
    """Métriques système pour le monitoring"""
    
    metric_name = models.CharField(_('nom de la métrique'), max_length=100)
    metric_value = models.FloatField(_('valeur'))
    
    # Dimensions
    dimension_1 = models.CharField(_('dimension 1'), max_length=100, blank=True)
    dimension_2 = models.CharField(_('dimension 2'), max_length=100, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(_('horodatage'), default=timezone.now)
    
    class Meta:
        verbose_name = _('métrique système')
        verbose_name_plural = _('métriques système')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_name', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"
    
    @classmethod
    def record(cls, name, value, dimension_1='', dimension_2=''):
        """Enregistrer une métrique"""
        return cls.objects.create(
            metric_name=name,
            metric_value=value,
            dimension_1=dimension_1,
            dimension_2=dimension_2
        )
