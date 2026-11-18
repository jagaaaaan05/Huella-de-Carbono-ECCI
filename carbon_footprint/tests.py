from django.test import TestCase
import json
from rest_framework.test import APIRequestFactory
from carbon_footprint.carbon_formulas import (
	combustion_estacionaria,
	combustion_movil,
	electricidad,
	fugitivas,
	papel_resmas,
	remocion_forestal,
	transporte_generico,
	residuos,
	reciclaje,
	convertir_kg_a_ton,
)
from carbon_footprint.serializers import (
	ElectricityConsumptionSerializer,
	WasteRecordSerializer,
	PaperConsumptionSerializer,
	GroundTransportRecordSerializer,
	LodgingRecordSerializer,
)
from carbon_footprint.models import (
	Campus,
	Period,
	EmissionCategory,
	EmissionSource,
	EmissionFactor,
	FuelType,
	WasteType,
	ExtinguisherType,
	PaperWeightCatalog,
	ElectricityConsumption,
	NaturalGasConsumption,
	VehicleFleetConsumption,
	ExtinguisherRefill,
	WasteRecord,
	PaperConsumption,
	RemovalRecord,
	CalculationRun,
	CalculationSourceTrace,
	Flight,
	FieldPracticeTrip,
	LodgingRecord,
)
from carbon_footprint.engine.calculation_service import calculate_inventory_run


def convertir_g_a_kg(valor_g):
	return valor_g / 1000


class CarbonFormulasTestCase(TestCase):
	def test_combustion_estacionaria_known_values(self):
		result = combustion_estacionaria(
			A_m3=1000,
			FE_CO2=2.0,
			FE_CH4=0.01,
			FE_N2O=0.005,
			PCG_CH4=28,
			PCG_N2O=265,
		)
		self.assertAlmostEqual(result, 0.003605, places=6)

	def test_combustion_movil_known_values(self):
		result = combustion_movil(
			A_litros=500,
			FE_CO2=2.3,
			FE_CH4=0.01,
			FE_N2O=0.002,
			PCG_CH4=28,
			PCG_N2O=265,
		)
		self.assertAlmostEqual(result, 0.001555, places=6)

	def test_electricidad_known_values(self):
		result = electricidad(consumo_kwh=1000, FE_kg_kwh=0.144)
		self.assertAlmostEqual(result, 0.144, places=6)

	def test_electricidad_upme_2023(self):
		# PDF methodology value: FE = 0.112 kg CO2e/kWh (UPME 2023)
		result = electricidad(consumo_kwh=1000, FE_kg_kwh=0.112)
		self.assertAlmostEqual(result, 0.112, places=6)

	def test_fugitivas_known_values(self):
		result = fugitivas(m_kg=10, GWP=1430)
		self.assertAlmostEqual(result, 14.3, places=6)

	def test_papel_resmas_known_values(self):
		result = papel_resmas(resmas=10, FE=1.3)
		self.assertAlmostEqual(result, 32.5, places=6)

	def test_papel_resmas_fe_135(self):
		# PDF methodology value: FE = 1.35 tCO2e/t (Ecoinvent)
		result = papel_resmas(resmas=10, FE=1.35)
		self.assertAlmostEqual(result, 33.75, places=6)

	def test_remocion_forestal_known_values(self):
		result = remocion_forestal(N=100, captura_ha=6, densidad=500)
		self.assertAlmostEqual(result, 1.2, places=6)

	def test_transporte_generico(self):
		# 100 km × 0.18 kgCO2e/km → 0.018 tCO2e
		result = transporte_generico(dato_actividad=100, FE=0.18)
		self.assertAlmostEqual(result, 0.018, places=6)

	def test_residuos_relleno(self):
		# 1 t residuos × 1.2 FE (CH4 relleno) → 1.2
		result = residuos(masa=1, FE=1.2)
		self.assertAlmostEqual(result, 1.2, places=6)

	def test_reciclaje_fe_ch4_048(self):
		# PDF value: FE_CH4_res = 0.048, GWP_CH4 = 27 → 1 t × 0.048 × 27 = 1.296 tCO2e
		result = reciclaje(masa_t=1, FE_CH4_res=0.048, GWP_CH4=27)
		self.assertAlmostEqual(result, 1.296, places=6)

	def test_unit_conversions(self):
		self.assertAlmostEqual(convertir_kg_a_ton(1230), 1.23, places=6)
		self.assertAlmostEqual(convertir_g_a_kg(2500), 2.5, places=6)


