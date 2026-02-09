from django.test import TestCase
from django.contrib.gis.geos import Point
from .models import EducationFacility, HealthFacility
from .serializers import EducationFacilitySerializer
from fati_geography.models import Commune, Department, Region

class FacilitySerializerTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.region = Region.objects.create(name="Test Region", code="REG")
        self.department = Department.objects.create(name="Test Dept", code="DEP", region=self.region)
        self.commune = Commune.objects.create(name="Test Commune", code="COM", department=self.department)

    def test_education_facility_creation_with_geojson(self):
        data = {
            'code': 'TEST_EDU_001',
            'name': 'Test School',
            'facility_type': 'primary',
            'level': 'basic',
            'commune_name': self.commune.name, # Serializer uses source='commune.name' read_only=True
            # Wait, serializer expects 'commune' ID for writing?
            # Looking at serializer: 'commune' is in fields, but not defined explicitly as writeable?
            # Default ModelSerializer behavior: ForeignKey is PrimaryKeyRelatedField.
            'commune': self.commune.id,
            'location': {
                'type': 'Point',
                'coordinates': [-17.444, 14.692]
            }
        }
        
        serializer = EducationFacilitySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        facility = serializer.save()
        
        self.assertIsInstance(facility, EducationFacility)
        self.assertIsInstance(facility.location, Point)
        self.assertEqual(facility.location.x, -17.444)
        self.assertEqual(facility.location.y, 14.692)

    def test_health_facility_creation_with_geojson(self):
        # Similar test for HealthFacility to be thorough
        data = {
            'code': 'TEST_HEALTH_001',
            'name': 'Test Clinic',
            'facility_type': 'clinic',
            'category': 'reference', # optional
            'commune': self.commune.id,
            'location': {
                'type': 'Point',
                'coordinates': [-17.500, 14.700]
            }
        }
        
        from .serializers import HealthFacilitySerializer
        serializer = HealthFacilitySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        facility = serializer.save()
        
        self.assertIsInstance(facility, HealthFacility)
        self.assertIsInstance(facility.location, Point)
        self.assertEqual(facility.location.x, -17.500)
        self.assertEqual(facility.location.y, 14.700)
