"""
Commande pour importer les données géographiques à partir des fichiers Shapefiles de façon intelligente
"""
import os
import json
from django.core.management.base import BaseCommand
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import MultiPolygon, Polygon, GEOSGeometry
from fati_geography.models import Region, Department, Commune

class Command(BaseCommand):
    help = 'Importe les données géographiques du Sénégal'

    def handle(self, *args, **options):
        shp_dir = os.path.join(os.getcwd(), 'SEN_adm')

        # 1. Nettoyage
        self.stdout.write('Nettoyage des anciennes données...')
        Commune.objects.all().delete()
        Department.objects.all().delete()
        Region.objects.all().delete()

        # 2. Importation des Régions (ADM1)
        self.stdout.write('Importation des Régions (ADM1)...')
        shp_reg = os.path.join(shp_dir, 'SEN_adm1.shp')
        
        mapping_reg = {
            'name': 'NAME_1',
            'code': 'NAME_1',
            'geometry': 'POLYGON',
        }
        
        lm_reg = LayerMapping(Region, shp_reg, mapping_reg, transform=False)
        lm_reg.save(strict=True, verbose=False)
        
        for r in Region.objects.all():
            if r.geometry and isinstance(r.geometry, Polygon):
                r.geometry = MultiPolygon(r.geometry)
            r.save()
            
        self.stdout.write(self.style.SUCCESS(f'  ✓ {Region.objects.count()} régions importées.'))

        # 3. Importation des Départements (ADM2)
        self.stdout.write('Importation des Départements (ADM2)...')
        shp_dept = os.path.join(shp_dir, 'SEN_adm2.shp')
        
        import shapefile 
        sf = shapefile.Reader(shp_dept)
        for sr in sf.shapeRecords():
            name = sr.record['NAME_2']
            # Utiliser geo_interface + json.dumps pour éviter les pointeurs invalides
            geom_data = sr.shape.__geo_interface__
            geos_geom = GEOSGeometry(json.dumps(geom_data))
            
            if isinstance(geos_geom, Polygon):
                geos_geom = MultiPolygon(geos_geom)
            
            parent_region = Region.objects.filter(geometry__contains=geos_geom.centroid).first()
            if not parent_region:
                parent_region = Region.objects.filter(geometry__intersects=geos_geom).first()

            Department.objects.create(
                name=name,
                code=f"DEP_{sr.record.oid}",
                geometry=geos_geom,
                region=parent_region or Region.objects.first()
            )

        self.stdout.write(self.style.SUCCESS(f'  ✓ {Department.objects.count()} départements importés.'))

        # 4. Importation des Communes (ADM4)
        self.stdout.write('Importation des Communes (ADM4)...')
        shp_com = os.path.join(shp_dir, 'SEN_adm4.shp')
        
        sf_com = shapefile.Reader(shp_com)
        for sr in sf_com.shapeRecords():
            name = sr.record['NAME_4']
            geom_data = sr.shape.__geo_interface__
            geos_geom = GEOSGeometry(json.dumps(geom_data))
            
            if isinstance(geos_geom, Polygon):
                geos_geom = MultiPolygon(geos_geom)
            
            parent_dept = Department.objects.filter(geometry__contains=geos_geom.centroid).first()
            if not parent_dept:
                parent_dept = Department.objects.filter(geometry__intersects=geos_geom).first()
            
            Commune.objects.create(
                name=name,
                code=f"COM_{sr.record.oid}",
                geometry=geos_geom,
                department=parent_dept or Department.objects.first()
            )

        self.stdout.write(self.style.SUCCESS(f'  ✓ {Commune.objects.count()} communes importées.'))
        self.stdout.write(self.style.SUCCESS('Initialisation géographique terminée avec succès !'))