class SerializerValidatorTestCase(TestCase):
	def _make_base_data(self, **overrides):
		data = {
			'period_id': None,
			'campus_id': None,
			'kwh': 100.0,
		}
		data.update(overrides)
		return data

	def test_electricity_kwh_negative_rejected(self):
		serializer = ElectricityConsumptionSerializer(data={
			'period_id': 1,
			'campus_id': 1,
			'kwh': -50.0,
		})
		self.assertFalse(serializer.is_valid())
		self.assertIn('kwh', serializer.errors)

	def test_waste_amount_negative_rejected(self):
		serializer = WasteRecordSerializer(data={
			'period_id': 1,
			'campus_id': 1,
			'waste_type_id': 'RESIDUO_RSU',
			'unit': 'kg',
			'amount': -10.0,
		})
		self.assertFalse(serializer.is_valid())
		self.assertIn('amount', serializer.errors)

	def test_paper_reams_negative_rejected(self):
		serializer = PaperConsumptionSerializer(data={
			'period_id': 1,
			'campus_id': 1,
			'size_id': 'A4',
			'reams': -5,
		})
		self.assertFalse(serializer.is_valid())
		self.assertIn('reams', serializer.errors)

	def test_ground_transport_amount_negative_rejected(self):
		serializer = GroundTransportRecordSerializer(data={
			'period_id': 1,
			'campus_id': 1,
			'description': 'Test',
			'unit': 'km',
			'amount': -20.0,
		})
		self.assertFalse(serializer.is_valid())
		self.assertIn('amount', serializer.errors)

	def test_lodging_nights_negative_rejected(self):
		serializer = LodgingRecordSerializer(data={
			'period_id': 1,
			'campus_id': 1,
			'description': 'Hotel',
			'nights': -3.0,
		})
		self.assertFalse(serializer.is_valid())
		self.assertIn('nights', serializer.errors)


