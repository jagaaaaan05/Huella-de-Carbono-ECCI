import { catalogCache } from '../../state.js';
import { RECORD_CONFIG } from '../../config/records.js';

const RECORD_KEY_ALIASES = {
  fuelstationary: 'fuelStationary',
  fuel: 'fuelStationary',
  combustiblesestacionarias: 'fuelStationary',
  fuelmobile: 'fuelMobile',
  vehiclefleet: 'fuelMobile',
  combustiblesmoviles: 'fuelMobile',
  extinguisherrefill: 'extinguisherRefill',
  fugitivas: 'extinguisherRefill',
  electricity: 'electricity',
  flights: 'flights',
  fieldpractice: 'fieldPractice',
  groundtransport: 'groundTransport',
  lodging: 'lodging',
  paper: 'paper',
  waste: 'waste',
  removals: 'removals',
};

const normaliseKey = (value) =>
  `${value || ''}`
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');

const resolveRecordKey = (value) => {
  const key = `${value || ''}`.trim();
  if (!key) {
    return '';
  }
  if (RECORD_CONFIG[key]) {
    return key;
  }
  return RECORD_KEY_ALIASES[normaliseKey(key)] || '';
};

const parseCsvRows = (content) => {
  const lines = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) {
    return [];
  }

  const delimiter = (lines[0].match(/;/g) || []).length > (lines[0].match(/,/g) || []).length
    ? ';'
    : ',';

  const split = (line) => line.split(delimiter).map((cell) => cell.replace(/^"|"$/g, '').trim());
  const headers = split(lines[0]);

  return lines.slice(1).map((line) => {
    const cells = split(line);
    const row = {};
    headers.forEach((header, index) => {
      row[header] = cells[index] ?? '';
    });
    return row;
  });
};

const parseExcelRows = async (arrayBuffer) => {
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(arrayBuffer);
  const worksheet = workbook.worksheets[0];
  if (!worksheet) {
    return [];
  }

  const headers = [];
  worksheet.getRow(1).eachCell((cell, colNumber) => {
    headers[colNumber - 1] = `${cell.value || ''}`.trim();
  });

  const rows = [];
  for (let rowNumber = 2; rowNumber <= worksheet.rowCount; rowNumber += 1) {
    const excelRow = worksheet.getRow(rowNumber);
    if (excelRow.values.every((value) => value == null || `${value}`.trim() === '')) {
      continue;
    }
    const row = {};
    headers.forEach((header, index) => {
      const value = excelRow.getCell(index + 1).value;
      row[header] = value == null ? '' : `${value}`.trim();
    });
    rows.push(row);
  }

  return rows;
};

const fieldValueFromRow = (rowMap, fieldName) => {
  const fieldKey = normaliseKey(fieldName);
  if (Object.prototype.hasOwnProperty.call(rowMap, fieldKey)) {
    return rowMap[fieldKey];
  }

  if (fieldKey === 'periodyear') {
    return rowMap.periodoanio || rowMap.anio || '';
  }
  if (fieldKey === 'periodmonth') {
    return rowMap.periodomes || rowMap.mes || '';
  }
  return '';
};

const buildBulkPayload = (recordKey, row) => {
  const config = RECORD_CONFIG[recordKey];
  if (!config) {
    throw new Error('El tipo de registro no está soportado.');
  }

  const rowMap = {};
  Object.entries(row).forEach(([key, value]) => {
    rowMap[normaliseKey(key)] = `${value ?? ''}`.trim();
  });

  const payload = {};
  config.fields.forEach((field) => {
    const raw = fieldValueFromRow(rowMap, field.name);
    if (!raw) {
      return;
    }

    if (field.cast === 'int') {
      const parsed = Number.parseInt(raw, 10);
      if (!Number.isNaN(parsed)) {
        payload[field.name] = parsed;
      }
      return;
    }

    if (field.cast === 'float' || field.type === 'number') {
      const parsed = Number.parseFloat(`${raw}`.replace(',', '.'));
      if (!Number.isNaN(parsed)) {
        payload[field.name] = parsed;
      }
      return;
    }

    payload[field.name] = raw;
  });

  if (rowMap.periodid && !payload.period_id) {
    payload.period_id = rowMap.periodid;
  }
  if (rowMap.periodyear || rowMap.periodoanio || rowMap.anio) {
    payload.period_year = rowMap.periodyear || rowMap.periodoanio || rowMap.anio;
  }
  if (rowMap.periodmonth || rowMap.periodomes || rowMap.mes) {
    payload.period_month = rowMap.periodmonth || rowMap.periodomes || rowMap.mes;
  }

  return payload;
};

