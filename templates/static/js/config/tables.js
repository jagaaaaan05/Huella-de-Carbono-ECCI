// TABLE_DATA_CONFIG: maps each record type to its API endpoint and row renderer.
import { formatNumber, formatRecordContext } from '../utils.js';

export const TABLE_DATA_CONFIG = {
  fuelStationary: {
    endpoint: 'fuel',
    mapRecord: (record) => [
      record.description || formatRecordContext(record),
      { value: record.fuel_type?.fuel_code, display: record.fuel_type?.description },
      { value: record.unit, display: record.unit },
      formatNumber(record.amount),
      formatNumber(record.total_tco2e),
      '',
      '',
    ],
  },
  fuelMobile: {
    endpoint: 'vehicle-fleet',
    mapRecord: (record) => [
      record.description ||
        formatRecordContext(
          record,
          record.km_traveled ? `${formatNumber(record.km_traveled, 2)} km` : ''
        ),
      { value: record.fuel_type?.fuel_code, display: record.fuel_type?.description },
      { value: record.unit, display: record.unit },
      formatNumber(record.amount),
      '',
      '',
      '',
    ],
  },
  extinguisherRefill: {
    endpoint: 'extinguisher-refill',
    mapRecord: (record) => [
      record.description || formatRecordContext(record),
      { value: record.ext_type?.ext_code, display: record.ext_type?.description },
      { value: record.unit || 'kg', display: record.unit || 'kg' },
      formatNumber(record.amount),
      '',
      '',
      '',
    ],
  },
  electricity: {
    endpoint: 'electricity',
    mapRecord: (record) => [
      formatRecordContext(record),
      record.description || '',
      { value: 'kwh', display: 'kWh' },
      formatNumber(record.kwh),
      '',
      '',
      '',
    ],
  },
  flights: {
    endpoint: 'flights',
    mapRecord: (record) => [
      record.description || `${record.origin || ''} → ${record.destination || ''}`.trim(),
      { value: 'pasajeros', display: 'Pasajeros' },
      { value: 'cantidad', display: 'Cantidad' },
      record.passengers != null ? `${record.passengers}` : '',
      formatNumber(record.total_tco2e),
      '',
      '',
    ],
  },
  fieldPractice: {
    endpoint: 'field-practice',
    mapRecord: (record) => [
      `${record.origin || ''} → ${record.destination || ''}`.trim(),
      { value: record.campus?.name || '', display: record.campus?.name || '' },
      { value: 'km', display: 'Kilómetros' },
      formatNumber(record.total_km, 2),
      '',
      '',
      '',
    ],
  },
  paper: {
    endpoint: 'paper',
    mapRecord: (record) => [
      formatRecordContext(record),
      { value: record.size?.size, display: record.size?.size },
      { value: 'reams', display: 'Resmas' },
      record.reams != null ? `${record.reams}` : '',
      '',
      '',
      '',
    ],
  },
  waste: {
    endpoint: 'waste',
    mapRecord: (record) => [
      formatRecordContext(record),
      { value: record.waste_type?.waste_code, display: record.waste_type?.description },
      { value: record.unit || 'kg', display: record.unit || 'Kilogramos' },
      formatNumber(record.amount),
      '',
      '',
      '',
    ],
  },
  removals: {
    endpoint: 'removals',
    mapRecord: (record) => [
      record.rtype || '',
      record.campus?.name || '',
      formatNumber(record.tco2e),
      '',
      '',
    ],
  },
  groundTransport: {
    endpoint: 'ground-transport',
    mapRecord: (record) => [
      record.description || formatRecordContext(record),
      { value: record.unit || '', display: record.unit || '' },
      { value: record.unit || '', display: record.unit || '' },
      formatNumber(record.amount),
      formatNumber(record.total_tco2e),
      '',
      '',
    ],
  },
  lodging: {
    endpoint: 'lodging',
    mapRecord: (record) => [
      record.description || formatRecordContext(record),
      { value: 'noches', display: 'Noches' },
      { value: 'noches', display: 'Noches' },
      formatNumber(record.nights),
      formatNumber(record.total_tco2e),
      '',
      '',
    ],
  },
};
