"""
FATI Accounts - User Manager
"""
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Gestionnaire de modèle utilisateur personnalisé"""
    
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        """Créer et sauvegarder un utilisateur"""
        if not email:
            raise ValueError(_('L\'email est obligatoire'))
        if not first_name:
            raise ValueError(_('Le prénom est obligatoire'))
        if not last_name:
            raise ValueError(_('Le nom est obligatoire'))
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        """Créer et sauvegarder un superutilisateur"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('status', 'active')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_superuser=True.'))
        
        return self.create_user(email, first_name, last_name, password, **extra_fields)
    
    def active(self):
        """Retourner uniquement les utilisateurs actifs"""
        return self.filter(status='active', is_active=True)
    
    def by_role(self, role):
        """Filtrer par rôle"""
        return self.filter(role=role)
    
    def by_region(self, region_id):
        """Filtrer par région assignée"""
        return self.filter(assigned_region_id=region_id)
