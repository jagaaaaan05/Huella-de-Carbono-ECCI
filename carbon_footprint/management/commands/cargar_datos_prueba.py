"""Carga un conjunto de datos de prueba que recorre todas las funciones de la aplicación.

Uso:
    python manage.py cargar_datos_prueba            # carga catálogos (si faltan), datos y corridas
    python manage.py cargar_datos_prueba --reset    # borra los periodos de prueba y los vuelve a crear
    python manage.py cargar_datos_prueba --sin-corridas

Periodos que crea:
    2022 anual   -> inventario oficial ECCI (herramienta Excel). Neto esperado: 304,342 t CO2e.
    2023 anual   -> escenario completo: 3 sedes y TODOS los tipos de registro.
    2024 ene-mar -> periodos mensuales (electricidad, agua, papel) y un caso con advertencia.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rest_framework.test import APIRequestFactory

from carbon_footprint.models import (
    CalculationRun,
    Campus,
    ElectricityConsumption,
    EmissionFactor,
    ExtinguisherRefill,
    FieldPracticeTrip,
    Flight,
    FuelConsumption,
    GroundTransportRecord,
    IndustrialProcessEmission,
    LodgingRecord,
    LubricantConsumption,
    NaturalGasConsumption,
    PaperConsumption,
    PaperWeightCatalog,
    Period,
    RemovalRecord,
    VehicleFleetConsumption,
    WasteRecord,
    WaterConsumption,
)
from carbon_footprint.views import CalculationRunView

TEST_PERIODS = [(2022, None), (2023, None), (2024, 1), (2024, 2), (2024, 3)]

# Modelos con FK a Period: se usan para saber si un periodo ya tiene datos.
RECORD_MODELS = [
    ElectricityConsumption, NaturalGasConsumption, FuelConsumption, VehicleFleetConsumption,
    IndustrialProcessEmission, LubricantConsumption, ExtinguisherRefill, WasteRecord,
    PaperConsumption, WaterConsumption, Flight, GroundTransportRecord, LodgingRecord,
    FieldPracticeTrip, RemovalRecord, CalculationRun,
]


def _period(year, month=None):
    if month:
        import calendar
        last = calendar.monthrange(year, month)[1]
        start, end = f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last:02d}"
    else:
        start, end = f"{year}-01-01", f"{year}-12-31"
    period, _ = Period.objects.get_or_create(
        year=year, month=month, defaults={"start_date": start, "end_date": end}
    )
    return period


class Command(BaseCommand):
    help = "Carga datos de prueba (2022 oficial, 2023 completo, 2024 mensual) y ejecuta corridas de cálculo."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Borra los periodos de prueba (2022, 2023, 2024-01..03) y sus registros antes de cargar.")
        parser.add_argument("--sin-corridas", action="store_true",
                            help="Solo carga datos; no ejecuta corridas de cálculo.")

    def handle(self, *args, **options):
        if not EmissionFactor.objects.exists():
            self.stdout.write("Catálogo vacío: cargando initial_data.json ...")
            call_command("loaddata", "initial_data", verbosity=0)

        test_periods = [
            period.id for period in Period.objects.filter(year__in=[2022, 2023, 2024])
            if (period.year, period.month) in TEST_PERIODS
        ]
        has_data = any(
            model.objects.filter(period_id__in=test_periods).exists() for model in RECORD_MODELS
        )
        if has_data and not options["reset"]:
            raise CommandError(
                "Ya hay registros en 2022, 2023 o 2024 (ene-mar). "
                "Usa --reset para borrarlos y recargar los datos de prueba."
            )

        with transaction.atomic():
            if options["reset"]:
                for year, month in TEST_PERIODS:
                    Period.objects.filter(year=year, month=month).delete()
                self.stdout.write(self.style.WARNING("Periodos de prueba anteriores eliminados."))

            principal, norte, sur = (Campus.objects.get(pk=pk) for pk in (1, 2, 3))
            self._load_2022(principal)
            self._load_2023(principal, norte, sur)
            self._load_2024(principal, norte, sur)

        self.stdout.write(self.style.SUCCESS("Datos de prueba cargados."))
        if not options["sin_corridas"]:
            self._run_calculations(principal, norte, sur)

    # ------------------------------------------------------------------ 2022
    def _load_2022(self, principal):
        """Datos de actividad 2022 de la herramienta Excel ECCI (informe oficial)."""
        period = _period(2022)
        base = {"period": period, "campus": principal}

        NaturalGasConsumption.objects.create(**base, fuel_type_id="GASNATURAL", m3=5975)
        VehicleFleetConsumption.objects.create(**base, description="Vehículos institucionales", fuel_type_id="GASOLINA", unit="gal", amount=2951.57)
        VehicleFleetConsumption.objects.create(**base, description="Vehículos institucionales", fuel_type_id="ACPM", unit="gal", amount=684.54)
        ExtinguisherRefill.objects.create(**base, description="Extintores CO2", ext_type_id="CO2", unit="kg", amount=473.66)
        ExtinguisherRefill.objects.create(**base, description="Extintores R-123", ext_type_id="HCFC-123", unit="kg", amount=225.7)
        ElectricityConsumption.objects.create(**base, description="Consumo total 2022", kwh=1503331.485)

        flights = [
            ("Rio de Janeiro", True, 2), ("Cali", False, 23), ("Cali", True, 31),
            ("Medellín-Enrique Olaya Herrera", False, 11), ("Medellín-Enrique Olaya Herrera", True, 16),
            ("Cartagena", True, 9), ("Santa Marta", True, 1), ("Santiago de Chile", True, 2),
            ("Ciudad de México", True, 1), ("Ciudad de Panamá", True, 1), ("Frankfurt", True, 1),
            ("Guadalajara", True, 3), ("La Habana", True, 1), ("Madrid", True, 2), ("Quito", True, 2),
            ("San Francisco", True, 1),
        ]
        for destination, round_trip, passengers in flights:
            Flight.objects.create(period=period, origin="Bogotá", destination=destination,
                                  round_trip=round_trip, passengers=passengers)
        FieldPracticeTrip.objects.create(**base, description="Salidas de campo", origin="Bogotá",
                                         destination="Varios", km_oneway=16353.1, total_km=32706.2)

        # La herramienta Excel reporta el papel en kg: formato "kg" de 1 kg por "resma".
        kg_sheet, _ = PaperWeightCatalog.objects.get_or_create(size="kg", defaults={"kg_per_ream": 1})
        PaperConsumption.objects.create(**base, size=kg_sheet, reams=2011)
        WasteRecord.objects.create(**base, waste_type_id="RESIDUO_RSU", unit="kg", amount=30230.3)
        WasteRecord.objects.create(**base, waste_type_id="RESIDUO_PEL", unit="kg", amount=1790.86)
        RemovalRecord.objects.create(**base, rtype="forestal", description="Cupressus lusitanica",
                                     activity_value=74, activity_unit="arbol")
        RemovalRecord.objects.create(**base, rtype="reciclaje", description="Aprovechamiento de residuos",
                                     activity_value=3746.5, activity_unit="kg")

    # ------------------------------------------------------------------ 2023
    def _load_2023(self, principal, norte, sur):
        """Escenario completo: cada tipo de registro y cada regla del motor al menos una vez."""
        period = _period(2023)
        p = {"period": period, "campus": principal}
        n = {"period": period, "campus": norte}
        s = {"period": period, "campus": sur}

        # ED1 combustión estacionaria (gas natural + combustibles líquidos/sólidos)
        NaturalGasConsumption.objects.create(**p, fuel_type_id="GASNATURAL", m3=6210)
        NaturalGasConsumption.objects.create(**n, fuel_type_id="GASNATURAL", m3=1480)
        FuelConsumption.objects.create(**p, description="Planta eléctrica de respaldo", fuel_type_id="ACPM", unit="gal", amount=118)
        FuelConsumption.objects.create(**n, description="Cocina cafetería (GLP)", fuel_type_id="GLP", unit="kg", amount=320)
        FuelConsumption.objects.create(**s, description="Planta eléctrica Sede Sur (litros)", fuel_type_id="ACPM", unit="litros", amount=190)

        # ED2 combustión móvil
        VehicleFleetConsumption.objects.create(**p, description="Camionetas institucionales", fuel_type_id="GASOLINA", unit="gal", amount=3020.4, km_traveled=84500)
        VehicleFleetConsumption.objects.create(**p, description="Bus institucional", fuel_type_id="ACPM", unit="gal", amount=712.8, km_traveled=9800)
        VehicleFleetConsumption.objects.create(**s, description="Motocicleta mensajería", fuel_type_id="GASOLINA", unit="gal", amount=96.5, km_traveled=7200)

        # ED3 procesos industriales (laboratorios)
        IndustrialProcessEmission.objects.create(**p, description="Laboratorio de materiales", process_type="Producción de vidrio especial (laboratorio)", unit="t", activity=0.35)
        IndustrialProcessEmission.objects.create(**n, description="Práctica de calcinación", process_type="Calcinación de Calcita (CaCO3)", unit="kg", activity=120)

        # ED4 fugitivas (GWP del tipo de extintor/refrigerante)
        ExtinguisherRefill.objects.create(**p, description="Recarga extintores CO2", ext_type_id="CO2", unit="kg", amount=486.2)
        ExtinguisherRefill.objects.create(**p, description="Recarga extintores R-123", ext_type_id="HCFC-123", unit="kg", amount=210.4)
        ExtinguisherRefill.objects.create(**n, description="Aire acondicionado sala de cómputo", ext_type_id="HFC-410A", unit="kg", amount=3.2)
        ExtinguisherRefill.objects.create(**s, description="Nevera cafetería", ext_type_id="HFC-134a", unit="kg", amount=0.8)

        # ED5 lubricantes
        LubricantConsumption.objects.create(**p, description="Aceite de motor flota", unit="gal", amount=42)
        LubricantConsumption.objects.create(**p, description="Grasa lubricante mantenimiento", unit="kg", amount=15)

        # EI1 electricidad
        ElectricityConsumption.objects.create(**p, description="Medidor general", kwh=1548200)
        ElectricityConsumption.objects.create(**n, description="Medidor general", kwh=418750)
        ElectricityConsumption.objects.create(**s, description="Medidor general", kwh=262300)

        # EI2 transporte y hospedaje
        for destination, round_trip, passengers in [
            ("Cali", True, 28), ("Cali", False, 12), ("Medellín-José María Córdova", True, 22),
            ("Cartagena", True, 7), ("Barranquilla", True, 5), ("Bucaramanga", False, 4),
            ("Madrid", True, 3), ("Ciudad de México", True, 2), ("Quito", True, 2),
        ]:
            Flight.objects.create(period=period, description="Viajes académicos 2023", origin="Bogotá",
                                  destination=destination, round_trip=round_trip, passengers=passengers)
        # Vuelo de regreso a Bogotá (usa la misma ruta del catálogo)
        Flight.objects.create(period=period, description="Regreso ponentes", origin="Cartagena",
                              destination="Bogotá", round_trip=False, passengers=3)
        FieldPracticeTrip.objects.create(**p, description="Salidas de campo ingeniería ambiental", origin="Bogotá",
                                         destination="Villa de Leyva", km_oneway=165, total_km=4950)
        FieldPracticeTrip.objects.create(**s, description="Salida de campo", origin="Bogotá",
                                         destination="Girardot", km_oneway=134, total_km=2680)
        GroundTransportRecord.objects.create(**p, description="Bus intermunicipal docentes", unit="pkm", amount=26400)
        GroundTransportRecord.objects.create(**n, description="Transmilenio funcionarios", unit="pasajero-km", amount=118000)
        GroundTransportRecord.objects.create(**s, description="Taxi diligencias", unit="pkm", amount=3150)
        LodgingRecord.objects.create(**p, description="Hotel Medellín congreso", nights=24)
        LodgingRecord.objects.create(**n, description="Alojamiento y desayuno Cartagena", nights=9)

        # EI3 papel (blanco y reciclado, tres formatos)
        PaperConsumption.objects.create(**p, size_id="A4", reams=780)
        PaperConsumption.objects.create(**p, size_id="Carta", reams=210, recycled=True)
        PaperConsumption.objects.create(**n, size_id="Carta", reams=260)
        PaperConsumption.objects.create(**s, size_id="Oficio", reams=140)

        # EI4 residuos (cuatro tratamientos)
        WasteRecord.objects.create(**p, waste_type_id="RESIDUO_RSU", unit="kg", amount=31480)
        WasteRecord.objects.create(**p, waste_type_id="RESIDUO_PEL", unit="kg", amount=1825.4)
        WasteRecord.objects.create(**p, waste_type_id="RESIDUO_ORG", unit="kg", amount=2600)
        WasteRecord.objects.create(**p, waste_type_id="RESIDUO_REC", unit="kg", amount=3100)
        WasteRecord.objects.create(**n, waste_type_id="RESIDUO_RSU", unit="t", amount=8.9)
        WasteRecord.objects.create(**s, waste_type_id="RESIDUO_RSU", unit="kg", amount=5950)

        # EI5 agua (se registra, NO suma al total)
        WaterConsumption.objects.create(**p, description="Acueducto", m3=17850)
        WaterConsumption.objects.create(**n, description="Acueducto", m3=4920)
        WaterConsumption.objects.create(**s, description="Acueducto", m3=3100)

        # RE1 remociones (forestal, aprovechamiento y entrada directa)
        RemovalRecord.objects.create(**p, rtype="forestal", description="Cupressus lusitanica", activity_value=74, activity_unit="arbol")
        RemovalRecord.objects.create(**n, rtype="forestal", description="Alnus acuminata", activity_value=30, activity_unit="arbol")
        RemovalRecord.objects.create(**p, rtype="reciclaje", description="Aprovechamiento de residuos", activity_value=3920, activity_unit="kg")
        RemovalRecord.objects.create(**s, rtype="compensacion", description="Certificado de compensación (entrada directa)", tco2e=1.5)

    # ------------------------------------------------------------------ 2024
    def _load_2024(self, principal, norte, sur):
        """Periodos mensuales para probar filtros por mes y el histórico."""
        monthly = {
            1: (128400, 34100, 21800, 1420, 60),
            2: (136900, 36250, 23100, 1510, 75),
            3: (141300, 37800, 23900, 1580, 70),
        }
        for month, (kwh_p, kwh_n, kwh_s, water, reams) in monthly.items():
            period = _period(2024, month)
            for campus, kwh in ((principal, kwh_p), (norte, kwh_n), (sur, kwh_s)):
                ElectricityConsumption.objects.create(period=period, campus=campus, description="Factura mensual", kwh=kwh)
            WaterConsumption.objects.create(period=period, campus=principal, description="Factura mensual", m3=water)
            PaperConsumption.objects.create(period=period, campus=principal, size_id="Carta", reams=reams)

        # Caso con advertencia: remoción sin cantidad ni tCO2e (la API no lo permite;
        # se crea directo para ver cómo la app muestra advertencias).
        RemovalRecord.objects.create(period=_period(2024, 3), campus=sur, rtype="forestal",
                                     description="Siembra pendiente de medición")

    # ------------------------------------------------------------------ corridas
    def _run_calculations(self, principal, norte, sur):
        factory = APIRequestFactory()
        view = CalculationRunView.as_view()
        runs = [(_period(2022), None), (_period(2023), None)]
        runs += [(_period(2023), campus) for campus in (principal, norte, sur)]
        runs += [(_period(2024, month), None) for month in (1, 2, 3)]

        self.stdout.write("\nCorridas de cálculo guardadas en el histórico:")
        for period, campus in runs:
            body = {"period_id": period.id, "include_traces": True}
            if campus:
                body["campus_id"] = campus.id
            response = view(factory.post("/api/calculation-runs/", body, format="json"))
            totals = response.data["totals"]
            label = f"{period.year}" + (f"-{period.month:02d}" if period.month else " anual")
            label += f" · {campus.name if campus else 'Todas las sedes'}"
            warnings = len(response.data["warnings"])
            self.stdout.write(
                f"  {label:<32} bruto {totals['gross_tco2e']:>9.3f}  remociones {totals['removals_tco2e']:>8.3f}"
                f"  neto {totals['net_tco2e']:>9.3f} t CO2e" + (f"  ({warnings} advertencia/s)" if warnings else "")
            )
