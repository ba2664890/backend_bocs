"""
Commande de peuplement global FATI.

Objectif:
- importer d'abord les donnees depuis les JSON sante/education;
- si les JSON sont absents/incomplets, generer des donnees synthetiques.
"""
import csv
import json
import random
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from fati_accounts.models import User
from fati_facilities.models import EducationFacility, HealthFacility, Staff
from fati_geography.models import Commune, Department, Region
from fati_indicators.models import Indicator, IndicatorValue
from fati_workflows.models import Alert


class Command(BaseCommand):
    help = "Peuplement FATI: import JSON puis fallback en donnees generees."

    def add_arguments(self, parser):
        parser.add_argument(
            "--health-json",
            default="/home/cardan/Pictures/pro_suivi/sante.json",
            help="Chemin du fichier JSON sante",
        )
        parser.add_argument(
            "--education-json",
            default="/home/cardan/Pictures/pro_suivi/education.json",
            help="Chemin du fichier JSON education",
        )
        parser.add_argument(
            "--only-json",
            action="store_true",
            help="Importer uniquement les JSON sans generation fallback",
        )
        parser.add_argument(
            "--only-generate",
            action="store_true",
            help="Ignorer les JSON et generer uniquement des donnees synthetiques",
        )
        parser.add_argument(
            "--min-health-values",
            type=int,
            default=250,
            help="Minimum de valeurs sante attendu apres import JSON",
        )
        parser.add_argument(
            "--min-education-values",
            type=int,
            default=250,
            help="Minimum de valeurs education attendu apres import JSON",
        )
        parser.add_argument(
            "--min-health-facilities",
            type=int,
            default=60,
            help="Nombre minimal de structures de sante",
        )
        parser.add_argument(
            "--min-education-facilities",
            type=int,
            default=80,
            help="Nombre minimal d'etablissements d'education",
        )
        parser.add_argument(
            "--min-alerts",
            type=int,
            default=20,
            help="Nombre minimal d'alertes a generer",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Graine aleatoire pour generation synthetique",
        )

    def handle(self, *args, **options):
        if options["only_json"] and options["only_generate"]:
            raise CommandError("Utiliser soit --only-json soit --only-generate, pas les deux.")

        self.rng = random.Random(options["seed"])
        self.stdout.write(self.style.NOTICE("Demarrage du peuplement FATI..."))

        self.sync_geography_from_csv()
        self._build_geo_lookup()

        health_values_from_json = 0
        education_values_from_json = 0

        if not options["only_generate"]:
            health_values_from_json = self.import_health_json(options["health_json"])
            education_values_from_json = self.import_education_json(options["education_json"])

        if not options["only_json"]:
            if health_values_from_json < options["min_health_values"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"Import JSON sante insuffisant ({health_values_from_json} valeurs). "
                        "Generation fallback sante..."
                    )
                )
                self.generate_synthetic_values(sector="health")

            if education_values_from_json < options["min_education_values"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"Import JSON education insuffisant ({education_values_from_json} valeurs). "
                        "Generation fallback education..."
                    )
                )
                self.generate_synthetic_values(sector="education")

        self.ensure_facilities(
            min_health=options["min_health_facilities"],
            min_education=options["min_education_facilities"],
        )
        self.ensure_users()
        self.ensure_alerts(min_alerts=options["min_alerts"])

        self.stdout.write(self.style.SUCCESS("\nPeuplement termine."))
        self.print_summary()

    # ------------------------------------------------------------------
    # Geography
    # ------------------------------------------------------------------
    def sync_geography_from_csv(self):
        """Synchronise regions/departements/communes a partir des CSV locaux."""
        base = Path.cwd() / "SEN_adm"
        regions_csv = base / "SEN_adm1.csv"
        departments_csv = base / "SEN_adm2.csv"
        communes_csv = base / "SEN_adm3.csv"

        if not regions_csv.exists() or not departments_csv.exists() or not communes_csv.exists():
            self.stdout.write(
                self.style.WARNING(
                    "CSV geographiques absents. Synchronisation geographique ignoree."
                )
            )
            return

        created_regions = 0
        created_departments = 0
        created_communes = 0

        # Regions
        region_rows = self._read_csv_rows(regions_csv, delimiter=";")
        for row in region_rows:
            name = (row.get("NAME_1") or "").strip()
            if not name:
                continue

            pop = self._parse_int(row.get("Pop"))
            region = Region.objects.filter(name__iexact=name).first()
            if region:
                changed = False
                if pop and region.population != pop:
                    region.population = pop
                    changed = True
                if changed:
                    region.save(update_fields=["population"])
                continue

            code = self._unique_geo_code(Region, f"R{int(row.get('ID_region') or 0):02d}")
            Region.objects.create(code=code, name=name, population=pop)
            created_regions += 1

        # Departments
        department_rows = self._read_csv_rows(departments_csv)
        for row in department_rows:
            region_name = (row.get("NAME_1") or "").strip()
            dept_name = (row.get("NAME_2") or "").strip()
            if not region_name or not dept_name:
                continue

            region = Region.objects.filter(name__iexact=region_name).first()
            if not region:
                continue

            department = Department.objects.filter(
                name__iexact=dept_name,
                region=region,
            ).first()
            if department:
                continue

            code = self._unique_geo_code(Department, f"D{int(row.get('ID_2') or 0):03d}")
            Department.objects.create(code=code, name=dept_name, region=region)
            created_departments += 1

        # Communes
        commune_rows = self._read_csv_rows(communes_csv)
        for row in commune_rows:
            dept_name = (row.get("NAME_2") or "").strip()
            commune_name = (row.get("NAME_3") or "").strip()
            if not dept_name or not commune_name:
                continue

            department = Department.objects.filter(name__iexact=dept_name).first()
            if not department:
                continue

            commune = Commune.objects.filter(
                name__iexact=commune_name,
                department=department,
            ).first()
            if commune:
                continue

            code = self._unique_geo_code(Commune, f"C{int(row.get('ID_3') or 0):04d}")
            Commune.objects.create(code=code, name=commune_name, department=department)
            created_communes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Geographie synchronisee (crees: regions={created_regions}, "
                f"departements={created_departments}, communes={created_communes})."
            )
        )

    def _read_csv_rows(self, path: Path, delimiter: Optional[str] = None):
        encodings = ("utf-8-sig", "utf-8", "latin-1")
        last_error = None

        for encoding in encodings:
            try:
                with path.open("r", encoding=encoding, newline="") as handle:
                    reader = csv.DictReader(handle, delimiter=delimiter) if delimiter else csv.DictReader(handle)
                    return list(reader)
            except UnicodeDecodeError as exc:
                last_error = exc
                continue

        raise CommandError(f"Impossible de lire le CSV {path} (encodage): {last_error}")

    def _unique_geo_code(self, model_cls, base_code: str) -> str:
        code = base_code
        idx = 1
        while model_cls.objects.filter(code=code).exists():
            code = f"{base_code}_{idx}"
            idx += 1
        return code

    def _build_geo_lookup(self):
        self.region_by_name: Dict[str, Region] = {}
        self.department_by_name: Dict[str, Department] = {}

        for region in Region.objects.all():
            self.region_by_name[self._normalize(region.name)] = region

        for department in Department.objects.select_related("region").all():
            self.department_by_name[self._normalize(department.name)] = department

        # Alias frequents pour les JSON.
        aliases = {
            "ST LOUIS": "SAINT LOUIS",
            "THIES": "THIES",
            "KEDOUGOU": "KEDOUGOU",
            "ZIGUINCHOR": "ZIGUINCHOR",
            "SENEGAL": "SENEGAL",
        }
        for src, dst in aliases.items():
            src_norm = self._normalize(src)
            dst_norm = self._normalize(dst)
            if dst_norm in self.region_by_name:
                self.region_by_name[src_norm] = self.region_by_name[dst_norm]

    def _resolve_geo(self, raw_label: Optional[str]) -> Tuple[Optional[Region], Optional[Department], Optional[Commune]]:
        if not raw_label:
            return None, None, None

        label = self._normalize(raw_label)
        if not label or label in {"SENEGAL", "TOTAL", "NATIONAL"}:
            return None, None, None

        department = self.department_by_name.get(label)
        if department:
            return None, department, None

        region = self.region_by_name.get(label)
        if region:
            return region, None, None

        # Tentative fuzzy simple.
        for key, dep in self.department_by_name.items():
            if key in label or label in key:
                return None, dep, None
        for key, reg in self.region_by_name.items():
            if key in label or label in key:
                return reg, None, None

        return None, None, None

    # ------------------------------------------------------------------
    # JSON import
    # ------------------------------------------------------------------
    def import_health_json(self, json_path: str) -> int:
        path = Path(json_path)
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"JSON sante introuvable: {path}"))
            return 0

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Erreur de lecture JSON sante: {exc}"))
            return 0

        imported_values = 0
        created_indicators = 0

        for group_key, sheets in data.items():
            if not isinstance(sheets, dict):
                continue

            for sheet_name, rows in sheets.items():
                if not isinstance(rows, list):
                    continue

                current_geo_label = None
                for row in rows:
                    if not isinstance(row, dict):
                        continue

                    period_label = row.get("Période")
                    if isinstance(period_label, str) and period_label.strip():
                        normalized = self._normalize(period_label)
                        if normalized not in {"", "PERIODE", "DECOUPAGE ADMINISTRATIF"}:
                            current_geo_label = period_label.strip()

                    indicator_raw = row.get("Unnamed: 1") or row.get("Unnamed: 2") or ""
                    indicator_name = self._clean_indicator_name(indicator_raw)
                    if not indicator_name or self._looks_like_header(indicator_name):
                        continue

                    year_values = self._extract_year_values(row)
                    if not year_values:
                        continue

                    category = self._guess_category(
                        sector="health",
                        group_key=group_key,
                        sheet_name=sheet_name,
                        indicator_name=indicator_name,
                    )
                    indicator_type = self._guess_type(unit="", indicator_name=indicator_name)
                    indicator, created = self._get_or_create_indicator(
                        sector=Indicator.Sector.HEALTH,
                        category=category,
                        indicator_type=indicator_type,
                        name=indicator_name,
                        group_key=group_key,
                        sheet_name=sheet_name,
                        unit="",
                        description=f"Import JSON sante / {group_key} / {sheet_name}",
                    )
                    if created:
                        created_indicators += 1

                    region, department, commune = self._resolve_geo(current_geo_label)
                    for year, value in year_values:
                        self._upsert_indicator_value(
                            indicator=indicator,
                            year=year,
                            value=value,
                            region=region,
                            department=department,
                            commune=commune,
                            source=f"json:{path.name}",
                        )
                        imported_values += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sante JSON importe: {imported_values} valeurs, {created_indicators} indicateurs crees."
            )
        )
        return imported_values

    def import_education_json(self, json_path: str) -> int:
        path = Path(json_path)
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"JSON education introuvable: {path}"))
            return 0

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Erreur de lecture JSON education: {exc}"))
            return 0

        imported_values = 0
        created_indicators = 0

        for group_key, sheets in data.items():
            if not isinstance(sheets, dict):
                continue

            for sheet_name, rows in sheets.items():
                if not isinstance(rows, list):
                    continue

                year_map: Dict[str, int] = {}
                current_indicator = None

                for row in rows:
                    if not isinstance(row, dict) or not row:
                        continue

                    first_col = next(iter(row.keys()))
                    first_value = str(row.get(first_col) or "").strip()
                    if not first_value:
                        continue

                    normalized_first_value = self._normalize(first_value)

                    if "PERIODE" in normalized_first_value:
                        year_map = self._extract_year_map_from_education_row(row)
                        continue

                    if "FREQUENCE" in normalized_first_value and "INDICATEUR" in normalized_first_value:
                        indicator_name, unit = self._parse_education_indicator_line(first_value)
                        indicator_name = self._clean_indicator_name(indicator_name)
                        if not indicator_name:
                            continue

                        category = self._guess_category(
                            sector="education",
                            group_key=group_key,
                            sheet_name=sheet_name,
                            indicator_name=indicator_name,
                        )
                        indicator_type = self._guess_type(unit=unit, indicator_name=indicator_name)
                        current_indicator, created = self._get_or_create_indicator(
                            sector=Indicator.Sector.EDUCATION,
                            category=category,
                            indicator_type=indicator_type,
                            name=indicator_name,
                            group_key=group_key,
                            sheet_name=sheet_name,
                            unit=unit,
                            description=f"Import JSON education / {group_key} / {sheet_name}",
                        )
                        if created:
                            created_indicators += 1
                        continue

                    if not current_indicator or not year_map:
                        continue

                    if self._is_education_meta_row(normalized_first_value):
                        continue

                    region, department, commune = self._resolve_geo(first_value)
                    for column_key, year in year_map.items():
                        value = self._parse_number(row.get(column_key))
                        if value is None:
                            continue

                        self._upsert_indicator_value(
                            indicator=current_indicator,
                            year=year,
                            value=value,
                            region=region,
                            department=department,
                            commune=commune,
                            source=f"json:{path.name}",
                        )
                        imported_values += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Education JSON importe: {imported_values} valeurs, {created_indicators} indicateurs crees."
            )
        )
        return imported_values

    # ------------------------------------------------------------------
    # Synthetic generation fallback
    # ------------------------------------------------------------------
    def generate_synthetic_values(self, sector: str):
        years = list(range(max(2018, datetime.now().year - 6), datetime.now().year + 1))
        regions = list(Region.objects.all())
        if not regions:
            regions = [None]

        templates = self._synthetic_templates(sector)

        generated_values = 0
        created_indicators = 0

        for tpl in templates:
            indicator, created = self._get_or_create_indicator(
                sector=tpl["sector"],
                category=tpl["category"],
                indicator_type=tpl["type"],
                name=tpl["name"],
                group_key="generated",
                sheet_name=sector,
                unit=tpl["unit"],
                description="Donnee synthetique generee automatiquement",
                target_value=tpl.get("target"),
                alert_threshold=tpl.get("alert_threshold"),
            )
            if created:
                created_indicators += 1

            for region in regions:
                base = self.rng.uniform(tpl["min"], tpl["max"])
                trend = self.rng.uniform(*tpl["trend"])

                for idx, year in enumerate(years):
                    noise = self.rng.uniform(-tpl["noise"], tpl["noise"])
                    value = base + (idx * trend) + noise
                    if tpl["type"] == Indicator.Type.PERCENTAGE:
                        value = max(0.0, min(100.0, value))
                    elif tpl["type"] == Indicator.Type.COUNT:
                        value = max(0.0, round(value))
                    else:
                        value = max(0.0, value)

                    self._upsert_indicator_value(
                        indicator=indicator,
                        year=year,
                        value=float(round(value, 2)),
                        region=region,
                        department=None,
                        commune=None,
                        source="generated",
                    )
                    generated_values += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Generation {sector}: {generated_values} valeurs, {created_indicators} indicateurs crees."
            )
        )

    def _synthetic_templates(self, sector: str):
        if sector == "health":
            return [
                {
                    "name": "Taux de couverture vaccinale",
                    "sector": Indicator.Sector.HEALTH,
                    "category": Indicator.Category.ACCESS,
                    "type": Indicator.Type.PERCENTAGE,
                    "unit": "%",
                    "target": 95.0,
                    "alert_threshold": 70.0,
                    "min": 60.0,
                    "max": 88.0,
                    "trend": (0.5, 2.5),
                    "noise": 2.0,
                },
                {
                    "name": "Taux de mortalite maternelle",
                    "sector": Indicator.Sector.HEALTH,
                    "category": Indicator.Category.OUTCOMES,
                    "type": Indicator.Type.NUMBER,
                    "unit": "/100000",
                    "target": 120.0,
                    "alert_threshold": 220.0,
                    "min": 180.0,
                    "max": 280.0,
                    "trend": (-8.0, -2.0),
                    "noise": 6.0,
                },
                {
                    "name": "Nombre de structures de sante fonctionnelles",
                    "sector": Indicator.Sector.HEALTH,
                    "category": Indicator.Category.INFRASTRUCTURE,
                    "type": Indicator.Type.COUNT,
                    "unit": "unites",
                    "target": 500.0,
                    "alert_threshold": 250.0,
                    "min": 140.0,
                    "max": 220.0,
                    "trend": (2.0, 8.0),
                    "noise": 4.0,
                },
                {
                    "name": "Disponibilite du personnel soignant",
                    "sector": Indicator.Sector.HEALTH,
                    "category": Indicator.Category.PERSONNEL,
                    "type": Indicator.Type.PERCENTAGE,
                    "unit": "%",
                    "target": 90.0,
                    "alert_threshold": 65.0,
                    "min": 55.0,
                    "max": 82.0,
                    "trend": (0.4, 1.5),
                    "noise": 2.5,
                },
            ]

        return [
            {
                "name": "Taux brut de scolarisation",
                "sector": Indicator.Sector.EDUCATION,
                "category": Indicator.Category.ACCESS,
                "type": Indicator.Type.PERCENTAGE,
                "unit": "%",
                "target": 100.0,
                "alert_threshold": 80.0,
                "min": 70.0,
                "max": 94.0,
                "trend": (0.4, 1.8),
                "noise": 2.0,
            },
            {
                "name": "Taux de reussite aux examens nationaux",
                "sector": Indicator.Sector.EDUCATION,
                "category": Indicator.Category.OUTCOMES,
                "type": Indicator.Type.PERCENTAGE,
                "unit": "%",
                "target": 80.0,
                "alert_threshold": 55.0,
                "min": 45.0,
                "max": 74.0,
                "trend": (0.5, 2.0),
                "noise": 3.0,
            },
            {
                "name": "Nombre d'etablissements scolaires",
                "sector": Indicator.Sector.EDUCATION,
                "category": Indicator.Category.INFRASTRUCTURE,
                "type": Indicator.Type.COUNT,
                "unit": "unites",
                "target": 1500.0,
                "alert_threshold": 700.0,
                "min": 350.0,
                "max": 700.0,
                "trend": (5.0, 16.0),
                "noise": 8.0,
            },
            {
                "name": "Ratio eleves par enseignant",
                "sector": Indicator.Sector.EDUCATION,
                "category": Indicator.Category.QUALITY,
                "type": Indicator.Type.RATIO,
                "unit": "ratio",
                "target": 35.0,
                "alert_threshold": 55.0,
                "min": 48.0,
                "max": 62.0,
                "trend": (-1.8, -0.2),
                "noise": 1.6,
            },
        ]

    # ------------------------------------------------------------------
    # Facilities, users, alerts
    # ------------------------------------------------------------------
    def ensure_facilities(self, min_health: int, min_education: int):
        communes = list(Commune.objects.all())
        if not communes:
            self.stdout.write(self.style.WARNING("Aucune commune: generation de structures ignoree."))
            return

        health_missing = max(0, min_health - HealthFacility.objects.count())
        education_missing = max(0, min_education - EducationFacility.objects.count())

        health_types = [choice[0] for choice in HealthFacility.Type.choices]
        education_types = [choice[0] for choice in EducationFacility.Type.choices]
        education_levels = [choice[0] for choice in EducationFacility.Level.choices]

        for _ in range(health_missing):
            commune = self.rng.choice(communes)
            code = self._next_code(HealthFacility, "HS")
            facility = HealthFacility.objects.create(
                code=code,
                name=f"Structure Sante {commune.name} {code.split('-')[-1]}",
                facility_type=self.rng.choice(health_types),
                commune=commune,
                address=commune.name,
                bed_capacity=self.rng.randint(20, 220),
                is_active=True,
            )
            total_staff = self.rng.randint(2, 20)
            Staff.objects.create(
                health_facility=facility,
                category=Staff.Category.DOCTOR,
                total=total_staff,
                filled=self.rng.randint(1, total_staff),
            )

        for _ in range(education_missing):
            commune = self.rng.choice(communes)
            code = self._next_code(EducationFacility, "ED")
            facility = EducationFacility.objects.create(
                code=code,
                name=f"Etablissement {commune.name} {code.split('-')[-1]}",
                facility_type=self.rng.choice(education_types),
                level=self.rng.choice(education_levels),
                commune=commune,
                address=commune.name,
                student_capacity=self.rng.randint(120, 1800),
                is_active=True,
            )
            total_staff = self.rng.randint(8, 120)
            Staff.objects.create(
                education_facility=facility,
                category=Staff.Category.OTHER,
                total=total_staff,
                filled=max(1, total_staff - self.rng.randint(0, 12)),
            )

        if health_missing or education_missing:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Structures completees: +{health_missing} sante, +{education_missing} education."
                )
            )

    def ensure_users(self):
        users_data = [
            {
                "email": "admin@fati.local",
                "first_name": "Admin",
                "last_name": "FATI",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "institution@fati.local",
                "first_name": "Decideur",
                "last_name": "Institution",
                "role": User.Role.INSTITUTION,
            },
            {
                "email": "local@fati.local",
                "first_name": "Agent",
                "last_name": "Local",
                "role": User.Role.LOCAL_MANAGER,
            },
            {
                "email": "public@fati.local",
                "first_name": "Profil",
                "last_name": "Public",
                "role": User.Role.ANNONCEUR,
            },
            {
                "email": "viewer@fati.local",
                "first_name": "Lecteur",
                "last_name": "FATI",
                "role": User.Role.VIEWER,
            },
        ]
        created = 0
        default_region = Region.objects.first()

        for payload in users_data:
            user, was_created = User.objects.get_or_create(
                email=payload["email"],
                defaults={
                    "first_name": payload["first_name"],
                    "last_name": payload["last_name"],
                    "role": payload["role"],
                    "status": User.Status.ACTIVE,
                    "is_active": True,
                    "is_staff": payload.get("is_staff", False),
                    "is_superuser": payload.get("is_superuser", False),
                    "assigned_region": default_region,
                    "password": make_password("test123"),
                },
            )
            if was_created:
                created += 1
            elif not user.is_active:
                user.is_active = True
                user.status = User.Status.ACTIVE
                user.save(update_fields=["is_active", "status"])

        if created:
            self.stdout.write(self.style.SUCCESS(f"Utilisateurs crees: {created} (mot de passe: test123)"))

    def ensure_alerts(self, min_alerts: int):
        existing = Alert.objects.count()
        missing = max(0, min_alerts - existing)
        if missing == 0:
            return

        users = list(User.objects.filter(is_active=True))
        indicators = list(Indicator.objects.all())
        regions = list(Region.objects.all())
        severities = [item[0] for item in Alert.Severity.choices]
        alert_types = [item[0] for item in Alert.AlertType.choices]

        for idx in range(missing):
            indicator = self.rng.choice(indicators) if indicators else None
            region = self.rng.choice(regions) if regions else None
            value = round(self.rng.uniform(20, 95), 2)
            threshold = round(value + self.rng.uniform(-15, 15), 2)

            alert = Alert.objects.create(
                type=self.rng.choice(alert_types),
                severity=self.rng.choice(severities),
                title=f"Alerte automatique {idx + 1}",
                message=f"Verification sur {'indicateur ' + indicator.name if indicator else 'donnees territoriales'}",
                sector=indicator.sector if indicator else "",
                indicator=indicator,
                region=region,
                value=value,
                threshold=threshold,
                is_read=False,
            )
            if users:
                alert.recipients.set(users)

        self.stdout.write(self.style.SUCCESS(f"Alertes generees: +{missing}."))

    # ------------------------------------------------------------------
    # Indicator helpers
    # ------------------------------------------------------------------
    def _get_or_create_indicator(
        self,
        sector: str,
        category: str,
        indicator_type: str,
        name: str,
        group_key: str,
        sheet_name: str,
        unit: str,
        description: str,
        target_value: Optional[float] = None,
        alert_threshold: Optional[float] = None,
    ):
        clean_name = " ".join(name.split()).strip()
        indicator = Indicator.objects.filter(sector=sector, name__iexact=clean_name).first()
        if indicator:
            updates = {}
            if unit and not indicator.unit:
                updates["unit"] = unit
            if target_value is not None and indicator.target_value is None:
                updates["target_value"] = target_value
            if alert_threshold is not None and indicator.alert_threshold is None:
                updates["alert_threshold"] = alert_threshold
            if updates:
                for field, value in updates.items():
                    setattr(indicator, field, value)
                indicator.save(update_fields=list(updates.keys()))
            return indicator, False

        code = self._build_indicator_code(sector, group_key, sheet_name, clean_name)
        defaults = {
            "description": description,
            "category": category,
            "type": indicator_type,
            "unit": unit or "",
            "is_active": True,
            "target_value": target_value,
            "alert_threshold": alert_threshold,
        }

        indicator, created = Indicator.objects.get_or_create(
            code=code,
            defaults={"name": clean_name, "sector": sector, **defaults},
        )

        if created:
            return indicator, True

        if indicator.name.lower() == clean_name.lower() and indicator.sector == sector:
            return indicator, False

        # Collision de code: creer avec suffixe deterministe.
        code = self._build_indicator_code(
            sector, group_key, sheet_name, f"{clean_name}-{abs(hash(clean_name)) % 1000}"
        )
        indicator, created = Indicator.objects.get_or_create(
            code=code,
            defaults={"name": clean_name, "sector": sector, **defaults},
        )
        return indicator, created

    def _build_indicator_code(self, sector: str, group_key: str, sheet_name: str, indicator_name: str) -> str:
        raw = f"{sector}_{group_key}_{sheet_name}_{indicator_name}"
        token = slugify(raw).replace("-", "_").upper()
        token = re.sub(r"[^A-Z0-9_]", "", token)
        if not token:
            token = f"{sector[:3].upper()}_IND"
        return token[:50]

    def _upsert_indicator_value(
        self,
        indicator: Indicator,
        year: int,
        value: float,
        region: Optional[Region],
        department: Optional[Department],
        commune: Optional[Commune],
        source: str,
    ):
        IndicatorValue.objects.update_or_create(
            indicator=indicator,
            region=region,
            department=department,
            commune=commune,
            year=year,
            period="",
            defaults={
                "value": value,
                "status": IndicatorValue.Status.VALIDATED,
                "source": source,
                "target_value": indicator.target_value,
            },
        )

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    def _normalize(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        text = unicodedata.normalize("NFKD", str(value))
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^A-Za-z0-9]+", " ", text).strip().upper()
        return text

    def _parse_number(self, value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text or text in {"-", "--", "...", "NA", "N/A"}:
            return None

        text = text.replace("\xa0", " ").replace("%", "").replace(" ", "")

        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif text.count(",") == 1 and "." not in text:
            text = text.replace(",", ".")
        elif text.count(",") > 1 and "." not in text:
            text = text.replace(",", "")

        try:
            return float(text)
        except ValueError:
            return None

    def _parse_int(self, value) -> Optional[int]:
        number = self._parse_number(value)
        if number is None:
            return None
        return int(number)

    def _extract_year_values(self, row: dict) -> Iterable[Tuple[int, float]]:
        year_values = []
        for key, raw in row.items():
            key_str = str(key).strip()
            if not re.fullmatch(r"(19|20)\d{2}", key_str):
                continue
            value = self._parse_number(raw)
            if value is None:
                continue
            year_values.append((int(key_str), value))
        return year_values

    def _extract_year_map_from_education_row(self, row: dict) -> Dict[str, int]:
        year_map = {}
        for col, raw in row.items():
            if raw is None:
                continue
            match = re.search(r"(19|20)\d{2}", str(raw))
            if match:
                year_map[col] = int(match.group(0))
        return year_map

    def _parse_education_indicator_line(self, text: str) -> Tuple[str, str]:
        indicator_match = re.search(r"indicateurs?\s*:\s*([^,]+)", text, flags=re.IGNORECASE)
        unit_match = re.search(r"unit[ée]?\s*:\s*([^,]+)", text, flags=re.IGNORECASE)
        indicator_name = indicator_match.group(1).strip() if indicator_match else text.strip()
        unit = unit_match.group(1).strip() if unit_match else ""
        return indicator_name, unit

    def _clean_indicator_name(self, value: str) -> str:
        text = str(value or "").strip()
        text = text.replace("(*)", "")
        text = re.sub(r"\s+", " ", text).strip(" -:;")
        return text

    def _looks_like_header(self, indicator_name: str) -> bool:
        normalized = self._normalize(indicator_name)
        if not normalized or len(normalized) < 3:
            return True
        blocked_patterns = [
            "PRINCIPAUX INDICATEURS",
            "DECOUPAGE ADMINISTRATIF",
            "ETABLISSEMENTS DE SANTE",
            "INDICATEURS",
        ]
        return any(pattern in normalized for pattern in blocked_patterns)

    def _is_education_meta_row(self, normalized_value: str) -> bool:
        meta_prefixes = [
            "STATUT",
            "CYCLES",
            "NIVEAU",
            "MILIEU",
            "SEXE",
            "ACADEMIES",
            "IA",
        ]
        return any(normalized_value.startswith(prefix) for prefix in meta_prefixes)

    def _guess_category(self, sector: str, group_key: str, sheet_name: str, indicator_name: str) -> str:
        text = self._normalize(f"{group_key} {sheet_name} {indicator_name}")

        if sector == "health":
            if any(token in text for token in ["DEPENSE", "BUDGET", "FINANCE"]):
                return Indicator.Category.FINANCE
            if any(token in text for token in ["PERSONNEL", "SOIGNANT", "MEDECIN", "SAGE FEMME"]):
                return Indicator.Category.PERSONNEL
            if any(token in text for token in ["LIT", "ETABLISSEMENT", "HOPITAL", "CENTRE", "POSTE", "INFRA"]):
                return Indicator.Category.INFRASTRUCTURE
            if any(token in text for token in ["MORTAL", "PREVALENCE", "DECES", "RESULTAT"]):
                return Indicator.Category.OUTCOMES
            if any(token in text for token in ["ACCES", "COUVERTURE", "CONSULTATION", "VACCIN"]):
                return Indicator.Category.ACCESS
            return Indicator.Category.RESOURCES

        if any(token in text for token in ["RESULTAT", "REUSSITE", "ADMIS", "EXAMEN"]):
            return Indicator.Category.OUTCOMES
        if any(token in text for token in ["ETABLISSEMENT", "CLASSE", "SALLE", "INFRA"]):
            return Indicator.Category.INFRASTRUCTURE
        if any(token in text for token in ["ENSEIGNANT", "PERSONNEL", "MAITRE"]):
            return Indicator.Category.PERSONNEL
        if any(token in text for token in ["SCOLAR", "INSCRIPTION", "ACCES"]):
            return Indicator.Category.ACCESS
        if "RATIO" in text or "QUALITE" in text:
            return Indicator.Category.QUALITY
        return Indicator.Category.RESOURCES

    def _guess_type(self, unit: str, indicator_name: str) -> str:
        normalized = self._normalize(f"{unit} {indicator_name}")
        unit_norm = self._normalize(unit)

        if "%" in unit or "TAUX" in normalized or "POURCENT" in normalized:
            return Indicator.Type.PERCENTAGE
        if "RATIO" in normalized or unit_norm in {"PER 1000", "1000", "POUR 1000"}:
            return Indicator.Type.RATIO
        if any(token in normalized for token in ["BUDGET", "DEPENSE", "COUT", "FCFA"]):
            return Indicator.Type.CURRENCY
        if any(token in normalized for token in ["NOMBRE", "EFFECTIF", "NB", "ETABLISSEMENT"]):
            return Indicator.Type.COUNT
        return Indicator.Type.NUMBER

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _next_code(self, model_cls, prefix: str) -> str:
        idx = 1
        while True:
            code = f"{prefix}-{idx:04d}"
            if not model_cls.objects.filter(code=code).exists():
                return code
            idx += 1

    def print_summary(self):
        self.stdout.write("Resume des volumes:")
        self.stdout.write(f"  Regions: {Region.objects.count()}")
        self.stdout.write(f"  Departements: {Department.objects.count()}")
        self.stdout.write(f"  Communes: {Commune.objects.count()}")
        self.stdout.write(f"  Indicateurs: {Indicator.objects.count()}")
        self.stdout.write(f"  Valeurs d'indicateurs: {IndicatorValue.objects.count()}")
        self.stdout.write(f"  Structures sante: {HealthFacility.objects.count()}")
        self.stdout.write(f"  Structures education: {EducationFacility.objects.count()}")
        self.stdout.write(f"  Utilisateurs: {User.objects.count()}")
        self.stdout.write(f"  Alertes: {Alert.objects.count()}")
