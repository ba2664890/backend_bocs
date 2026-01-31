"""
FATI - Script de peuplement de la base de données
Utilise les fichiers SEN_adm pour les données géographiques réelles
"""
import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fati_backend.settings')
django.setup()

from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource
from django.contrib.auth import get_user_model
from fati_geography.models import Region, Department, Commune
from fati_facilities.models import HealthFacility, EducationFacility, Equipment, Staff
from fati_indicators.models import Indicator, IndicatorValue
from fati_workflows.models import Alert
import json

User = get_user_model()

def populate_regions():
    """Peuple les régions depuis SEN_adm1.shp"""
    print("📍 Importation des régions depuis SEN_adm1.shp...")
    
    shp_path = 'SEN_adm/SEN_adm1.shp'
    ds = DataSource(shp_path)
    layer = ds[0]
    
    # Charger les données CSV pour la population et PIB
    csv_data = {}
    with open('SEN_adm/SEN_adm1.csv', 'r', encoding='latin-1') as f:
        lines = f.readlines()[1:]  # Skip header
        for line in lines:
            parts = line.strip().split(';')
            if len(parts) >= 3:
                name = parts[0]
                pop = parts[2].replace(',', '').replace(' ', '')
                try:
                    csv_data[name] = int(float(pop))
                except:
                    csv_data[name] = 500000
    
    for feature in layer:
        name = feature.get('NAME_1')
        id_region = feature.get('ID_region')
        pop = feature.get('Pop')
        geom = feature.geom
        
        # Obtenir le centroïde pour la location
        centroid = geom.geos.centroid
        
        # Convertir Polygon en MultiPolygon si nécessaire
        from django.contrib.gis.geos import MultiPolygon
        if geom.geos.geom_type == 'Polygon':
            geometry = MultiPolygon(geom.geos)
        else:
            geometry = geom.geos
        
        region, created = Region.objects.update_or_create(
            code=f"R{id_region:02d}",
            defaults={
                'name': name,
                'centroid': centroid,
                'geometry': geometry,
                'population': pop if pop else 500000,
                'area_km2': int(geom.geos.area * 10000),  # Approximation
            }
        )
        
        if created:
            print(f"  ✓ Région créée: {region.name} (Pop: {region.population:,})")
        else:
            print(f"  ↻ Région mise à jour: {region.name}")
    
    print(f"✅ {Region.objects.count()} régions importées")
    return Region.objects.all()

def populate_departments():
    """Peuple les départements depuis SEN_adm2.shp"""
    print("\n📍 Importation des départements depuis SEN_adm2.shp...")
    
    shp_path = 'SEN_adm/SEN_adm2.shp'
    ds = DataSource(shp_path)
    layer = ds[0]
    
    for feature in layer:
        # Les champs peuvent varier, essayer différentes variantes
        try:
            region_id = feature.get('ID_1')
        except:
            region_id = feature.get('ID_region')
        dept_name = feature.get('NAME_2')
        try:
            dept_id = feature.get('ID_2')
        except:
            dept_id = feature.get('OBJECTID')
        geom = feature.geom
        
        # Trouver la région correspondante
        try:
            region = Region.objects.get(code=f"R{region_id:02d}")
        except Region.DoesNotExist:
            print(f"  ⚠ Région non trouvée pour ID {region_id}")
            continue
        
        centroid = geom.geos.centroid
        
        dept, created = Department.objects.update_or_create(
            code=f"D{dept_id:03d}",
            defaults={
                'name': dept_name,
                'region': region,
                'centroid': centroid,
                'geometry': geom.geos,
                'population': random.randint(50000, 500000),
                'area_km2': int(geom.geos.area * 10000),
            }
        )
        
        if created:
            print(f"  ✓ Département créé: {dept.name} ({region.name})")
    
    print(f"✅ {Department.objects.count()} départements importés")
    return Department.objects.all()

def populate_communes():
    """Peuple les communes depuis SEN_adm3.shp"""
    print("\n📍 Importation des communes depuis SEN_adm3.shp...")
    
    shp_path = 'SEN_adm/SEN_adm3.shp'
    ds = DataSource(shp_path)
    layer = ds[0]
    
    count = 0
    for feature in layer:
        try:
            dept_id = feature.get('ID_2')
        except:
            dept_id = feature.get('OBJECTID')
        commune_name = feature.get('NAME_3')
        try:
            commune_id = feature.get('ID_3')
        except:
            commune_id = feature.get('OBJECTID')
        geom = feature.geom
        
        # Trouver le département correspondant
        try:
            dept = Department.objects.get(code=f"D{dept_id:03d}")
        except Department.DoesNotExist:
            continue
        
        centroid = geom.geos.centroid
        
        commune, created = Commune.objects.update_or_create(
            code=f"C{commune_id:04d}",
            defaults={
                'name': commune_name,
                'department': dept,
                'centroid': centroid,
                'geometry': geom.geos,
                'population': random.randint(10000, 100000),
                'area_km2': int(geom.geos.area * 10000),
            }
        )
        
        if created:
            count += 1
            if count % 20 == 0:
                print(f"  ✓ {count} communes créées...")
    
    print(f"✅ {Commune.objects.count()} communes importées")
    return Commune.objects.all()

