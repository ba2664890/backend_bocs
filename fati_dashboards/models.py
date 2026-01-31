"""
FATI Dashboards - Modèles de tableaux de bord
"""
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class Dashboard(models.Model):
    """Tableau de bord personnalisé"""
    
    class DashboardType(models.TextChoices):
        INSTITUTION = 'institution', _('Institution')
        HEALTH = 'health', _('Santé')
        EDUCATION = 'education', _('Éducation')
        ADMIN = 'admin', _('Administration')
        CONTRIBUTOR = 'contributor', _('Contributeur')
    
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=DashboardType.choices
    )
    
    # Configuration du dashboard
    layout_config = models.JSONField(
        _('configuration de la mise en page'),
        default=dict,
        help_text=_('Configuration des widgets et leur position')
    )
    
    # Filtres par défaut
    default_filters = models.JSONField(
        _('filtres par défaut'),
        default=dict,
        help_text=_('Filtres appliqués par défaut')
    )
    
    # Propriétaire
    owner = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name=_('propriétaire')
    )
    
    # Partage
    is_shared = models.BooleanField(_('partagé'), default=False)
    shared_with = models.ManyToManyField(
        'fati_accounts.User',
        related_name='shared_dashboards',
        verbose_name=_('partagé avec'),
        blank=True
    )
    
    # Métadonnées
    is_default = models.BooleanField(_('par défaut'), default=False)
    is_active = models.BooleanField(_('actif'), default=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('tableau de bord')
        verbose_name_plural = _('tableaux de bord')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Widget(models.Model):
    """Widget de tableau de bord"""
    
    class WidgetType(models.TextChoices):
        # Indicateurs
        KPI = 'kpi', _('KPI')
        KPI_LIST = 'kpi_list', _('Liste de KPIs')
        
        # Graphiques
        LINE_CHART = 'line_chart', _('Graphique linéaire')
        BAR_CHART = 'bar_chart', _('Graphique à barres')
        PIE_CHART = 'pie_chart', _('Graphique circulaire')
        AREA_CHART = 'area_chart', _('Graphique en aires')
        
        # Cartes
        MAP = 'map', _('Carte')
        MAP_HEATMAP = 'map_heatmap', _('Carte de chaleur')
        
        # Tableaux
        DATA_TABLE = 'data_table', _('Tableau de données')
        FACILITY_LIST = 'facility_list', _('Liste de structures')
        
        # Alertes
        ALERT_LIST = 'alert_list', _('Liste d\'alertes')
        ALERT_SUMMARY = 'alert_summary', _('Résumé des alertes')
        
        # Autres
        TEXT = 'text', _('Texte')
        IMAGE = 'image', _('Image')
        IFRAME = 'iframe', _('IFrame')
    
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets',
        verbose_name=_('tableau de bord')
    )
    
    name = models.CharField(_('nom'), max_length=255)
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=WidgetType.choices
    )
    
    # Position et taille
    position_x = models.PositiveIntegerField(_('position X'), default=0)
    position_y = models.PositiveIntegerField(_('position Y'), default=0)
    width = models.PositiveIntegerField(_('largeur'), default=4)
    height = models.PositiveIntegerField(_('hauteur'), default=4)
    
    # Configuration du widget
    config = models.JSONField(
        _('configuration'),
        default=dict,
        help_text=_('Configuration spécifique au type de widget')
    )
    
    # Données
    data_source = models.CharField(
        _('source de données'),
        max_length=100,
        blank=True,
        help_text=_('Identifiant de la source de données')
    )
    
    # Filtres
    filters = models.JSONField(
        _('filtres'),
        default=dict,
        blank=True
    )
    
    # Rafraîchissement automatique
    refresh_interval = models.PositiveIntegerField(
        _('intervalle de rafraîchissement (secondes)'),
        null=True,
        blank=True
    )
    
    is_active = models.BooleanField(_('actif'), default=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('widget')
        verbose_name_plural = _('widgets')
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.dashboard.name} - {self.name}"


class ReportTemplate(models.Model):
    """Modèle de rapport"""
    
    class ReportFormat(models.TextChoices):
        PDF = 'pdf', _('PDF')
        EXCEL = 'excel', _('Excel')
        CSV = 'csv', _('CSV')
        HTML = 'html', _('HTML')
    
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    # Secteur
    sector = models.CharField(
        _('secteur'),
        max_length=20,
        choices=[
            ('health', _('Santé')),
            ('education', _('Éducation')),
            ('both', _('Les deux')),
        ],
        default='both'
    )
    
    # Configuration
    template_config = models.JSONField(
        _('configuration du modèle'),
        default=dict,
        help_text=_('Sections et contenu du rapport')
    )
    
    # Formats disponibles
    available_formats = models.JSONField(
        _('formats disponibles'),
        default=list,
        help_text=_('Liste des formats de sortie')
    )
    
    # Paramètres
    parameters = models.JSONField(
        _('paramètres'),
        default=list,
        help_text=_('Paramètres requis pour générer le rapport')
    )
    
    is_active = models.BooleanField(_('actif'), default=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('modèle de rapport')
        verbose_name_plural = _('modèles de rapports')
    
    def __str__(self):
        return self.name


class GeneratedReport(models.Model):
    """Rapport généré"""
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='generated_reports',
        verbose_name=_('modèle')
    )
    
    name = models.CharField(_('nom'), max_length=255)
    
    # Paramètres utilisés
    parameters = models.JSONField(_('paramètres'), default=dict)
    
    # Fichier généré
    file = models.FileField(
        _('fichier'),
        upload_to='reports/%Y/%m/',
        null=True,
        blank=True
    )
    
    format = models.CharField(_('format'), max_length=10)
    
    # Génération
    generated_by = models.ForeignKey(
        'fati_accounts.User',
        on_delete=models.CASCADE,
        related_name='generated_reports',
        verbose_name=_('généré par')
    )
    generated_at = models.DateTimeField(_('généré le'), auto_now_add=True)
    
    # Statut
    class Status(models.TextChoices):
        PENDING = 'pending', _('En attente')
        GENERATING = 'generating', _('En cours')
        COMPLETED = 'completed', _('Terminé')
        FAILED = 'failed', _('Échec')
    
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    error_message = models.TextField(_('message d\'erreur'), blank=True)
    
    class Meta:
        verbose_name = _('rapport généré')
        verbose_name_plural = _('rapports générés')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.name} ({self.generated_at})"
