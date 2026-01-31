"""
FATI Accounts - Modèles utilisateurs
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.gis.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Modèle utilisateur personnalisé FATI"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrateur')
        INSTITUTION = 'institution', _('Institution')
        SECTOR_HEALTH = 'sector_health', _('Secteur Santé')
        SECTOR_EDUCATION = 'sector_education', _('Secteur Éducation')
        LOCAL_MANAGER = 'local_manager', _('Responsable Local')
        CONTRIBUTOR = 'contributor', _('Contributeur')
        VIEWER = 'viewer', _('Lecteur')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Actif')
        INACTIVE = 'inactive', _('Inactif')
        PENDING = 'pending', _('En attente')
        SUSPENDED = 'suspended', _('Suspendu')
    
    email = models.EmailField(_('email'), unique=True)
    first_name = models.CharField(_('prénom'), max_length=150)
    last_name = models.CharField(_('nom'), max_length=150)
    
    role = models.CharField(
        _('rôle'),
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER
    )
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Organisation
    organization = models.CharField(_('organisation'), max_length=255, blank=True)
    department = models.CharField(_('département'), max_length=255, blank=True)
    phone = models.CharField(_('téléphone'), max_length=20, blank=True)
    
    # Géographie assignée
    assigned_region = models.ForeignKey(
        'fati_geography.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_users',
        verbose_name=_('région assignée')
    )
    assigned_department = models.ForeignKey(
        'fati_geography.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_users',
        verbose_name=_('département assigné')
    )
    assigned_commune = models.ForeignKey(
        'fati_geography.Commune',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_users',
        verbose_name=_('commune assignée')
    )
    
    # Avatar
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        blank=True,
        null=True
    )
    
    # Timestamps
    last_login_at = models.DateTimeField(_('dernière connexion'), null=True, blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    # Django admin fields
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('actif'), default=True)
    is_superuser = models.BooleanField(_('superutilisateur'), default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name
    
    def update_last_login(self):
        self.last_login_at = timezone.now()
        self.save(update_fields=['last_login_at'])
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_institution(self):
        return self.role == self.Role.INSTITUTION
    
    @property
    def is_sector_user(self):
        return self.role in [self.Role.SECTOR_HEALTH, self.Role.SECTOR_EDUCATION]
    
    @property
    def is_local_manager(self):
        return self.role == self.Role.LOCAL_MANAGER
    
    @property
    def is_contributor(self):
        return self.role == self.Role.CONTRIBUTOR


class Permission(models.Model):
    """Permissions personnalisées par rôle"""
    
    class Resource(models.TextChoices):
        DASHBOARD = 'dashboard', _('Tableau de bord')
        INDICATORS = 'indicators', _('Indicateurs')
        FACILITIES = 'facilities', _('Structures')
        COLLECTIONS = 'collections', _('Collectes')
        REPORTS = 'reports', _('Rapports')
        USERS = 'users', _('Utilisateurs')
        SETTINGS = 'settings', _('Paramètres')
        AUDIT = 'audit', _('Audit')
        ALL = '*', _('Tout')
    
    class Action(models.TextChoices):
        CREATE = 'create', _('Créer')
        READ = 'read', _('Lire')
        UPDATE = 'update', _('Modifier')
        DELETE = 'delete', _('Supprimer')
        VALIDATE = 'validate', _('Valider')
        EXPORT = 'export', _('Exporter')
    
    role = models.CharField(_('rôle'), max_length=20, choices=User.Role.choices)
    resource = models.CharField(
        _('ressource'),
        max_length=50,
        choices=Resource.choices
    )
    actions = models.JSONField(_('actions'), default=list)
    
    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        unique_together = ['role', 'resource']
    
    def __str__(self):
        return f"{self.role} - {self.resource}"
