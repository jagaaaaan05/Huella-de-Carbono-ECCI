// API endpoint configuration for each record type used in forms and tables.

export const RECORD_CONFIG = {
  electricity: {
    endpoint: 'electricity',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción (opcional)', placeholder: 'Ej. Consumo administrativo' },
      { name: 'kwh', label: 'Consumo (kWh)', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  naturalGas: {
    endpoint: 'natural-gas',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'fuel_type_id', label: 'Tipo de combustible', type: 'select', source: 'fuelTypes', required: true },
      { name: 'm3', label: 'Consumo (m³)', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  fuelStationary: {
    endpoint: 'fuel',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción de la fuente', required: true, placeholder: 'Ej. Planta eléctrica principal' },
      { name: 'fuel_type_id', label: 'Combustible', type: 'select', source: 'fuelTypes', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'Ej. galones, litros o m3', required: true },
      { name: 'amount', label: 'Consumo', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  fuelMobile: {
    endpoint: 'vehicle-fleet',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción de la fuente', required: true, placeholder: 'Ej. Bus institucional' },
      { name: 'fuel_type_id', label: 'Combustible', type: 'select', source: 'fuelTypes', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'Ej. galones, litros o m3', required: true },
      { name: 'amount', label: 'Consumo', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'km_traveled', label: 'Kilómetros recorridos', type: 'number', step: '0.01', cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  extinguisherRefill: {
    endpoint: 'extinguisher-refill',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción', required: true, placeholder: 'Ej. Recarga anual de extintores' },
      { name: 'ext_type_id', label: 'Tipo de agente', type: 'select', source: 'extinguisherTypes', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'kg', required: true, default: 'kg' },
      { name: 'amount', label: 'Cantidad', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  waste: {
    endpoint: 'waste',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'waste_type_id', label: 'Tipo de residuo', type: 'select', source: 'wasteTypes', required: true },
      { name: 'unit', label: 'Unidad', placeholder: 'kg', required: true, default: 'kg' },
      { name: 'amount', label: 'Cantidad', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  paper: {
    endpoint: 'paper',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción (opcional)', placeholder: 'Ej. Área o responsable' },
      { name: 'size_id', label: 'Formato de papel', type: 'select', source: 'paperWeights', required: true },
      { name: 'reams', label: 'Cantidad (resmas)', type: 'number', step: '1', min: '0', required: true, cast: 'int' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  purchases: {
    endpoint: 'purchases',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'good_service', label: 'Bien o servicio', required: true, placeholder: 'Ej. Compra de equipos' },
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
      { name: 'description', label: 'Descripción (opcional)', placeholder: 'Ej. Viaje académico' },
      { name: 'origin', label: 'Origen', required: true },
      { name: 'destination', label: 'Destino', required: true },
      { name: 'passengers', label: 'Número de pasajeros', type: 'number', step: '1', min: '1', required: true, cast: 'int' },
      { name: 'km', label: 'Distancia (km)', type: 'number', step: '0.01', cast: 'float' },
      { name: 'total_tco2e', label: 'Emisiones totales (tCO₂e)', type: 'number', step: '0.001', cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  fieldPractice: {
    endpoint: 'field-practice',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción (opcional)', placeholder: 'Ej. Salida de campo' },
      { name: 'origin', label: 'Origen', required: true },
      { name: 'destination', label: 'Destino', required: true },
      { name: 'km_oneway', label: 'Kilómetros (solo ida)', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'total_km', label: 'Kilómetros totales', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  removals: {
    endpoint: 'removals',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'rtype', label: 'Tipo de remoción', required: true, placeholder: 'Ej. Reforestación interna' },
      { name: 'tco2e', label: 'Remoción (tCO₂e)', type: 'number', step: '0.001', required: true, cast: 'float' },
    ],
  },
  groundTransport: {
    endpoint: 'ground-transport',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción de la fuente', required: true, placeholder: 'Ej. Ruta intermunicipal' },
      { name: 'unit', label: 'Unidad', placeholder: 'Ej. km o pasajero-km', required: true },
      { name: 'amount', label: 'Cantidad', type: 'number', step: '0.01', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
  lodging: {
    endpoint: 'lodging',
    fields: [
      { name: 'period_id', label: 'Periodo', type: 'select', source: 'periods', required: true },
      { name: 'campus_id', label: 'Sede', type: 'select', source: 'campus', required: true },
      { name: 'description', label: 'Descripción del alojamiento', required: true, placeholder: 'Ej. Hotel ciudad destino' },
      { name: 'nights', label: 'Número de noches', type: 'number', step: '1', min: '1', required: true, cast: 'float' },
      { name: 'emission_factor_id', label: 'Factor de emisión (opcional)', type: 'select', source: 'emissionFactors', placeholder: 'Selecciona del catálogo oficial' },
    ],
  },
};
