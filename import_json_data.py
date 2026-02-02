import os
import json
import django
import sys
import re

def clean_value(val):
    if val is None or val == "" or val == " ": return None
    if isinstance(val, (int, float)): return float(val)
    val = val.replace('\xa0', '').replace(' ', '').replace(',', '.')
    try:
        if val.count('.') > 1:
             parts = val.split('.')
             val = "".join(parts[:-1]) + "." + parts[-1]
        return float(val)
    except ValueError:
        return None

def main():
    import sys
    from types import ModuleType
    if 'dj_database_url' not in sys.modules:
        m = ModuleType('dj_database_url'); m.config = lambda **k: {'ENGINE': 'django.db.backends.postgresql'}; m.parse = lambda u, **k: {'ENGINE': 'django.db.backends.postgresql'}; sys.modules['dj_database_url'] = m
    if 'dotenv' not in sys.modules:
        m = ModuleType('dotenv'); m.load_dotenv = lambda **k: None; sys.modules['dotenv'] = m

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fati_backend.settings')
    from fati_backend import settings
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': 'neondb',
            'USER': 'neondb_owner',
            'PASSWORD': 'npg_zKuQSEG0Z9lr',
            'HOST': 'ep-young-shape-aheybnnb-pooler.c-3.us-east-1.aws.neon.tech',
            'PORT': '5432',
            'OPTIONS': {'sslmode': 'require'},
        }
    }
    
    django.setup()

    from fati_geography.models import Region
    from fati_indicators.models import Indicator, IndicatorValue

    sante_path = '/home/cardan/Pictures/pro_suivi/sante.json'
    edu_path = '/home/cardan/Pictures/pro_suivi/education.json'

    regions_map = {r.name.upper(): r for r in Region.objects.all()}
    
    def get_region(name):
        if not name: return None
        n = name.strip().upper()
        if n == 'SENEGAL': return None
        return regions_map.get(n)

    def process_sante():
        print("--- Importing Health data (Bulk) ---")
        with open(sante_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        all_values = []
        for cat_name, sheets in data.items():
            print(f" Category: {cat_name}")
            for sheet_name, rows in sheets.items():
                current_region = None
                for row in rows:
                    if row.get('Période'): current_region = get_region(row.get('Période'))
                    indicator_name = row.get('Unnamed: 1')
                    if not indicator_name or "indicateurs" in indicator_name.lower(): continue

                    indicator_name = indicator_name.replace('(*)', '').strip()
                    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', indicator_name.upper())
                    code = f"{cat_name[:4].upper()}_{clean_name[:40]}"
                    
                    indicator, _ = Indicator.objects.get_or_create(
                        name=indicator_name,
                        defaults={
                            'code': code[:50],
                            'sector': Indicator.Sector.HEALTH,
                            'category': Indicator.Category.RESOURCES if "Budget" in indicator_name else Indicator.Category.ACCESS,
                        }
                    )

                    for key, val in row.items():
                        if re.match(r'^\d{4}$', key):
                            cv = clean_value(val)
                            if cv is not None:
                                all_values.append(IndicatorValue(
                                    indicator=indicator, region=current_region, year=int(key),
                                    value=cv, status=IndicatorValue.Status.VALIDATED, source='sante.json'
                                ))
        
        print(f"  Inserting {len(all_values)} health values...")
        IndicatorValue.objects.bulk_create(all_values, batch_size=500, ignore_conflicts=True)
        print("DONE Health.")

    def process_education():
        print("\n--- Importing Education data (Bulk) ---")
        with open(edu_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        all_values = []
        for cat_name, sheets in data.items():
            print(f" Category: {cat_name}")
            for sheet_name, rows in sheets.items():
                years = {}
                indicator = None
                for row in rows:
                    if not row: continue
                    # Get the first key and its value
                    first_key = list(row.keys())[0]
                    first_val = str(row[first_key] or '')

                    # Ligne d'entête avec les années
                    if 'Période' in first_val:
                        years = {k: int(str(v).strip()) for k, v in row.items() if v and re.match(r'^\d{4}', str(v).strip())}
                        continue

                    # Ligne avec info indicateur
                    if 'Fréquence:' in first_val:
                        info = first_val.split(',')
                        indicator_name = "Inconnu"
                        unit = ""
                        for i in info:
                            if 'Indicateurs' in i and ':' in i: indicator_name = i.split(':')[1].strip()
                            elif 'Unité' in i and ':' in i: unit = i.split(':')[1].strip()
                        
                        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', indicator_name.upper())
                        code = f"EDU_{clean_name[:40]}"
                        indicator, _ = Indicator.objects.get_or_create(
                            name=indicator_name,
                            defaults={'code': code[:50], 'sector': Indicator.Sector.EDUCATION, 'category': Indicator.Category.INFRASTRUCTURE, 'unit': unit}
                        )
                        continue

                    region_name = first_val.strip()
                    if region_name and years and indicator:
                        region = get_region(region_name)
                        for col_key, year in years.items():
                            cv = clean_value(row.get(col_key))
                            if cv is not None:
                                all_values.append(IndicatorValue(
                                    indicator=indicator, region=region, year=year,
                                    value=cv, status=IndicatorValue.Status.VALIDATED, source='education.json'
                                ))
        
        print(f"  Inserting {len(all_values)} education values...")
        # Use batches to avoid memory issues and giant SQL statements
        IndicatorValue.objects.bulk_create(all_values, batch_size=500, ignore_conflicts=True)
        print("DONE Education.")

    process_sante()
    process_education()

if __name__ == "__main__":
    main()
