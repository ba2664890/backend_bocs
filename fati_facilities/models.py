"""
FATI Facilities - Modèles de structures (santé et éducation)
"""
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class HealthFacility(models.Model):
    """Structure de santé"""
    
    class Type(models.TextChoices):
        HOSPITAL = 'hospital', _('Hôpital')
        HEALTH_CENTER = 'health_center', _('Centre de santé')
        HEALTH_POST = 'health_post', _('Poste de santé')
        CLINIC = 'clinic', _('Clinique')
        OTHER = 'other', _('Autre')
    
    class Category(models.TextChoices):
        REFERENCE = 'reference', _('Hôpital de référence')
        DISTRICT = 'district', _('Hôpital de district')
        REGIONAL = 'regional', _('Hôpital régional')
        UNIVERSITY = 'university', _('CHU')
    
    code = models.CharField(_('code'), max_length=50, unique=True)
    name = models.CharField(_('nom'), max_length=255)
    
    facility_type = models.CharField(
        _('type'),
        max_length=20,
        choices=Type.choices
    )
    category = models.CharField(
        _('catégorie'),
        max_length=20,
        choices=Category.choices,
        blank=True
    )
    
    # Localisation
    commune = models.ForeignKey(
        'fati_geography.Commune',
        on_delete=models.CASCADE,
        related_name='health_facilities',
        verbose_name=_('commune')
    )
    location = models.PointField(_('localisation'), srid=4326, null=True, blank=True)
    address = models.TextField(_('adresse'), blank=True)
    
    # Contact
    phone = models.CharField(_('téléphone'), max_length=50, blank=True)
    email = models.EmailField(_('email'), blank=True)
    manager_name = models.CharField(_('responsable'), max_length=255, blank=True)
    
    # Capacité
    bed_capacity = models.PositiveIntegerField(_('capacité en lits'), null=True, blank=True)
    
    # Services
    services = models.JSONField(_('services'), default=list, blank=True)
    
    # Statut
    is_active = models.BooleanField(_('actif'), default=True)
    
    # Métadonnées
    metadata = models.JSONField(_('métadonnées'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('structure de santé')
        verbose_name_plural = _('structures de santé')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def department(self):
        return self.commune.department
    
    @property
    def region(self):
        return self.commune.department.region


class EducationFacility(models.Model):
    """Établissement d'enseignement"""
    
    class Type(models.TextChoices):
        PRESCHOOL = 'preschool', _('Préscolaire')
        PRIMARY = 'primary', _('Primaire')
        SECONDARY = 'secondary', _('Collège')
        HIGH_SCHOOL = 'high_school', _('Lycée')
        UNIVERSITY = 'university', _('Université')
        VOCATIONAL = 'vocational', _('Formation professionnelle')
    
    class Level(models.TextChoices):
        BASIC = 'basic', _('De base')
        SECONDARY = 'secondary', _('Secondaire')
        SUPERIOR = 'superior', _('Supérieur')
    
    code = models.CharField(_('code'), max_length=50, unique=True)
    name = models.CharField(_('nom'), max_length=255)
    
    facility_type = models.CharField(
        _('type'),
        max_length=20,
        choices=Type.choices
    )
    level = models.CharField(
        _('niveau'),
        max_length=20,
        choices=Level.choices
    )
    
    # Localisation
    commune = models.ForeignKey(
        'fati_geography.Commune',
        on_delete=models.CASCADE,
        related_name='education_facilities',
        verbose_name=_('commune')
    )
    location = models.PointField(_('localisation'), srid=4326, null=True, blank=True)
    address = models.TextField(_('adresse'), blank=True)
    
    # Contact
    phone = models.CharField(_('téléphone'), max_length=50, blank=True)
    email = models.EmailField(_('email'), blank=True)
    principal_name = models.CharField(_('directeur'), max_length=255, blank=True)
    
    # Capacité
    student_capacity = models.PositiveIntegerField(_('capacité d\'accueil'), null=True, blank=True)
    
    # Statut
    is_active = models.BooleanField(_('actif'), default=True)
    
    # Métadonnées
    metadata = models.JSONField(_('métadonnées'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('établissement d\'enseignement')
        verbose_name_plural = _('établissements d\'enseignement')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def department(self):
        return self.commune.department
    
    @property
    def region(self):
        return self.commune.department.region


class Equipment(models.Model):
    """Équipement d'une structure"""
    
    class Category(models.TextChoices):
        IMAGING = 'imaging', _('Imagerie médicale')
        LABORATORY = 'laboratory', _('Laboratoire')
        SURGERY = 'surgery', _('Chirurgie')
        EMERGENCY = 'emergency', _('Urgence')
        OTHER = 'other', _('Autre')
    
    health_facility = models.ForeignKey(
        HealthFacility,
        on_delete=models.CASCADE,
        related_name='equipment',
        verbose_name=_('structure de santé')
    )
    
    name = models.CharField(_('nom'), max_length=255)
    category = models.CharField(
        _('catégorie'),
        max_length=20,
        choices=Category.choices
    )
    
    quantity = models.PositiveIntegerField(_('quantité'), default=0)
    functional = models.PositiveIntegerField(_('fonctionnel'), default=0)
    non_functional = models.PositiveIntegerField(_('non fonctionnel'), default=0)
    
    last_updated = models.DateField(_('dernière mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('équipement')
        verbose_name_plural = _('équipements')
    
    def __str__(self):
        return f"{self.name} - {self.health_facility.name}"


class Staff(models.Model):
    """Personnel d'une structure"""
    
    class Category(models.TextChoices):
        DOCTOR = 'doctor', _('Médecin')
        NURSE = 'nurse', _('Infirmier')
        MIDWIFE = 'midwife', _('Sage-femme')
        TECHNICIAN = 'technician', _('Technicien')
        ADMIN = 'admin', _('Personnel administratif')
        OTHER = 'other', _('Autre')
    
    health_facility = models.ForeignKey(
        HealthFacility,
        on_delete=models.CASCADE,
        related_name='staff',
        verbose_name=_('structure de santé'),
        null=True,
        blank=True
    )
    education_facility = models.ForeignKey(
        EducationFacility,
        on_delete=models.CASCADE,
        related_name='staff',
        verbose_name=_('établissement d\'enseignement'),
        null=True,
        blank=True
    )
    
    category = models.CharField(
        _('catégorie'),
        max_length=20,
        choices=Category.choices
    )
    
    total = models.PositiveIntegerField(_('total'), default=0)
    filled = models.PositiveIntegerField(_('pourvu'), default=0)
    vacant = models.PositiveIntegerField(_('vacant'), default=0)
    
    last_updated = models.DateField(_('dernière mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('personnel')
        verbose_name_plural = _('personnels')
    
    def __str__(self):
        facility = self.health_facility or self.education_facility
        return f"{self.category} - {facility}"
    
    def save(self, *args, **kwargs):
        # Calculer automatiquement les postes vacants
        self.vacant = self.total - self.filled
        super().save(*args, **kwargs)
