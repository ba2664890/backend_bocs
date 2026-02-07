"""
FATI - Script de peuplement simplifié
Utilise CSV pour les départements et communes
"""
import os, django, random, csv
from datetime import datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fati_backend.settings')
django.setup()

from django.contrib.gis.geos import Point, MultiPolygon, Polygon
from django.contrib.auth import get_user_model
from fati_geography.models import Region, Department, Commune
from fati_facilities.models import HealthFacility, EducationFacility, Staff
from fati_indicators.models import Indicator, IndicatorValue
from fati_workflows.models import Alert

User = get_user_model()

def populate_departments_from_csv():
    """Peuple les départements depuis le CSV"""
    print("\n📍 Importation des départements depuis CSV...")
    
    with open('SEN_adm/SEN_adm2.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            region_name = row['NAME_1']
            dept_name = row['NAME_2']
            dept_id = row['ID_2']
            
            try:
                region = Region.objects.get(name=region_name)
            except Region.DoesNotExist:
                continue
            
            # Créer un point aléatoire dans la région
            bounds = region.geometry.extent
            lon = random.uniform(bounds[0], bounds[2])
            lat = random.uniform(bounds[1], bounds[3])
            
            # Créer une petite géométrie autour du point
            offset = 0.1
            poly = Polygon((
                (lon - offset, lat - offset),
                (lon + offset, lat - offset),
                (lon + offset, lat + offset),
                (lon - offset, lat + offset),
                (lon - offset, lat - offset),
            ))
            
            dept, created = Department.objects.get_or_create(
                code=f"D{dept_id}",
                defaults={
                    'name': dept_name,
                    'region': region,
                    'centroid': Point(lon, lat),
                    'geometry': MultiPolygon(poly),
                    'population': random.randint(50000, 500000),
                    'area_km2': random.uniform(500, 5000),
                }
            )
            if created:
                print(f"  ✓ {dept.name} ({region.name})")
    
    print(f"✅ {Department.objects.count()} départements")

def populate_communes_from_csv():
    """Peuple les communes depuis le CSV"""
    print("\n📍 Importation des communes depuis CSV...")
    
    count = 0
    with open('SEN_adm/SEN_adm3.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dept_id = row['ID_2']
            commune_name = row['NAME_3']
            commune_id = row['ID_3']
            
            try:
                dept = Department.objects.get(code=f"D{dept_id}")
            except Department.DoesNotExist:
                continue
            
            # Point aléatoire dans le département
            bounds = dept.geometry.extent
            lon = random.uniform(bounds[0], bounds[2])
            lat = random.uniform(bounds[1], bounds[3])
            
            offset = 0.05
            poly = Polygon((
                (lon - offset, lat - offset),
                (lon + offset, lat - offset),
                (lon + offset, lat + offset),
                (lon - offset, lat + offset),
                (lon - offset, lat - offset),
            ))
            
            commune, created = Commune.objects.get_or_create(
                code=f"C{commune_id}",
                defaults={
                    'name': commune_name,
                    'department': dept,
                    'centroid': Point(lon, lat),
                    'geometry': MultiPolygon(poly),
                    'population': random.randint(10000, 100000),
                    'area_km2': random.uniform(50, 500),
                }
            )
            if created:
                count += 1
                if count % 20 == 0:
                    print(f"  ✓ {count} communes...")
    
    print(f"✅ {Commune.objects.count()} communes")

def create_facilities():
    """Crée des structures de santé et d'éducation"""
    print("\n🏥 Création des structures de santé...")
    
    communes = list(Commune.objects.all())
    if not communes:
        print("  ⚠ Aucune commune disponible, création impossible")
        return
    
    for i in range(50):
        commune = random.choice(communes)
        bounds = commune.geometry.extent
        lon = random.uniform(bounds[0], bounds[2])
        lat = random.uniform(bounds[1], bounds[3])
        
        facility, created = HealthFacility.objects.get_or_create(
            name=f"Structure Santé {commune.name} {i+1}",
            defaults={
                'code': f"HS-{commune.code}-{i+1:03d}",
                'facility_type': random.choice(['hospital', 'health_center', 'health_post', 'clinic']),
                'commune': commune,
                'location': Point(lon, lat),
                'address': f"{commune.name}",
                'bed_capacity': random.randint(20, 200),
                'is_active': True,
            }
        )
        if created:
            pass  # Facility created successfully
    
    print(f"✅ {HealthFacility.objects.count()} structures de santé")
    
    print("\n🎓 Création des structures d'éducation...")
    for i in range(80):
        commune = random.choice(communes)
        bounds = commune.geometry.extent
        lon = random.uniform(bounds[0], bounds[2])
        lat = random.uniform(bounds[1], bounds[3])
        
        facility, created = EducationFacility.objects.get_or_create(
            name=f"École {commune.name} {i+1}",
            defaults={
                'code': f"ED-{commune.code}-{i+1:03d}",
                'facility_type': random.choice(['elementary', 'middle_school', 'high_school', 'university']),
                'commune': commune,
                'location': Point(lon, lat),
                'address': f"{commune.name}",
                'student_capacity': random.randint(200, 1000),
                'is_active': True,
            }
        )
        if created:
            pass  # Facility created successfully
    
    print(f"✅ {EducationFacility.objects.count()} structures d'éducation")
    
    print(f"✅ {EducationFacility.objects.count()} structures d'éducation")

def create_indicators():
    """Crée les indicateurs et leurs valeurs"""
    print("\n📊 Création des indicateurs...")
    
    indicators_data = [
        {'name': 'Taux de vaccination DTC3', 'sector': 'health', 'unit': '%', 'category': 'vaccination', 'code': 'HLTH-VACC-DTC3'},
        {'name': 'Mortalité maternelle', 'sector': 'health', 'unit': 'pour 100 000', 'category': 'maternal_health', 'code': 'HLTH-MAT-MORT'},
        {'name': 'Prévalence du paludisme', 'sector': 'health', 'unit': '%', 'category': 'disease', 'code': 'HLTH-PALU-PREV'},
        {'name': 'Taux de scolarisation primaire', 'sector': 'education', 'unit': '%', 'category': 'enrollment', 'code': 'EDUC-SCOL-PRI'},
        {'name': 'Ratio élèves/enseignant', 'sector': 'education', 'unit': 'ratio', 'category': 'quality', 'code': 'EDUC-RATIO-EE'},
        {'name': 'Taux de réussite au BFEM', 'sector': 'education', 'unit': '%', 'category': 'performance', 'code': 'EDUC-REUS-BFEM'},
    ]
    
    for ind_data in indicators_data:
        ind, created = Indicator.objects.get_or_create(
            name=ind_data['name'],
            defaults={
                'code': ind_data['code'],
                'sector': ind_data['sector'],
                'category': ind_data['category'],
                'unit': ind_data['unit'],
                'description': f"Indicateur: {ind_data['name']}",
                'is_active': True,
            }
        )
        if created:
            print(f"  ✓ {ind.name}")
    
    print(f"✅ {Indicator.objects.count()} indicateurs")
    
    print("\n📈 Création des valeurs d'indicateurs...")
    indicators = Indicator.objects.all()
    regions = list(Region.objects.all())
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    
    count = 0
    for indicator in indicators:
        for region in regions:
            for year in years:
                if '%' in indicator.unit:
                    value = random.uniform(60, 95) + (year - 2020) * random.uniform(0.5, 2.0)
                    value = min(100, max(0, value))
                elif 'mortalité' in indicator.name.lower():
                    value = random.uniform(200, 400) - (year - 2020) * random.uniform(5, 15)
                    value = max(100, value)
                elif 'ratio' in indicator.unit.lower():
                    value = random.uniform(25, 45)
                else:
                    value = random.uniform(50, 100)
                
                IndicatorValue.objects.get_or_create(
                    indicator=indicator,
                    region=region,
                    year=year,
                    defaults={
                        'value': Decimal(str(round(value, 2))),
                        'status': 'validated',
                        'source': 'Ministère',
                    }
                )
                count += 1
    
    print(f"✅ {count} valeurs")

def create_users_and_alerts():
    """Crée les utilisateurs et alertes"""
    print("\n👥 Création des utilisateurs...")
    
    users_data = [
        {'email': 'actor@fati.gov', 'first_name': 'Dr. Aminata', 'last_name': 'Diop', 'role': 'local_manager'},
        {'email': 'population@fati.gov', 'first_name': 'Prof. Mamadou', 'last_name': 'Sall', 'role': 'annonceur'},
    ]
    
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'role': user_data['role'],
                'status': 'active',
                'is_active': True,
            }
        )
        if created:
            user.set_password('password')
            user.save()
            print(f"  ✓ {user.email}")
    
    print(f"✅ {User.objects.count()} utilisateurs")
    
    print("\n⚠️  Création des alertes...")
    regions = list(Region.objects.all())
    indicators = list(Indicator.objects.all())
    
    for i in range(15):
        region = random.choice(regions)
        indicator = random.choice(indicators)
        
        Alert.objects.create(
            title=f"Alerte {indicator.sector} - {region.name}",
            message=f"Attention concernant {indicator.name}",
            severity=random.choice(['critical', 'high', 'medium']),
            sector=indicator.sector,
            region=region,
            indicator=indicator,
            type=random.choice(['threshold', 'trend', 'anomaly']),
            is_read=random.choice([False, False, True]),
        )
    
    print(f"✅ {Alert.objects.count()} alertes")

def main():
    print("🚀 Peuplement de la base de données FATI")
    print("=" * 60)
    
    try:
        print(f"\n✓ {Region.objects.count()} régions déjà importées")
        populate_departments_from_csv()
        populate_communes_from_csv()
        create_facilities()
        create_indicators()
        create_users_and_alerts()
        
        print("\n" + "=" * 60)
        print("✅ Peuplement terminé!")
        print(f"\n📊 Résumé:")
        print(f"  - Régions: {Region.objects.count()}")
        print(f"  - Départements: {Department.objects.count()}")
        print(f"  - Communes: {Commune.objects.count()}")
        print(f"  - Structures de santé: {HealthFacility.objects.count()}")
        print(f"  - Structures d'éducation: {EducationFacility.objects.count()}")
        print(f"  - Indicateurs: {Indicator.objects.count()}")
        print(f"  - Valeurs: {IndicatorValue.objects.count()}")
        print(f"  - Utilisateurs: {User.objects.count()}")
        print(f"  - Alertes: {Alert.objects.count()}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
