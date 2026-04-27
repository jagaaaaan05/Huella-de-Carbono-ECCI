// Catalog-level config: header matching, select sources, and download endpoints.
import { normalise, formatPeriodLabel } from '../utils.js';

export const HEADER_CATALOG_MAP = [
  {
    matches: ['combustible', 'medio de transporte', 'combustible utilizado'].map(normalise),
    endpoint: 'fuel-types',
    valueField: 'fuel_code',
    label: (item) => `${item.description} (${item.fuel_code})`,
  },
  {
    matches: ['agente utilizado', 'tipo de agente'].map(normalise),
    endpoint: 'extinguisher-types',
    valueField: 'ext_code',
    label: (item) => `${item.description} (${item.ext_code})`,
  },
  {
    matches: ['consumo de papel', 'formato de papel'].map(normalise),
    endpoint: 'paper-weight',
    valueField: 'size',
    label: (item) => `${item.size} · ${item.kg_per_ream} kg/paq.`,
  },
  {
    matches: ['tratamiento y/o disposicion final de residuos', 'tipo de residuo'].map(normalise),
    endpoint: 'waste-types',
    valueField: 'waste_code',
    label: (item) => `${item.description} (${item.waste_code})`,
  },
];

export const STATIC_HEADER_OPTIONS = [
  {
    matches: ['energia electrica'].map(normalise),
    options: [
      { value: 'red_sin', label: 'Electricidad de red (SIN)' },
      { value: 'autogeneracion_diesel', label: 'Autogeneracion diesel' },
      { value: 'autogeneracion_solar', label: 'Autogeneracion solar' },
      { value: 'contrato_renovable', label: 'Contrato de energia renovable' },
    ],
  },
  {
    matches: ['tipo de vuelo'].map(normalise),
    options: [
      { value: 'nacional', label: 'Nacional' },
      { value: 'internacional_corto', label: 'Internacional corto radio' },
      { value: 'internacional_largo', label: 'Internacional largo radio' },
    ],
  },
  {
    matches: ['tipo de produccion'].map(normalise),
    options: [
      { value: 'vapor', label: 'Generacion de vapor' },
      { value: 'refrigeracion', label: 'Refrigeracion' },
      { value: 'manufactura', label: 'Manufactura general' },
      { value: 'laboratorio', label: 'Procesos de laboratorio' },
    ],
  },
  {
    matches: ['alojamiento y hospedaje'].map(normalise),
    options: [
      { value: 'hotel_urbano', label: 'Hotel urbano' },
      { value: 'hotel_rural', label: 'Hotel rural' },
      { value: 'residencia_universitaria', label: 'Residencia universitaria' },
      { value: 'apartahotel', label: 'Apartahotel' },
    ],
  },
  {
    matches: ['residuos aprovechables'].map(normalise),
    options: [
      { value: 'papel_carton', label: 'Papel y carton' },
      { value: 'plastico', label: 'Plastico' },
      { value: 'vidrio', label: 'Vidrio' },
      { value: 'metal', label: 'Metal' },
      { value: 'organico_compostable', label: 'Organico compostable' },
    ],
  },
];

export const UNIT_OPTIONS_BY_RECORD_KEY = {
  fuelStationary: [
    { value: 'gal', label: 'Galones (gal)' },
    { value: 'l', label: 'Litros (L)' },
    { value: 'm3', label: 'Metros cubicos (m3)' },
    { value: 'kg', label: 'Kilogramos (kg)' },
  ],
  fuelMobile: [
    { value: 'gal', label: 'Galones (gal)' },
    { value: 'l', label: 'Litros (L)' },
    { value: 'm3', label: 'Metros cubicos (m3)' },
    { value: 'kg', label: 'Kilogramos (kg)' },
  ],
  electricity: [
    { value: 'kwh', label: 'Kilovatio-hora (kWh)' },
    { value: 'mwh', label: 'Megavatio-hora (MWh)' },
  ],
  flights: [
    { value: 'pasajero', label: 'Pasajero' },
    { value: 'pasajero_km', label: 'Pasajero-km' },
  ],
  fieldPractice: [
    { value: 'km', label: 'Kilometros (km)' },
    { value: 'pasajero_km', label: 'Pasajero-km' },
  ],
  groundTransport: [
    { value: 'km', label: 'Kilometros (km)' },
    { value: 'pasajero_km', label: 'Pasajero-km' },
    { value: 'tonelada_km', label: 'Tonelada-km' },
    { value: 'l', label: 'Litros (L)' },
    { value: 'gal', label: 'Galones (gal)' },
  ],
  lodging: [
    { value: 'noche', label: 'Noche' },
    { value: 'noche_persona', label: 'Noche-persona' },
  ],
  paper: [
    { value: 'resma', label: 'Resma' },
    { value: 'kg', label: 'Kilogramos (kg)' },
  ],
  waste: [
    { value: 'kg', label: 'Kilogramos (kg)' },
    { value: 't', label: 'Toneladas (t)' },
  ],
  extinguisherRefill: [
    { value: 'kg', label: 'Kilogramos (kg)' },
  ],
  removals: [
    { value: 't', label: 'Toneladas (t)' },
    { value: 'kg', label: 'Kilogramos (kg)' },
  ],
};

export const UNIT_OPTIONS_BY_SUBSCREEN = {
  'sub-procesos': [
    { value: 'kg', label: 'Kilogramos (kg)' },
    { value: 't', label: 'Toneladas (t)' },
    { value: 'm3', label: 'Metros cubicos (m3)' },
    { value: 'unidad', label: 'Unidad producida' },
  ],
  'sub-emisiones2': [
    { value: 'l', label: 'Litros (L)' },
    { value: 'gal', label: 'Galones (gal)' },
    { value: 'kg', label: 'Kilogramos (kg)' },
  ],
  'sub-captura-tecnologica': [
    { value: 't', label: 'Toneladas (t)' },
    { value: 'kg', label: 'Kilogramos (kg)' },
  ],
};

export const DOWNLOAD_ENDPOINTS = {
  campus: 'campus',
  periods: 'periods',
  fuelTypes: 'fuel-types',
  wasteTypes: 'waste-types',
  extinguisherTypes: 'extinguisher-types',
  paperWeights: 'paper-weight',
};

export const SELECT_SOURCE_CONFIG = {
  periods: {
    endpoint: 'periods',
    value: (item) => item.id,
    label: formatPeriodLabel,
  },
  campus: {
    endpoint: 'campus',
    value: (item) => item.id,
    label: (item) => item.name,
  },
  fuelTypes: {
    endpoint: 'fuel-types',
    value: (item) => item.fuel_code,
    label: (item) => `${item.description} (${item.fuel_code})`,
  },
  extinguisherTypes: {
    endpoint: 'extinguisher-types',
    value: (item) => item.ext_code,
    label: (item) => `${item.description} (${item.ext_code})`,
  },
  wasteTypes: {
    endpoint: 'waste-types',
    value: (item) => item.waste_code,
    label: (item) => `${item.description} (${item.waste_code})`,
  },
  paperWeights: {
    endpoint: 'paper-weight',
    value: (item) => item.size,
    label: (item) => `${item.size} · ${item.kg_per_ream} kg/paq.`,
  },
  emissionFactors: {
    endpoint: 'emission-factors',
    value: (item) => item.id,
    label: (item) => `${item.agent} (${item.gas})`,
  },
};
