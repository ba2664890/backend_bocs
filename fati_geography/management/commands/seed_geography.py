"""
Commande pour initialiser les données géographiques du Sénégal
"""
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, MultiPolygon, Polygon
from fati_geography.models import Region, Department, Commune


class Command(BaseCommand):
    help = 'Initialise les données géographiques du Sénégal'
    
    REGIONS_DATA = [
        {'code': 'DK', 'name': 'Dakar', 'population': 4042225},
        {'code': 'ZL', 'name': 'Ziguinchor', 'population': 549151},
        {'code': 'DB', 'name': 'Diourbel', 'population': 1842255},
        {'code': 'SF', 'name': 'Saint-Louis', 'population': 1020335},
        {'code': 'TC', 'name': 'Tambacounda', 'population': 807912},
        {'code': 'KA', 'name': 'Kaolack', 'population': 1198662},
        {'code': 'TH', 'name': 'Thiès', 'population': 2238861},
        {'code': 'LG', 'name': 'Louga', 'population': 1089059},
        {'code': 'FA', 'name': 'Fatick', 'population': 959702},
        {'code': 'KE', 'name': 'Kolda', 'population': 803817},
        {'code': 'MT', 'name': 'Matam', 'population': 706699},
        {'code': 'KN', 'name': 'Kaffrine', 'population': 722464},
        {'code': 'KD', 'name': 'Kédougou', 'population': 181520},
        {'code': 'SE', 'name': 'Sédhiou', 'population': 553041},
    ]
    
    def handle(self, *args, **options):
        self.stdout.write('Création des régions du Sénégal...')
        
        for region_data in self.REGIONS_DATA:
            # Créer un polygone simplifié pour chaque région
            # Note: Ces coordonnées sont approximatives
            centroid = self._get_region_centroid(region_data['code'])
            
            region, created = Region.objects.get_or_create(
                code=region_data['code'],
                defaults={
                    'name': region_data['name'],
                    'population': region_data['population'],
                    'centroid': centroid,
                    'geometry': self._create_simple_polygon(centroid)
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Région créée: {region.name}')
                )
            else:
                self.stdout.write(f'  • Région existante: {region.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n{len(self.REGIONS_DATA)} régions initialisées!')
        )
        
        # Créer quelques départements exemples pour Dakar
        self._create_sample_departments()
    
    def _get_region_centroid(self, code):
        """Retourner le centroïde approximatif d'une région"""
        centroids = {
            'DK': (-17.4677, 14.7167),  # Dakar
            'ZL': (-16.2667, 12.5833),  # Ziguinchor
            'DB': (-16.2333, 14.6603),  # Diourbel
            'SF': (-16.5000, 16.0333),  # Saint-Louis
            'TC': (-13.6667, 13.7667),  # Tambacounda
            'KA': (-16.0667, 14.1500),  # Kaolack
            'TH': (-16.9333, 14.7833),  # Thiès
            'LG': (-15.6167, 15.6167),  # Louga
            'FA': (-16.4167, 14.2833),  # Fatick
            'KE': (-14.9500, 12.8833),  # Kolda
            'MT': (-13.6333, 15.6167),  # Matam
            'KN': (-15.5500, 14.1000),  # Kaffrine
            'KD': (-12.1833, 12.5500),  # Kédougou
            'SE': (-15.5500, 12.7000),  # Sédhiou
        }
        lon, lat = centroids.get(code, (-15.0, 14.0))
        return Point(lon, lat, srid=4326)
    
    def _create_simple_polygon(self, centroid):
        """Créer un polygone simple autour d'un point"""
        lon, lat = centroid.x, centroid.y
        offset = 0.5  # degrés
        
        coords = [
            (lon - offset, lat - offset),
            (lon + offset, lat - offset),
            (lon + offset, lat + offset),
            (lon - offset, lat + offset),
            (lon - offset, lat - offset),
        ]
        
        polygon = Polygon(coords, srid=4326)
        return MultiPolygon([polygon], srid=4326)
    
    def _create_sample_departments(self):
        """Créer des départements exemples pour Dakar"""
        self.stdout.write('\nCréation des départements exemples...')
        
        try:
            dakar = Region.objects.get(code='DK')
        except Region.DoesNotExist:
            return
        
        departments = [
            {'code': 'DK01', 'name': 'Dakar', 'population': 1200000},
            {'code': 'DK02', 'name': 'Pikine', 'population': 1300000},
            {'code': 'DK03', 'name': 'Guédiawaye', 'population': 400000},
            {'code': 'DK04', 'name': 'Rufisque', 'population': 600000},
        ]
        
        for dept_data in departments:
            centroid = Point(
                dakar.centroid.x + (hash(dept_data['code']) % 10 - 5) * 0.05,
                dakar.centroid.y + (hash(dept_data['code']) % 10 - 5) * 0.05,
                srid=4326
            )
            
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={
                    'name': dept_data['name'],
                    'region': dakar,
                    'population': dept_data['population'],
                    'centroid': centroid,
                    'geometry': self._create_simple_polygon(centroid)
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Département créé: {dept.name}')
                )