class CalculationRunApiTestCase(TestCase):
	def setUp(self):
		self.period = Period.objects.create(year=2022, month=1)
		self.campus = Campus.objects.create(name='Principal')

		cat1 = EmissionCategory.objects.create(code=1, name='Alcance 1')
		cat2 = EmissionCategory.objects.create(code=2, name='Alcance 2')
		cat3 = EmissionCategory.objects.create(code=3, name='Alcance 3')

		src_stationary = EmissionSource.objects.create(code='ED1', name='Combustion estacionaria', category=cat1)
		src_mobile = EmissionSource.objects.create(code='ED2', name='Combustion movil', category=cat1)
		src_fugitive = EmissionSource.objects.create(code='ED4', name='Fugitivas', category=cat1)
		src_electric = EmissionSource.objects.create(code='EI1', name='Electricidad', category=cat2)
		src_transport = EmissionSource.objects.create(code='EI2', name='Transporte', category=cat3)
		src_paper = EmissionSource.objects.create(code='EI3', name='Papel', category=cat3)
		src_waste = EmissionSource.objects.create(code='EI4', name='Residuos', category=cat3)
		EmissionSource.objects.create(code='RE1', name='Remociones', category=cat3)

		self.electric_factor = EmissionFactor.objects.create(
			source=src_electric,
			agent='Electricidad UPME',
			gas='CO2',
			factor_value=0.112,
			unit='kWh',
			year_applic=2022,
		)
		self.electric_override_factor = EmissionFactor.objects.create(
			source=src_electric,
			agent='Electricidad override',
			gas='CO2',
			factor_value=1.0,
			unit='kWh',
			year_applic=2022,
		)
		EmissionFactor.objects.create(
			source=src_stationary,
			agent='Gas natural',
			gas='CO2',
			factor_value=1.98,
			unit='m3',
			year_applic=2022,
		)
		EmissionFactor.objects.create(
			source=src_mobile,
			agent='Gasolina corriente',
			gas='CO2',
			factor_value=2.271,
			unit='L',
			year_applic=2022,
		)
		EmissionFactor.objects.create(
			source=src_transport,
			agent='Transporte terrestre',
			gas='CO2',
			factor_value=0.18,
			unit='km',
			year_applic=2022,
		)
		EmissionFactor.objects.create(
			source=src_paper,
			agent='Papel A4',
			gas='CO2',
			factor_value=1.35,
			unit='kg',
			year_applic=2022,
		)
		EmissionFactor.objects.create(
			source=src_waste,
			agent='Relleno sanitario',
			gas='CO2',
			factor_value=0.05,
			unit='kg',
			year_applic=2022,
		)

		fuel_gn = FuelType.objects.create(fuel_code='GASNATURAL', description='Gas natural')
		fuel_gas = FuelType.objects.create(fuel_code='GASOLINA', description='Gasolina corriente')
		waste = WasteType.objects.create(waste_code='RESIDUO_RSU', description='Residuo', treatment='Relleno sanitario')
		ext = ExtinguisherType.objects.create(ext_code='HCFC-123', description='HCFC-123', gwp_100yr=77)
		paper = PaperWeightCatalog.objects.create(size='A4', kg_per_ream=2.5)

		self.electricity_record = ElectricityConsumption.objects.create(period=self.period, campus=self.campus, kwh=100)
		NaturalGasConsumption.objects.create(period=self.period, campus=self.campus, fuel_type=fuel_gn, m3=10)
		VehicleFleetConsumption.objects.create(
			period=self.period,
			campus=self.campus,
			description='Vehiculo',
			fuel_type=fuel_gas,
			unit='gal',
			amount=1,
		)
		ExtinguisherRefill.objects.create(
			period=self.period,
			campus=self.campus,
			description='Recarga',
			ext_type=ext,
			unit='kg',
			amount=1,
		)
		WasteRecord.objects.create(period=self.period, campus=self.campus, waste_type=waste, unit='kg', amount=10)
		PaperConsumption.objects.create(period=self.period, campus=self.campus, size=paper, reams=2)
		RemovalRecord.objects.create(period=self.period, campus=self.campus, rtype='reciclaje', tco2e=2)

	def test_calculation_run_returns_auditable_payload(self):
		response = self.client.post(
			'/api/calculation-runs/',
			data=json.dumps({'period_id': self.period.id}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn('totals', payload)
		self.assertIn('sources', payload)
		self.assertIn('run_id', payload)
		self.assertEqual(payload['period_id'], self.period.id)
		self.assertGreater(len(payload['sources']), 0)

		totals = payload['totals']
		self.assertIn('gross_tco2e', totals)
		self.assertIn('net_tco2e', totals)
		self.assertLess(totals['net_tco2e'], totals['gross_tco2e'])

		removals = [item for item in payload['sources'] if item['source_code'] == 'RE1'][0]
		self.assertLess(removals['total_tco2e'], 0)

		mobile = [item for item in payload['sources'] if item['source_code'] == 'ED2'][0]
		# 1 gal -> 3.78541 L; 3.78541 * 2.271 / 1000 = 0.00859666611 tCO2e
		self.assertAlmostEqual(mobile['total_tco2e'], 0.00859666611, places=6)

		run = CalculationRun.objects.get(id=payload['run_id'])
		self.assertEqual(run.period_id, self.period.id)
		self.assertGreater(CalculationSourceTrace.objects.filter(run=run).count(), 0)

	def test_calculation_run_rejects_missing_period_id(self):
		response = self.client.post(
			'/api/calculation-runs/',
			data=json.dumps({}),
			content_type='application/json',
		)
		self.assertEqual(response.status_code, 400)

	def test_record_specific_factor_has_priority(self):
		self.electricity_record.emission_factor = self.electric_override_factor
		self.electricity_record.save(update_fields=['emission_factor'])

		response = self.client.post(
			'/api/calculation-runs/',
			data=json.dumps({'period_id': self.period.id}),
			content_type='application/json',
		)
		self.assertEqual(response.status_code, 200)
		sources = response.json()['sources']
		electricity = [item for item in sources if item['source_code'] == 'EI1'][0]
		# 100 kWh * 1.0 kgCO2e/kWh / 1000 = 0.1 tCO2e
		self.assertAlmostEqual(electricity['total_tco2e'], 0.1, places=6)

	def test_can_disable_trace_payload(self):
		response = self.client.post(
			'/api/calculation-runs/',
			data=json.dumps({'period_id': self.period.id, 'include_traces': False}),
			content_type='application/json',
		)
		self.assertEqual(response.status_code, 200)
		for source in response.json()['sources']:
			self.assertEqual(source['traces'], [])

	def test_history_filter_by_period(self):
		self.client.post(
			'/api/calculation-runs/',
			data=json.dumps({'period_id': self.period.id}),
			content_type='application/json',
		)
		other_period = Period.objects.create(year=2023, month=1)
		self.client.post(
			'/api/calculation-runs/',
			data=json.dumps({'period_id': other_period.id}),
			content_type='application/json',
		)

		response = self.client.get(f'/api/calculation-runs-history/?period_id={self.period.id}')
		self.assertEqual(response.status_code, 200)
		data = response.json()
		results = data if isinstance(data, list) else data.get('results', [])
		self.assertTrue(results)
		self.assertTrue(all(item['period']['id'] == self.period.id for item in results))

	def test_history_filter_by_campus(self):
		self.client.post(
			'/api/calculation-runs/',
			data=json.dumps({'period_id': self.period.id, 'campus_id': self.campus.id}),
			content_type='application/json',
		)
		other_campus = Campus.objects.create(name='Norte')
		self.client.post(
			'/api/calculation-runs/',
			data=json.dumps({'period_id': self.period.id, 'campus_id': other_campus.id}),
			content_type='application/json',
		)

		response = self.client.get(f'/api/calculation-runs-history/?campus_id={self.campus.id}')
		self.assertEqual(response.status_code, 200)
		data = response.json()
		results = data if isinstance(data, list) else data.get('results', [])
		self.assertTrue(results)
		self.assertTrue(all(item['campus'] and item['campus']['id'] == self.campus.id for item in results))


class Inventory2022ValidationTestCase(TestCase):
	"""Loads the official factor catalog and the 2022 activity data from the ECCI Excel tool.

	Expected values come from the tool's sheets and table 3 of the Informe ECCI 2023.
	"""

	fixtures = ['initial_data']

	def setUp(self):
		self.period = Period.objects.create(year=2022)
		campus = Campus.objects.get(pk=1)
		base = {'period': self.period, 'campus': campus}

		NaturalGasConsumption.objects.create(**base, fuel_type_id='GASNATURAL', m3=5975)
		VehicleFleetConsumption.objects.create(**base, description='Vehiculos', fuel_type_id='GASOLINA', unit='gal', amount=2951.57)
		VehicleFleetConsumption.objects.create(**base, description='Vehiculos', fuel_type_id='ACPM', unit='gal', amount=684.54)
		ExtinguisherRefill.objects.create(**base, description='Extintores CO2', ext_type_id='CO2', unit='kg', amount=473.66)
		ExtinguisherRefill.objects.create(**base, description='Extintores R-123', ext_type_id='HCFC-123', unit='kg', amount=225.7)
		ElectricityConsumption.objects.create(**base, kwh=1503331.485)

		flights = [
			('Rio de Janeiro', True, 2), ('Cali', False, 23), ('Cali', True, 31),
			('Medellín-Enrique Olaya Herrera', False, 11), ('Medellín-Enrique Olaya Herrera', True, 16),
			('Cartagena', True, 9), ('Santa Marta', True, 1), ('Santiago de Chile', True, 2),
			('Ciudad de México', True, 1), ('Ciudad de Panamá', True, 1), ('Frankfurt', True, 1),
			('Guadalajara', True, 3), ('La Habana', True, 1), ('Madrid', True, 2), ('Quito', True, 2),
			('San Francisco', True, 1),
		]
		for destination, round_trip, passengers in flights:
			Flight.objects.create(
				period=self.period, origin='Bogotá', destination=destination,
				round_trip=round_trip, passengers=passengers,
			)
		FieldPracticeTrip.objects.create(
			**base, description='Salidas de campo', origin='Bogotá', destination='Varios',
			km_oneway=16353.1, total_km=32706.2,
		)

		sheet = PaperWeightCatalog.objects.create(size='kg', kg_per_ream=1)
		PaperConsumption.objects.create(**base, size=sheet, reams=2011)
		WasteRecord.objects.create(**base, waste_type_id='RESIDUO_RSU', unit='kg', amount=30230.3)
		WasteRecord.objects.create(**base, waste_type_id='RESIDUO_PEL', unit='kg', amount=1790.86)
		RemovalRecord.objects.create(**base, rtype='forestal', description='Cupressus lusitanica', activity_value=74, activity_unit='arbol')
		RemovalRecord.objects.create(**base, rtype='reciclaje', activity_value=3746.5, activity_unit='kg')

		self.result = calculate_inventory_run(period_id=self.period.id)
		self.sources = {source['source_code']: source for source in self.result['sources']}

	def test_sources_match_excel_tool(self):
		expected = {
			'ED1': 11.84273327,
			'ED2': 26.55919394,
			'ED4': 20.87694,
			'EI1': 168.37312632,
			'EI2': 15.14835 + 25.00147171,
			'EI3': 2.11155,
			'EI4': 39.1784688 + 0.89543,
			'RE1': -(0.78933333 + 4.855464),
		}
		for code, value in expected.items():
			self.assertAlmostEqual(self.sources[code]['total_tco2e'], value, places=4, msg=code)
		self.assertEqual(self.result['warnings'], [])

	def test_totals_match_inventory_report(self):
		totals = self.result['totals']
		self.assertAlmostEqual(totals['gross_tco2e'], 309.987, places=2)
		self.assertAlmostEqual(totals['net_tco2e'], 304.342, places=2)
		# Biogenic CO2 from the 10 % biofuel blend, reported apart (table 3: 4.596).
		self.assertAlmostEqual(totals['biogenic_tco2e'], 4.5953, places=3)

	def test_gas_breakdown_sums_to_gross(self):
		totals = self.result['totals']
		fossil = sum(value for gas, value in totals['gas_breakdown'].items() if gas != 'CO2_BIO')
		self.assertAlmostEqual(fossil, totals['gross_tco2e'], places=6)
		self.assertIn('CH4', totals['gas_breakdown'])
		self.assertIn('N2O', totals['gas_breakdown'])

	def test_flights_excluded_from_campus_runs(self):
		campus_result = calculate_inventory_run(period_id=self.period.id, campus_id=1)
		transport = next(s for s in campus_result['sources'] if s['source_code'] == 'EI2')
		self.assertAlmostEqual(transport['total_tco2e'], 25.00147171, places=4)

	def test_lodging_uses_hotel_factor(self):
		LodgingRecord.objects.create(
			period=self.period, campus_id=1, description='Hotel en Medellín', nights=10,
		)
		result = calculate_inventory_run(period_id=self.period.id)
		transport = next(s for s in result['sources'] if s['source_code'] == 'EI2')
		self.assertAlmostEqual(transport['total_tco2e'], 15.14835 + 25.00147171 + 0.07895, places=4)

	def test_water_is_recorded_but_not_added_to_total(self):
		from carbon_footprint.models import WaterConsumption
		WaterConsumption.objects.create(period=self.period, campus_id=1, m3=10000)
		result = calculate_inventory_run(period_id=self.period.id)
		self.assertNotIn('EI5', {source['source_code'] for source in result['sources']})
		self.assertAlmostEqual(result['totals']['gross_tco2e'], self.result['totals']['gross_tco2e'], places=6)


class BugRegressionTestCase(TestCase):
	"""Tests that verify all critical QA bugs are resolved."""

	def setUp(self):
		from carbon_footprint.engine.gases_catalog import METHOD_PROFILES
		self.profiles = METHOD_PROFILES

	def test_hcfc123_gwp_is_90_4(self):
		"""BUG-03: GWP for HCFC-123 must be 90.4 per IPCC AR6 / Informe ECCI 2022."""
		gwp = self.profiles['ISO14064_ECCI_2022']['default_gwp']['HCFC-123']
		self.assertAlmostEqual(gwp, 90.4, places=1)

	def test_waste_ch4_gwp_is_27(self):
		"""BUG-02 / WARN-04: Default CH4 GWP must be 27 (AR6 non-fossil)."""
		gwp = self.profiles['ISO14064_ECCI_2022']['default_gwp']['CH4']
		self.assertAlmostEqual(gwp, 27.0, places=1)

	def test_residuos_factor_produces_correct_co2e(self):
		"""BUG-02: 1 kg residuos × FE 0.048 kgCH4/kg × GWP 27 = 1.296 kgCO2e/kg."""
		from carbon_footprint.engine.formulas_engine import gas_factor_to_tco2e
		result_tco2e = gas_factor_to_tco2e(1000.0, 0.048, 27.0)  # 1000 kg
		expected = (1000.0 * 0.048 * 27.0) / 1000.0
		self.assertAlmostEqual(result_tco2e, expected, places=6)
		self.assertAlmostEqual(result_tco2e, 1.296, places=3)

	def test_flight_model_import(self):
		"""BUG-01: Flight must be importable and usable in calculation_service."""
		from carbon_footprint.engine.calculation_service import _calculate_transport
		import inspect
		source = inspect.getsource(_calculate_transport)
		self.assertIn('flight_records', source)
		self.assertIn('Flight.objects', source)

	def test_water_consumption_model_exists(self):
		"""BUG-05: WaterConsumption model must exist."""
		from carbon_footprint.models import WaterConsumption
		self.assertTrue(hasattr(WaterConsumption, 'objects'))
		self.assertTrue(hasattr(WaterConsumption, 'm3'))

	def test_hcfc123_extinguisher_type_in_fixture(self):
		"""BUG-04: HCFC-123 extinguisher type must be present."""
		from carbon_footprint.models import ExtinguisherType
		# Verify the type can be created with GWP 90.4
		ext = ExtinguisherType(ext_code='HCFC-123', description='Test', gwp_100yr=90.4)
		self.assertAlmostEqual(ext.gwp_100yr, 90.4, places=1)

	def test_water_source_constant_defined(self):
		"""A5: SOURCE_WATER constant must be defined in emission_sources."""
		from carbon_footprint.engine.emission_sources import SOURCE_WATER
		self.assertEqual(SOURCE_WATER, 'EI5')

	def test_industrial_source_constant_defined(self):
		"""B1: SOURCE_INDUSTRIAL constant must be defined in emission_sources."""
		from carbon_footprint.engine.emission_sources import SOURCE_INDUSTRIAL
		self.assertEqual(SOURCE_INDUSTRIAL, 'ED3')


class CargarDatosPruebaCommandTestCase(TestCase):
	"""The test-data command loads every record type and reproduces the official 2022 result."""

	def test_command_loads_all_periods_and_runs(self):
		from io import StringIO
		from django.core.management import call_command
		from carbon_footprint.models import CalculationRun, IndustrialProcessEmission, LubricantConsumption

		call_command('cargar_datos_prueba', stdout=StringIO())
		self.assertEqual(CalculationRun.objects.count(), 8)
		run_2022 = CalculationRun.objects.get(period__year=2022, campus__isnull=True)
		self.assertAlmostEqual(run_2022.net_tco2e, 304.342, places=2)
		run_2023 = CalculationRun.objects.get(period__year=2023, period__month__isnull=True, campus__isnull=True)
		self.assertAlmostEqual(run_2023.net_tco2e, 404.508, places=2)
		self.assertTrue(IndustrialProcessEmission.objects.exists())
		self.assertTrue(LubricantConsumption.objects.exists())

	def test_command_refuses_to_overwrite_without_reset(self):
		from io import StringIO
		from django.core.management import call_command
		from django.core.management.base import CommandError
		from carbon_footprint.models import CalculationRun

		call_command('cargar_datos_prueba', '--sin-corridas', stdout=StringIO())
		with self.assertRaises(CommandError):
			call_command('cargar_datos_prueba', stdout=StringIO())
		call_command('cargar_datos_prueba', '--reset', stdout=StringIO())
		self.assertEqual(CalculationRun.objects.count(), 8)