def populate_health_facilities():
    """Peuple les structures de santé depuis sante.json"""
    print("\n🏥 Importation des structures de santé...")
    
    # Charger le fichier JSON
    json_path = '/home/cardan/Pictures/pro_suivi/sante.json'
    if not os.path.exists(json_path):
        print("  ⚠ Fichier sante.json non trouvé, création de données fictives...")
        create_sample_health_facilities()
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    regions = {r.name: r for r in Region.objects.all()}
    
    for item in data.get('features', []):
        props = item.get('properties', {})
        geom = item.get('geometry', {})
        
        # Extraire les coordonnées
        coords = geom.get('coordinates', [])
        if not coords or len(coords) < 2:
            continue
        
        lon, lat = coords[0], coords[1]
        
        # Trouver la région la plus proche
        region = find_closest_region(lat, lon, regions)
        if not region:
            continue
        
        facility_name = props.get('nom', props.get('name', f'Structure Santé {props.get("id", "")}'))
        facility_type = props.get('type', 'health_center').lower()
        
        # Mapper les types
        type_mapping = {
            'hopital': 'hospital',
            'hospital': 'hospital',
            'centre de santé': 'health_center',
            'health_center': 'health_center',
            'poste de santé': 'health_post',
            'health_post': 'health_post',
            'clinique': 'clinic',
            'clinic': 'clinic',
        }
        facility_type = type_mapping.get(facility_type, 'health_center')
        
        from django.contrib.gis.geos import Point
        facility, created = HealthFacility.objects.get_or_create(
            name=facility_name,
            defaults={
                'code': f"HS-{props.get('id', random.randint(1000, 9999))}",
                'type': facility_type,
                'region': region,
                'centroid': Point(lon, lat),
                'address': props.get('adresse', f'{region.name}'),
                'phone': props.get('telephone', ''),
                'capacity': props.get('capacite', random.randint(20, 200)),
                'status': 'operational',
            }
        )
        
        if created:
            # Ajouter du personnel
            Staff.objects.create(
                facility=facility,
                position='doctor',
                count=random.randint(2, 15),
                qualification='MD'
            )
            Staff.objects.create(
                facility=facility,
                position='nurse',
                count=random.randint(5, 30),
                qualification='RN'
            )
    
    print(f"✅ {HealthFacility.objects.count()} structures de santé importées")

def populate_education_facilities():
    """Peuple les structures d'éducation depuis education.json"""
    print("\n🎓 Importation des structures d'éducation...")
    
    json_path = '/home/cardan/Pictures/pro_suivi/education.json'
    if not os.path.exists(json_path):
        print("  ⚠ Fichier education.json non trouvé, création de données fictives...")
        create_sample_education_facilities()
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    regions = {r.name: r for r in Region.objects.all()}
    
    for item in data.get('features', []):
        props = item.get('properties', {})
        geom = item.get('geometry', {})
        
        coords = geom.get('coordinates', [])
        if not coords or len(coords) < 2:
            continue
        
        lon, lat = coords[0], coords[1]
        region = find_closest_region(lat, lon, regions)
        if not region:
            continue
        
        facility_name = props.get('nom', props.get('name', f'École {props.get("id", "")}'))
        facility_type = props.get('type', 'elementary').lower()
        
        type_mapping = {
            'élémentaire': 'elementary',
            'elementary': 'elementary',
            'primaire': 'elementary',
            'collège': 'middle_school',
            'middle_school': 'middle_school',
            'lycée': 'high_school',
            'high_school': 'high_school',
            'université': 'university',
            'university': 'university',
        }
        facility_type = type_mapping.get(facility_type, 'elementary')
        
        from django.contrib.gis.geos import Point
        facility, created = EducationFacility.objects.get_or_create(
            name=facility_name,
            defaults={
                'code': f"ED-{props.get('id', random.randint(1000, 9999))}",
                'type': facility_type,
                'region': region,
                'centroid': Point(lon, lat),
                'address': props.get('adresse', f'{region.name}'),
                'phone': props.get('telephone', ''),
                'capacity': props.get('capacite', random.randint(200, 1000)),
                'enrollment': props.get('effectif', random.randint(150, 900)),
                'status': 'operational',
            }
        )
        
        if created:
            Staff.objects.create(
                facility=facility,
                position='teacher',
                count=random.randint(10, 50),
                qualification='Bachelor'
            )
    
    print(f"✅ {EducationFacility.objects.count()} structures d'éducation importées")

