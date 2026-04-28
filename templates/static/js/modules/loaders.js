// Table hydration and record loading from the API.
import { normalise } from '../utils.js';
import {
  HEADER_CATALOG_MAP,
  STATIC_HEADER_OPTIONS,
  UNIT_OPTIONS_BY_RECORD_KEY,
  UNIT_OPTIONS_BY_SUBSCREEN,
} from '../config/catalogs.js';
import { TABLE_DATA_CONFIG } from '../config/tables.js';
import { fetchCatalog, populateSelectElement } from './api.js';

let activeInventoryFilters = {};

const STRICT_RULES_BY_SUBSCREEN = {
  'sub-combustibles1': {
    variable: 'A_m3',
    units: ['gal', 'l', 'm3', 'kg'],
  },
  'sub-combustibles2': {
    variable: 'A_litros',
    units: ['gal', 'l', 'm3', 'kg'],
  },
  'sub-procesos': {
    variable: 'Q',
    units: ['kg', 't', 'm3', 'unidad'],
  },
  'sub-emisiones1': {
    variable: 'm_kg',
    units: ['kg'],
  },
  'sub-emisiones2': {
    variable: 'actividad',
    units: ['l', 'gal', 'kg'],
  },
  'sub-electricidad': {
    variable: 'consumo_kwh',
    units: ['kwh'],
  },
  'sub-viajes': {
    variable: 'dato_actividad',
    units: ['pasajero'],
  },
  'sub-desplazamiento1': {
    variable: 'dato_actividad',
    units: ['km'],
  },
  'sub-desplazamiento2': {
    variable: 'dato_actividad',
    units: ['km', 'pasajero_km', 'tonelada_km', 'l', 'gal'],
  },
  'sub-hospedaje': {
    variable: 'dato_actividad',
    units: ['noche_persona'],
  },
  'sub-consumo': {
    variable: 'resmas',
    units: ['resma'],
  },
  'sub-residuos': {
    variable: 'masa',
    units: ['kg', 't'],
  },
  'sub-reforestacion': {
    variable: 'N',
    integer: true,
  },
  'sub-captura-tecnologica': {
    variable: 'masa_t',
    units: ['t'],
  },
};

const staticSelectConfig = (options) => ({
  valueField: 'value',
  label: (item) => item.label,
  options,
});

const resolveStaticCatalogForColumn = (table, header) => {
  const matchedHeaderConfig = STATIC_HEADER_OPTIONS.find((entry) =>
    entry.matches.some((match) => header.includes(match))
  );

  if (matchedHeaderConfig) {
    return staticSelectConfig(matchedHeaderConfig.options);
  }

  if (!header.includes('unidad')) {
    return null;
  }

  const subId = table.closest('.subscreen')?.id;
  const recordKey = table.dataset.recordKey;
  const options =
    (subId && UNIT_OPTIONS_BY_SUBSCREEN[subId]) ||
    (recordKey && UNIT_OPTIONS_BY_RECORD_KEY[recordKey]);

  if (!options || !options.length) {
    return null;
  }

  return staticSelectConfig(options);
};

const filterUnitOptions = (select, allowedUnits) => {
  if (!select || !allowedUnits || !allowedUnits.length) {
    return;
  }

  const allowed = new Set(allowedUnits);
  Array.from(select.options).forEach((option) => {
    if (option.value && !allowed.has(option.value)) {
      option.remove();
    }
  });

  if (select.value && !allowed.has(select.value)) {
    select.value = '';
  }
};

const enforceStrictRules = (table, headers) => {
  const subId = table.closest('.subscreen')?.id;
  const rule = subId ? STRICT_RULES_BY_SUBSCREEN[subId] : null;
  if (!rule) {
    return;
  }

  const variableInputs = table.querySelectorAll('tbody [data-carbon-field]');
  variableInputs.forEach((input) => {
    input.min = '0';
    if (rule.integer) {
      input.step = '1';
    }
    if (rule.variable && input.dataset.carbonField !== rule.variable) {
      input.setCustomValidity(
        `Variable no valida para esta tabla. Esperada: ${rule.variable}.`
      );
    } else {
      input.setCustomValidity('');
    }
  });

  if (!rule.units?.length) {
    return;
  }

  const unitColumnIndex = headers.findIndex((header) => header.includes('unidad'));
  if (unitColumnIndex < 0) {
    return;
  }

  table
    .querySelectorAll(`tbody tr td:nth-child(${unitColumnIndex + 1}) select`)
    .forEach((select) => {
      filterUnitOptions(select, rule.units);
    });
};

const normaliseInventoryFilters = (raw = {}) => {
  const queryParams = {};
  if (raw.period_id !== undefined && raw.period_id !== null && `${raw.period_id}` !== '') {
    queryParams.period_id = `${raw.period_id}`;
  }
  if (raw.campus_id !== undefined && raw.campus_id !== null && `${raw.campus_id}` !== '') {
    queryParams.campus_id = `${raw.campus_id}`;
  }
  return queryParams;
};

const getActiveInventoryFilters = () => {
  if (Object.keys(activeInventoryFilters).length) {
    return activeInventoryFilters;
  }

  const periodId = document.getElementById('official-period')?.value || '';
  const campusId = document.getElementById('official-campus')?.value || '';

  return normaliseInventoryFilters({ period_id: periodId, campus_id: campusId });
};

