"""
Commande pour créer un superutilisateur FATI
"""
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from fati_accounts.models import User


class Command(BaseCommand):
    help = 'Crée un superutilisateur pour FATI'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@fati.gov.sn',
            help='Email du superutilisateur'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Mot de passe du superutilisateur'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Administrateur',
            help='Prénom du superutilisateur'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='FATI',
            help='Nom du superutilisateur'
        )
    
    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        
        try:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='admin'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Superutilisateur créé avec succès!')
            )
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Mot de passe: {password}')
            self.stdout.write(f'  Nom: {first_name} {last_name}')
            
        except IntegrityError:
            self.stdout.write(
                self.style.WARNING(f'\nUn utilisateur avec l\'email {email} existe déjà.')
            )
            user = User.objects.get(email=email)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS('Privilèges superutilisateur accordés.')
            )