def find_closest_region(lat, lon, regions):
    """Trouve la région la plus proche d'un point"""
    from django.contrib.gis.geos import Point
    point = Point(lon, lat)
    
    min_dist = float('inf')
    closest_region = None
    
    for region in regions.values():
        if region.geometry and region.geometry.contains(point):
            return region
        
        dist = region.centroid.distance(point)
        if dist < min_dist:
            min_dist = dist
            closest_region = region
    
    return closest_region

def create_sample_health_facilities():
    """Crée des structures de santé fictives si pas de JSON"""
    regions = list(Region.objects.all())
    facility_types = ['hospital', 'health_center', 'health_post', 'clinic']
    
    for i in range(50):
        region = random.choice(regions)
        facility_type = random.choice(facility_types)
        
        from django.contrib.gis.geos import Point
        # Point aléatoire dans la région
        bounds = region.geometry.extent
        lon = random.uniform(bounds[0], bounds[2])
        lat = random.uniform(bounds[1], bounds[3])
        
        facility, created = HealthFacility.objects.get_or_create(
            name=f"Structure Santé {region.name} {i+1}",
            defaults={
                'code': f"HS-{region.code}-{i+1:03d}",
                'type': facility_type,
                'region': region,
                'centroid': Point(lon, lat),
                'address': f"Avenue {i+1}, {region.name}",
                'capacity': random.randint(20, 200),
                'status': 'operational',
            }
        )
        
        if created:
            Staff.objects.create(facility=facility, position='doctor', count=random.randint(2, 15), qualification='MD')
            Staff.objects.create(facility=facility, position='nurse', count=random.randint(5, 30), qualification='RN')

def create_sample_education_facilities():
    """Crée des structures d'éducation fictives si pas de JSON"""
    regions = list(Region.objects.all())
    facility_types = ['elementary', 'middle_school', 'high_school', 'university']
    
    for i in range(80):
        region = random.choice(regions)
        facility_type = random.choice(facility_types)
        
        from django.contrib.gis.geos import Point
        bounds = region.geometry.extent
        lon = random.uniform(bounds[0], bounds[2])
        lat = random.uniform(bounds[1], bounds[3])
        
        facility, created = EducationFacility.objects.get_or_create(
            name=f"École {region.name} {i+1}",
            defaults={
                'code': f"ED-{region.code}-{i+1:03d}",
                'type': facility_type,
                'region': region,
                'centroid': Point(lon, lat),
                'address': f"Rue {i+1}, {region.name}",
                'capacity': random.randint(200, 1000),
                'enrollment': random.randint(150, 900),
                'status': 'operational',
            }
        )
        
        if created:
            Staff.objects.create(facility=facility, position='teacher', count=random.randint(10, 50), qualification='Bachelor')

def populate_indicators():
    """Crée les indicateurs"""
    print("\n📊 Création des indicateurs...")
    
    health_indicators = [
        {'name': 'Taux de vaccination DTC3', 'unit': '%', 'category': 'vaccination'},
        {'name': 'Mortalité maternelle', 'unit': 'pour 100 000', 'category': 'maternal_health'},
        {'name': 'Prévalence du paludisme', 'unit': '%', 'category': 'disease'},
        {'name': 'Couverture consultations prénatales', 'unit': '%', 'category': 'maternal_health'},
        {'name': 'Taux de malnutrition infantile', 'unit': '%', 'category': 'nutrition'},
    ]
    
    education_indicators = [
        {'name': 'Taux de scolarisation primaire', 'unit': '%', 'category': 'enrollment'},
        {'name': 'Ratio élèves/enseignant', 'unit': 'ratio', 'category': 'quality'},
        {'name': 'Taux de réussite au BFEM', 'unit': '%', 'category': 'performance'},
        {'name': 'Taux d\'abandon scolaire', 'unit': '%', 'category': 'retention'},
        {'name': 'Taux d\'alphabétisation', 'unit': '%', 'category': 'literacy'},
    ]
    
    for ind_data in health_indicators + education_indicators:
        sector = 'health' if ind_data in health_indicators else 'education'
        ind, created = Indicator.objects.get_or_create(
            name=ind_data['name'],
            defaults={
                'code': f"{sector[:4].upper()}-{ind_data['name'][:4].upper()}",
                'sector': sector,
                'category': ind_data['category'],
                'unit': ind_data['unit'],
                'description': f"Indicateur de {sector}: {ind_data['name']}",
                'frequency': 'annual',
                'is_active': True,
            }
        )
        if created:
            print(f"  ✓ {ind.name}")
    
    print(f"✅ {Indicator.objects.count()} indicateurs créés")

