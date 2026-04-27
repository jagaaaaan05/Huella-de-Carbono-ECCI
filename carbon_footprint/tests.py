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
)


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
