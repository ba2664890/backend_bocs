"""
Commande pour créer des utilisateurs de test pour FATI
"""
from django.core.management.base import BaseCommand
from fati_accounts.models import User, UserProfile
from fati_geography.models import Region


class Command(BaseCommand):
    help = 'Crée des utilisateurs de test pour FATI'
    
    USERS_DATA = [
        {
            'email': 'institution@fati.gov.sn',
            'password': 'test123',
            'first_name': 'Directeur',
            'last_name': 'Institution',
            'role': 'institution',
            'phone': '+221 77 123 45 67'
        },
        {
            'email': 'acteur@fati.gov.sn',
            'password': 'test123',
            'first_name': 'Personne',
            'last_name': 'Habilitée',
            'role': 'local_manager',
            'phone': '+221 77 234 56 78'
        },
        {
            'email': 'population@fati.gov.sn',
            'password': 'test123',
            'first_name': 'Annonceur',
            'last_name': 'Population',
            'role': 'annonceur',
            'phone': '+221 77 345 67 89'
        },
        {
            'email': 'local@fati.gov.sn',
            'password': 'test123',
            'first_name': 'Responsable',
            'last_name': 'Local',
            'role': 'local_manager',
            'phone': '+221 77 456 78 90'
        },
        {
            'email': 'contributeur@fati.gov.sn',
            'password': 'test123',
            'first_name': 'Contributeur',
            'last_name': 'Terrain',
            'role': 'contributor',
            'phone': '+221 77 567 89 01'
        },
        {
            'email': 'lecteur@fati.gov.sn',
            'password': 'test123',
            'first_name': 'Utilisateur',
            'last_name': 'Lecteur',
            'role': 'viewer',
            'phone': '+221 77 678 90 12'
        },
    ]
    
    def handle(self, *args, **options):
        self.stdout.write('Création des utilisateurs de test...\n')
        
        # Récupérer une région pour assignation
        dakar_region = Region.objects.filter(code='DK').first()
        
        for user_data in self.USERS_DATA:
            email = user_data['email']
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role'],
                    'phone': user_data['phone'],
                    'is_active': True,
                    'assigned_region': dakar_region
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                
                # Créer le profil utilisateur
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'language': 'fr',
                        'timezone': 'Africa/Dakar'
                    }
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {user.role}: {email} / {password}')
                )
            else:
                self.stdout.write(f'  • Utilisateur existant: {email}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n{len(self.USERS_DATA)} utilisateurs créés!')
        )
        self.stdout.write('\nIdentifiants de test:')
        for user_data in self.USERS_DATA:
            self.stdout.write(f'  {user_data["email"]} / test123')