const readUploadRows = async (file) => {
  const fileName = (file?.name || '').toLowerCase();
  if (fileName.endsWith('.csv')) {
    const text = await file.text();
    return parseCsvRows(text);
  }
  if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
    const buffer = await file.arrayBuffer();
    return parseExcelRows(buffer);
  }
  throw new Error('Formato no válido. Usa archivos CSV o XLSX.');
};

export const initBulkUpload = ({
  getCsrfToken,
  ensurePeriodIdInPayload,
  postRecord,
  refreshTablesForRecord,
}) => {
  const fileInput = document.getElementById('bulkUploadFile');
  const runButton = document.getElementById('bulkUploadRun');
  const status = document.getElementById('bulkUploadStatus');
  const globalTypeSelect = document.getElementById('bulkRecordType');
  if (!fileInput || !runButton || !status || !globalTypeSelect) {
    return;
  }

  runButton.addEventListener('click', async () => {
    const file = fileInput.files?.[0];
    if (!file) {
      status.textContent = 'Selecciona un archivo CSV o XLSX para continuar.';
      status.classList.remove('success');
      status.classList.add('error');
      return;
    }

    runButton.disabled = true;
    status.classList.remove('success', 'error');
    status.textContent = 'Estamos procesando tu archivo...';

    const csrfToken = getCsrfToken();
    let success = 0;
    const failures = [];
    const touchedRecordKeys = new Set();

    try {
      const rows = await readUploadRows(file);
      if (!rows.length) {
        throw new Error('El archivo no contiene filas con datos para procesar.');
      }

      for (let index = 0; index < rows.length; index += 1) {
        const row = rows[index];
        const rowMap = {};
        Object.entries(row).forEach(([key, value]) => {
          rowMap[normaliseKey(key)] = `${value ?? ''}`.trim();
        });

        const rowType = resolveRecordKey(rowMap.recordtype || rowMap.tiporegistro || rowMap.tipo);
        const recordKey = resolveRecordKey(globalTypeSelect.value) || rowType;
        if (!recordKey) {
          failures.push(`Fila ${index + 2}: no se identificó el tipo de registro.`);
          continue;
        }

        const config = RECORD_CONFIG[recordKey];
        if (!config) {
          failures.push(`Fila ${index + 2}: el tipo de registro no es válido.`);
          continue;
        }

        try {
          let payload = buildBulkPayload(recordKey, row);
          payload = await ensurePeriodIdInPayload(payload, {
            periodYear:
              rowMap.periodyear || rowMap.periodoanio || rowMap.anio || payload.period_year,
            periodMonth:
              rowMap.periodmonth || rowMap.periodomes || rowMap.mes || payload.period_month,
          });

          await postRecord(config.endpoint, payload, csrfToken);
          catalogCache.delete(config.endpoint);
          touchedRecordKeys.add(recordKey);
          success += 1;
        } catch (rowError) {
          failures.push(`Fila ${index + 2}: ${rowError.message}`);
        }
      }

      touchedRecordKeys.forEach((recordKey) => refreshTablesForRecord(recordKey));

      if (!failures.length) {
        status.textContent = `Carga masiva finalizada. Registros guardados: ${success}.`;
        status.classList.remove('error');
        status.classList.add('success');
      } else {
        status.textContent = `Carga parcial completada. Guardados: ${success}. Errores: ${failures.length}. ${failures.slice(0, 2).join(' | ')}`;
        status.classList.remove('success');
        status.classList.add('error');
      }
    } catch (error) {
      status.textContent = error.message;
      status.classList.remove('success');
      status.classList.add('error');
    } finally {
      runButton.disabled = false;
    }
  });
};
