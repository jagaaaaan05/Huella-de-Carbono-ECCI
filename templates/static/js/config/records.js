// API endpoint configuration for each record type used in forms and tables.

export const RECORD_CONFIG = {
  electricity: {
    endpoint: 'electricity',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción (opcional)', placeholder: 'Descripción del consumo' },
      { name: 'kwh', label: 'Consumo (kWh)', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  naturalGas: {
    endpoint: 'natural-gas',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'fuel_type_id', label: 'Tipo de combustible', type: 'select', source: 'fuelTypes', required: true },
      { name: 'm3', label: 'Consumo (m³)', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  fuelStationary: {
    endpoint: 'fuel',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción de la fuente', required: true },
      { name: 'fuel_type_id', label: 'Combustible', type: 'select', source: 'fuelTypes', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'galones, litros...', required: true },
      { name: 'amount', label: 'Consumo', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  fuelMobile: {
    endpoint: 'vehicle-fleet',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción de la fuente', required: true },
      { name: 'fuel_type_id', label: 'Combustible', type: 'select', source: 'fuelTypes', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'galones, litros...', required: true },
      { name: 'amount', label: 'Consumo', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'km_traveled', label: 'Kilómetros recorridos', type: 'number', step: '0.01', cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  extinguisherRefill: {
    endpoint: 'extinguisher-refill',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción', required: true },
      { name: 'ext_type_id', label: 'Tipo de agente', type: 'select', source: 'extinguisherTypes', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'kg', required: true, default: 'kg' },
      { name: 'amount', label: 'Cantidad', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  waste: {
    endpoint: 'waste',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'waste_type_id', label: 'Tipo de residuo', type: 'select', source: 'wasteTypes', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'kg', required: true, default: 'kg' },
      { name: 'amount', label: 'Cantidad', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  paper: {
    endpoint: 'paper',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción (opcional)', placeholder: 'Área o responsable' },
      { name: 'size_id', label: 'Formato de papel', type: 'select', source: 'paperWeights', required: true },
      { name: 'reams', label: 'Cantidad (resmas)', type: 'number', step: '1', min: '0', required: true, cast: 'int' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  purchases: {
    endpoint: 'purchases',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'good_service', label: 'Bien o servicio', required: true, placeholder: 'Descripción del bien/servicio' },
      { name: 'amount', label: 'Monto (COP)', type: 'number', step: '0.01', required: true, cast: 'float' },
      {
        name: 'emission_factor_id',
        label: 'Factor de emisión (opcional)',
        type: 'select',
        source: 'emissionFactors',
        placeholder: 'Sin factor específico',
      },
    ],
  },
  flights: {
    endpoint: 'flights',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'description', label: 'Descripción (opcional)', placeholder: 'Tipo de vuelo / motivo' },
      { name: 'origin', label: 'Origen', required: true },
      { name: 'destination', label: 'Destino', required: true },
      { name: 'passengers', label: 'Número de pasajeros', type: 'number', step: '1', min: '1', required: true, cast: 'int' },
      { name: 'km', label: 'Distancia (km)', type: 'number', step: '0.01', cast: 'float' },
      { name: 'total_tco2e', label: 'Emisiones totales (tCO₂e)', type: 'number', step: '0.001', cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  fieldPractice: {
    endpoint: 'field-practice',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción (opcional)', placeholder: 'Programa / actividad' },
      { name: 'origin', label: 'Origen', required: true },
      { name: 'destination', label: 'Destino', required: true },
      { name: 'km_oneway', label: 'Kilómetros (solo ida)', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'total_km', label: 'Kilómetros totales', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  removals: {
    endpoint: 'removals',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'rtype', label: 'Tipo de remoción', required: true, placeholder: 'Descripción de la remoción' },
      { name: 'tco2e', label: 'Remoción (tCO₂e)', type: 'number', step: '0.001', required: true, cast: 'float' },
    ],
  },
  groundTransport: {
    endpoint: 'ground-transport',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción de la fuente', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'km, pax-km...', required: true },
      { name: 'amount', label: 'Cantidad', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
  lodging: {
    endpoint: 'lodging',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede / campus', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción del alojamiento', required: true },
      { name: 'nights', label: 'Número de noches', type: 'number', step: '1', min: '1', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Catálogo oficial' },
    ],
  },
};