export const hydrateTable = async (table) => {
  const headers = Array.from(table.querySelectorAll('thead th')).map((th) =>
    normalise(th.textContent)
  );

  for (let columnIndex = 0; columnIndex < headers.length; columnIndex += 1) {
    const header = headers[columnIndex];
    const staticCatalog = resolveStaticCatalogForColumn(table, header);
    const selects = table.querySelectorAll(
      `tbody tr td:nth-child(${columnIndex + 1}) select`
    );

    if (staticCatalog) {
      selects.forEach((select) => {
        populateSelectElement(select, staticCatalog.options, staticCatalog);
      });
      continue;
    }

    const catalog = HEADER_CATALOG_MAP.find((entry) =>
      entry.matches.some((match) => header.includes(match))
    );

    if (!catalog) {
      continue;
    }

    let options = [];
    try {
      options = await fetchCatalog(catalog.endpoint);
    } catch (error) {
      console.error(error);
      continue;
    }

    selects.forEach((select) => {
      populateSelectElement(select, options, catalog);
    });
  }

  enforceStrictRules(table, headers);
};

export const hydrateAllTables = () => {
  document.querySelectorAll('table.emisiones-table').forEach((table) => {
    hydrateTable(table).catch((error) => console.error(error));
  });
};

export const resetRowInputs = (row) => {
  row.querySelectorAll('input').forEach((input) => {
    if (input.type === 'checkbox' || input.type === 'radio') {
      input.checked = input.defaultChecked;
    } else {
      input.value = '';
    }
  });
  row.querySelectorAll('select').forEach((select) => {
    if (select.options.length > 0) {
      select.selectedIndex = 0;
    } else {
      select.value = '';
    }
  });
};

export const setCellValue = (cell, value, display) => {
  const input = cell.querySelector('input');
  const select = cell.querySelector('select');

  if (input) {
    if (input.type === 'checkbox') {
      input.checked = Boolean(value);
    } else {
      input.value = value ?? '';
    }
    return;
  }

  if (select) {
    const valueStr = value == null ? '' : `${value}`;
    if (!valueStr) {
      select.selectedIndex = 0;
      return;
    }
    const existing = Array.from(select.options).find(
      (option) => option.value === valueStr
    );
    if (existing) {
      select.value = valueStr;
      return;
    }
    const option = document.createElement('option');
    option.value = valueStr;
    option.textContent = display || valueStr;
    option.selected = true;
    select.appendChild(option);
    return;
  }

  cell.textContent = value ?? '';
};

export const populateTableFromRecords = async (table, config) => {
  const tbody = table.querySelector('tbody');
  if (!tbody) {
    return;
  }
  const templateRow = tbody.querySelector('tr');
  if (!templateRow) {
    return;
  }
  const template = templateRow.cloneNode(true);

  let records = [];
  try {
    records = await fetchCatalog(config.endpoint, {
      force: true,
      queryParams: getActiveInventoryFilters(),
    });
  } catch (error) {
    console.error(error);
    return;
  }

  tbody.innerHTML = '';

  if (!records.length) {
    const emptyRow = template.cloneNode(true);
    resetRowInputs(emptyRow);
    tbody.appendChild(emptyRow);
    await hydrateTable(table);
    table.dispatchEvent(new Event('carbon:refresh'));
    return;
  }

  records.forEach((record) => {
    const row = template.cloneNode(true);
    resetRowInputs(row);
    const cells = row.querySelectorAll('td');
    const values = config.mapRecord(record) || [];

    values.forEach((entry, index) => {
      const cell = cells[index];
      if (!cell) {
        return;
      }
      if (
        entry &&
        typeof entry === 'object' &&
        Object.prototype.hasOwnProperty.call(entry, 'value')
      ) {
        setCellValue(cell, entry.value, entry.display);
      } else {
        setCellValue(cell, entry);
      }
    });

    tbody.appendChild(row);
  });

  await hydrateTable(table);
  table.dispatchEvent(new Event('carbon:refresh'));
};

export const initTableDataLoaders = () => {
  const buttons = document.querySelectorAll('.subtab[data-record-key]');

  const loadForButton = async (button) => {
    const key = button.dataset.recordKey;
    const subId = button.dataset.sub;
    if (!key || !subId) {
      return;
    }
    const config = TABLE_DATA_CONFIG[key];
    if (!config) {
      return;
    }
    const subScreen = document.getElementById(`sub-${subId}`);
    if (!subScreen) {
      return;
    }
    const table = subScreen.querySelector(`table[data-record-key="${key}"]`);
    if (!table) {
      return;
    }
    try {
      await populateTableFromRecords(table, config);
    } catch (error) {
      console.error(error);
    }
  };

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      loadForButton(button);
    });
  });

  const refreshAllRecordTables = async () => {
    const tables = document.querySelectorAll('table[data-record-key]');
    for (const table of tables) {
      const recordKey = table.dataset.recordKey;
      const config = recordKey ? TABLE_DATA_CONFIG[recordKey] : null;
      if (!config) {
        continue;
      }
      await populateTableFromRecords(table, config);
    }
  };

  document.addEventListener('inventory-filter-change', (event) => {
    activeInventoryFilters = normaliseInventoryFilters(event.detail || {});
    refreshAllRecordTables().catch((error) => console.error(error));
  });

  document.querySelectorAll('.subtab.active[data-record-key]').forEach((button) => {
    loadForButton(button);
  });
};