def populate_indicator_values():
    """Crée les valeurs d'indicateurs"""
    print("\n📈 Création des valeurs d'indicateurs...")
    
    indicators = Indicator.objects.all()
    regions = list(Region.objects.all())
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    
    count = 0
    for indicator in indicators:
        for region in regions:
            for year in years:
                if 'taux' in indicator.name.lower() or '%' in indicator.unit:
                    base_value = random.uniform(60, 95)
                    value = base_value + (year - 2020) * random.uniform(0.5, 2.0)
                    value = min(100, max(0, value))
                elif 'mortalité' in indicator.name.lower():
                    base_value = random.uniform(200, 400)
                    value = base_value - (year - 2020) * random.uniform(5, 15)
                    value = max(100, value)
                elif 'ratio' in indicator.unit.lower():
                    value = random.uniform(25, 45)
                else:
                    value = random.uniform(50, 100)
                
                IndicatorValue.objects.get_or_create(
                    indicator=indicator,
                    geographic_entity_id=region.id,
                    year=year,
                    defaults={
                        'value': Decimal(str(round(value, 2))),
                        'status': random.choice(['validated', 'validated', 'validated', 'pending']),
                        'source': 'Ministère',
                        'collection_date': datetime(year, 12, 31).date(),
                    }
                )
                count += 1
    
    print(f"✅ {count} valeurs créées")

def populate_users():
    """Crée des utilisateurs supplémentaires"""
    print("\n👥 Création des utilisateurs...")
    
    users_data = [
        {'email': 'sante@fati.gov', 'first_name': 'Dr. Aminata', 'last_name': 'Diop', 'role': 'sector_health', 'organization': 'Ministère de la Santé'},
        {'email': 'education@fati.gov', 'first_name': 'Prof. Mamadou', 'last_name': 'Sall', 'role': 'sector_education', 'organization': 'Ministère de l\'Éducation'},
    ]
    
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'role': user_data['role'],
                'status': 'active',
                'organization': user_data['organization'],
                'is_active': True,
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            print(f"  ✓ {user.email}")
    
    print(f"✅ {User.objects.count()} utilisateurs")

def populate_alerts():
    """Crée des alertes"""
    print("\n⚠️  Création des alertes...")
    
    regions = list(Region.objects.all())
    indicators = list(Indicator.objects.all())
    
    alert_templates = [
        {'title': 'Taux de vaccination faible', 'severity': 'high', 'sector': 'health'},
        {'title': 'Abandon scolaire élevé', 'severity': 'high', 'sector': 'education'},
        {'title': 'Manque de personnel médical', 'severity': 'critical', 'sector': 'health'},
        {'title': 'Infrastructure scolaire dégradée', 'severity': 'medium', 'sector': 'education'},
        {'title': 'Données manquantes', 'severity': 'medium', 'sector': 'health'},
    ]
    
    for template in alert_templates * 3:
        region = random.choice(regions)
        indicator = random.choice([ind for ind in indicators if ind.sector == template['sector']])
        
        Alert.objects.create(
            title=f"{template['title']} - {region.name}",
            message=f"Alerte concernant {indicator.name} dans la région de {region.name}",
            severity=template['severity'],
            sector=template['sector'],
            region=region,
            indicator=indicator,
            status=random.choice(['active', 'active', 'acknowledged']),
            is_read=random.choice([False, False, True]),
        )
    
    print(f"✅ {Alert.objects.count()} alertes")

def main():
    """Fonction principale"""
    print("🚀 Démarrage du peuplement de la base de données FATI")
    print("=" * 60)
    
    try:
        populate_regions()
        populate_departments()
        populate_communes()
        populate_health_facilities()
        populate_education_facilities()
        populate_indicators()
        populate_indicator_values()
        populate_users()
        populate_alerts()
        
        print("\n" + "=" * 60)
        print("✅ Peuplement terminé avec succès!")
        print("\n📊 Résumé:")
        print(f"  - Régions: {Region.objects.count()}")
        print(f"  - Départements: {Department.objects.count()}")
        print(f"  - Communes: {Commune.objects.count()}")
        print(f"  - Structures de santé: {HealthFacility.objects.count()}")
        print(f"  - Structures d'éducation: {EducationFacility.objects.count()}")
        print(f"  - Indicateurs: {Indicator.objects.count()}")
        print(f"  - Valeurs d'indicateurs: {IndicatorValue.objects.count()}")
        print(f"  - Utilisateurs: {User.objects.count()}")
        print(f"  - Alertes: {Alert.objects.count()}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
