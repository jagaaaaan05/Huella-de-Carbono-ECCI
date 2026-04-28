// Uncertainty defaults aligned with backend methodology.

export const SOURCE_CODE_BY_RECORD_KEY = {
  fuelStationary: 'ED1',
  fuelMobile: 'ED2',
  extinguisherRefill: 'ED4',
  electricity: 'EI1',
  flights: 'EI2',
  fieldPractice: 'EI2',
  groundTransport: 'EI2',
  lodging: 'EI2',
  paper: 'EI3',
  waste: 'EI4',
  removals: 'RE1',
};

export const ACTIVITY_UNCERTAINTY_BY_SUBSCREEN = {
  'sub-combustibles1': 0.5,
  'sub-combustibles2': 0.5,
  'sub-procesos': 0.5,
  'sub-emisiones1': 0.1,
  'sub-emisiones2': 0.5,
  'sub-electricidad': 1.0,
  'sub-viajes': 0.5,
  'sub-desplazamiento1': 0.5,
  'sub-desplazamiento2': 0.5,
  'sub-hospedaje': 0.5,
  'sub-consumo': 50.0,
  'sub-residuos': 0.1,
  'sub-reforestacion': 0.1,
  'sub-captura-tecnologica': 0.1,
};
