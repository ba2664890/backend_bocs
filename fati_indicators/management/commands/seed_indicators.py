"""
Commande pour initialiser les indicateurs de santé et d'éducation
"""
from django.core.management.base import BaseCommand
from fati_indicators.models import Indicator, IndicatorCategory
from fati_geography.models import Region


class Command(BaseCommand):
    help = 'Initialise les indicateurs de santé et d\'éducation'
    
    HEALTH_CATEGORIES = [
        {'name': 'Santé maternelle', 'order': 1},
        {'name': 'Santé infantile', 'order': 2},
        {'name': 'Maladies chroniques', 'order': 3},
        {'name': 'Épidémiologie', 'order': 4},
        {'name': 'Infrastructures sanitaires', 'order': 5},
    ]
    
    EDUCATION_CATEGORIES = [
        {'name': 'Accès à l\'éducation', 'order': 1},
        {'name': 'Qualité de l\'enseignement', 'order': 2},
        {'name': 'Résultats scolaires', 'order': 3},
        {'name': 'Infrastructures scolaires', 'order': 4},
        {'name': 'Personnel enseignant', 'order': 5},
    ]
    
    HEALTH_INDICATORS = [
        {
            'code': 'SANTE-001',
            'name': 'Taux de couverture des consultations prénatales (CPN)',
            'category': 'Santé maternelle',
            'description': 'Pourcentage de femmes enceintes ayant effectué au moins 4 consultations prénatales',
            'unit': '%',
            'target_value': 80.0,
            'alert_threshold_low': 60.0,
        },
        {
            'code': 'SANTE-002',
            'name': 'Taux d\'accouchements assistés',
            'category': 'Santé maternelle',
            'description': 'Pourcentage d\'accouchements assistés par du personnel qualifié',
            'unit': '%',
            'target_value': 90.0,
            'alert_threshold_low': 70.0,
        },
        {
            'code': 'SANTE-003',
            'name': 'Taux de mortalité maternelle',
            'category': 'Santé maternelle',
            'description': 'Nombre de décès maternels pour 100 000 naissances vivantes',
            'unit': '/100000',
            'target_value': 100.0,
            'alert_threshold_high': 200.0,
        },
        {
            'code': 'SANTE-004',
            'name': 'Taux de vaccination complète des enfants',
            'category': 'Santé infantile',
            'description': 'Pourcentage d\'enfants de 12-23 mois complètement vaccinés',
            'unit': '%',
            'target_value': 95.0,
            'alert_threshold_low': 80.0,
        },
        {
            'code': 'SANTE-005',
            'name': 'Prévalence de la malnutrition aiguë',
            'category': 'Santé infantile',
            'description': 'Pourcentage d\'enfants de moins de 5 ans souffrant de malnutrition aiguë',
            'unit': '%',
            'target_value': 5.0,
            'alert_threshold_high': 10.0,
        },
        {
            'code': 'SANTE-006',
            'name': 'Taux d\'utilisation des moustiquaires imprégnées',
            'category': 'Épidémiologie',
            'description': 'Pourcentage de population dormant sous moustiquaire imprégnée',
            'unit': '%',
            'target_value': 80.0,
            'alert_threshold_low': 60.0,
        },
        {
            'code': 'SANTE-007',
            'name': 'Taux de prévalence du paludisme',
            'category': 'Épidémiologie',
            'description': 'Pourcentage de cas de paludisme pour 1000 habitants',
            'unit': '‰',
            'target_value': 50.0,
            'alert_threshold_high': 100.0,
        },
        {
            'code': 'SANTE-008',
            'name': 'Nombre de centres de santé pour 10000 habitants',
            'category': 'Infrastructures sanitaires',
            'description': 'Densité des centres de santé par population',
            'unit': '/10000',
            'target_value': 2.0,
            'alert_threshold_low': 1.0,
        },
        {
            'code': 'SANTE-009',
            'name': 'Taux de couverture en médicaments essentiels',
            'category': 'Infrastructures sanitaires',
            'description': 'Pourcentage de structures disposant des médicaments essentiels',
            'unit': '%',
            'target_value': 90.0,
            'alert_threshold_low': 70.0,
        },
        {
            'code': 'SANTE-010',
            'name': 'Taux de diabète dépisté et pris en charge',
            'category': 'Maladies chroniques',
            'description': 'Pourcentage de patients diabétiques sous traitement régulier',
            'unit': '%',
            'target_value': 60.0,
            'alert_threshold_low': 40.0,
        },
    ]
    
    EDUCATION_INDICATORS = [
        {
            'code': 'EDUC-001',
            'name': 'Taux brut de scolarisation au primaire',
            'category': 'Accès à l\'éducation',
            'description': 'Pourcentage d\'enfants d\'âge scolaire inscrits à l\'école primaire',
            'unit': '%',
            'target_value': 100.0,
            'alert_threshold_low': 85.0,
        },
        {
            'code': 'EDUC-002',
            'name': 'Taux net de scolarisation au primaire',
            'category': 'Accès à l\'éducation',
            'description': 'Pourcentage d\'enfants du bon âge inscrits à l\'école primaire',
            'unit': '%',
            'target_value': 95.0,
            'alert_threshold_low': 80.0,
        },
        {
            'code': 'EDUC-003',
            'name': 'Taux d\'achèvement du primaire',
            'category': 'Résultats scolaires',
            'description': 'Pourcentage d\'enfants terminant le cycle primaire',
            'unit': '%',
            'target_value': 85.0,
            'alert_threshold_low': 70.0,
        },
        {
            'code': 'EDUC-004',
            'name': 'Taux d\'alphabétisation des jeunes (15-24 ans)',
            'category': 'Résultats scolaires',
            'description': 'Pourcentage de jeunes sachant lire et écrire',
            'unit': '%',
            'target_value': 90.0,
            'alert_threshold_low': 75.0,
        },
        {
            'code': 'EDUC-005',
            'name': 'Ratio élèves par salle de classe',
            'category': 'Infrastructures scolaires',
            'description': 'Nombre moyen d\'élèves par salle de classe',
            'unit': 'élèves',
            'target_value': 40.0,
            'alert_threshold_high': 60.0,
        },
        {
            'code': 'EDUC-006',
            'name': 'Taux d\'écoles avec accès à l\'eau potable',
            'category': 'Infrastructures scolaires',
            'description': 'Pourcentage d\'écoles disposant d\'eau potable',
            'unit': '%',
            'target_value': 90.0,
            'alert_threshold_low': 70.0,
        },
        {
            'code': 'EDUC-007',
            'name': 'Taux d\'écoles avec latrines fonctionnelles',
            'category': 'Infrastructures scolaires',
            'description': 'Pourcentage d\'écoles avec latrines en bon état',
            'unit': '%',
            'target_value': 85.0,
            'alert_threshold_low': 65.0,
        },
        {
            'code': 'EDUC-008',
            'name': 'Ratio élèves par enseignant',
            'category': 'Personnel enseignant',
            'description': 'Nombre d\'élèves par enseignant',
            'unit': 'élèves',
            'target_value': 35.0,
            'alert_threshold_high': 50.0,
        },
        {
            'code': 'EDUC-009',
            'name': 'Taux d\'enseignants qualifiés',
            'category': 'Personnel enseignant',
            'description': 'Pourcentage d\'enseignants avec formation pédagogique',
            'unit': '%',
            'target_value': 80.0,
            'alert_threshold_low': 60.0,
        },
        {
            'code': 'EDUC-010',
            'name': 'Taux de réussite au CFEE',
            'category': 'Résultats scolaires',
            'description': 'Pourcentage d\'élèves réussissant le CFEE',
            'unit': '%',
            'target_value': 75.0,
            'alert_threshold_low': 60.0,
        },
    ]
    
    def handle(self, *args, **options):
        self.stdout.write('Création des catégories d\'indicateurs...')
        
        # Créer les catégories santé
        for cat_data in self.HEALTH_CATEGORIES:
            cat, created = IndicatorCategory.objects.get_or_create(
                name=cat_data['name'],
                sector='health',
                defaults={'order': cat_data['order']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Catégorie santé: {cat.name}')
                )
        
        # Créer les catégories éducation
        for cat_data in self.EDUCATION_CATEGORIES:
            cat, created = IndicatorCategory.objects.get_or_create(
                name=cat_data['name'],
                sector='education',
                defaults={'order': cat_data['order']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Catégorie éducation: {cat.name}')
                )
        
        # Récupérer toutes les régions pour les assigner
        all_regions = list(Region.objects.all())
        
        self.stdout.write('\nCréation des indicateurs de santé...')
        for ind_data in self.HEALTH_INDICATORS:
            category = IndicatorCategory.objects.get(
                name=ind_data['category'],
                sector='health'
            )
            
            indicator, created = Indicator.objects.get_or_create(
                code=ind_data['code'],
                defaults={
                    'name': ind_data['name'],
                    'description': ind_data['description'],
                    'sector': 'health',
                    'category': category,
                    'data_type': 'percentage' if ind_data['unit'] == '%' else 'number',
                    'unit': ind_data['unit'],
                    'target_value': ind_data.get('target_value'),
                    'alert_threshold_low': ind_data.get('alert_threshold_low'),
                    'alert_threshold_high': ind_data.get('alert_threshold_high'),
                }
            )
            
            if created:
                indicator.applicable_regions.set(all_regions)
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Indicateur: {indicator.name}')
                )
        
        self.stdout.write('\nCréation des indicateurs d\'éducation...')
        for ind_data in self.EDUCATION_INDICATORS:
            category = IndicatorCategory.objects.get(
                name=ind_data['category'],
                sector='education'
            )
            
            indicator, created = Indicator.objects.get_or_create(
                code=ind_data['code'],
                defaults={
                    'name': ind_data['name'],
                    'description': ind_data['description'],
                    'sector': 'education',
                    'category': category,
                    'data_type': 'percentage' if ind_data['unit'] == '%' else 'number',
                    'unit': ind_data['unit'],
                    'target_value': ind_data.get('target_value'),
                    'alert_threshold_low': ind_data.get('alert_threshold_low'),
                    'alert_threshold_high': ind_data.get('alert_threshold_high'),
                }
            )
            
            if created:
                indicator.applicable_regions.set(all_regions)
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Indicateur: {indicator.name}')
                )
        
        total = Indicator.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'\n{total} indicateurs initialisés!')
        )
