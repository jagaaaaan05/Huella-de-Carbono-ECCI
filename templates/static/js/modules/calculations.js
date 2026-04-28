// Table actions engine: export and optional local row management.
import { hydrateTable, resetRowInputs } from './loaders.js';
import { fetchCatalog } from './api.js';
import {
  ACTIVITY_UNCERTAINTY_BY_SUBSCREEN,
  SOURCE_CODE_BY_RECORD_KEY,
} from '../config/uncertainty.js';

const sourceUncertaintyCache = new Map();
const sourceUncertaintyPending = new Map();

const numberFrom = (value, fallback = 0) => {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const getTableSetting = (table, key, fallback = 0) =>
  numberFrom(table.dataset[key], fallback);

const toDisplayNumber = (value) =>
  Number(value || 0).toLocaleString('es-CO', {
    minimumFractionDigits: 3,
    maximumFractionDigits: 6,
  });

const formatResultValue = (value) => {
  const abs = Math.abs(value);
  if (abs > 0 && abs < 0.001) {
    return value.toFixed(6);
  }
  return value.toFixed(3);
};

const formatPercentNumber = (value) => {
  const abs = Math.abs(value);
  if (abs > 0 && abs < 0.001) {
    return value.toLocaleString('es-CO', {
      minimumFractionDigits: 6,
      maximumFractionDigits: 6,
    });
  }
  return value.toLocaleString('es-CO', {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
};

const formatUncertaintyText = (value) => `+/- ${formatPercentNumber(value)}%`;

const resolveSourceCode = (table) => {
  const recordKey = table.dataset.recordKey || '';
  if (SOURCE_CODE_BY_RECORD_KEY[recordKey]) {
    return SOURCE_CODE_BY_RECORD_KEY[recordKey];
  }

  const subId = table.closest('.subscreen')?.id || '';
  if (subId === 'sub-procesos') {
    return 'ED1';
  }
  if (subId === 'sub-emisiones2') {
    return 'ED2';
  }
  return '';
};

const resolveActivityUncertainty = (table) => {
  const subId = table.closest('.subscreen')?.id || '';
  return ACTIVITY_UNCERTAINTY_BY_SUBSCREEN[subId] ?? 0;
};

const resolveFactorUncertainty = (sourceCode) => {
  if (!sourceCode) {
    return 0;
  }
  return sourceUncertaintyCache.get(sourceCode) ?? 0;
};

const preloadFactorUncertainty = (table) => {
  const sourceCode = resolveSourceCode(table);
  if (!sourceCode || sourceUncertaintyCache.has(sourceCode)) {
    return;
  }

  if (sourceUncertaintyPending.has(sourceCode)) {
    return;
  }

  const pending = fetchCatalog('emission-factors', {
    force: false,
    queryParams: { source_code: sourceCode },
  })
    .then((rows) => {
      const values = rows
        .map((row) => Number.parseFloat(`${row.uncertainty_pct ?? ''}`))
        .filter((value) => Number.isFinite(value));
      const avg = values.length
        ? values.reduce((acc, value) => acc + value, 0) / values.length
        : 0;
      sourceUncertaintyCache.set(sourceCode, avg);
    })
    .catch(() => {
      sourceUncertaintyCache.set(sourceCode, 0);
    })
    .finally(() => {
      sourceUncertaintyPending.delete(sourceCode);
      table.dispatchEvent(new Event('carbon:refresh'));
    });

  sourceUncertaintyPending.set(sourceCode, pending);
};

const combinedUncertainty = (activityUnc, factorUnc) =>
  Math.sqrt(activityUnc ** 2 + factorUnc ** 2);

const evaluateFormula = (table, activityValue) => {
  const formula = table.dataset.carbonFormula;

  switch (formula) {
    case 'combustion_estacionaria': {
      const feCo2 = getTableSetting(table, 'defaultFeCo2', 1);
      const feCh4 = getTableSetting(table, 'defaultFeCh4', 1);
      const feN2o = getTableSetting(table, 'defaultFeN2o', 1);
      const eCo2 = (activityValue * feCo2) / 1000;
      const eCh4 = (activityValue * feCh4 * 28) / 1000;
      const eN2o = (activityValue * feN2o * 265) / 1000;
      return (eCo2 + eCh4 + eN2o) / 1000;
    }
    case 'combustion_movil': {
      const feCo2 = getTableSetting(table, 'defaultFeCo2', 1);
      const feCh4 = getTableSetting(table, 'defaultFeCh4', 1);
      const feN2o = getTableSetting(table, 'defaultFeN2o', 1);
      const eCo2 = (activityValue * feCo2) / 1000;
      const eCh4 = (activityValue * feCh4 * 28) / 1000;
      const eN2o = (activityValue * feN2o * 265) / 1000;
      return (eCo2 + eCh4 + eN2o) / 1000;
    }
    case 'procesos_industriales':
    case 'lubricantes':
    case 'residuos': {
      const factor = getTableSetting(table, 'defaultFe', 1);
      return activityValue * factor;
    }
    case 'fugitivas': {
      const gwp = getTableSetting(table, 'defaultGwp', 1);
      return (activityValue * gwp) / 1000;
    }
    case 'electricidad': {
      const fe = getTableSetting(table, 'defaultFeKgKwh', 0.112);
      return (activityValue * fe) / 1000;
    }
    case 'transporte_generico': {
      const fe = getTableSetting(table, 'defaultFe', 0);
      return (activityValue * fe) / 1000;
    }
    case 'papel_resmas': {
      const fe = getTableSetting(table, 'defaultFe', 1.35);
      return activityValue * 2.5 * fe;
    }
    case 'remocion_forestal': {
      const captura = getTableSetting(table, 'defaultCapturaHa', 1);
      const densidad = getTableSetting(table, 'defaultDensidad', 1);
      return densidad > 0 ? (activityValue / densidad) * captura : 0;
    }
    case 'reciclaje': {
      const fe = getTableSetting(table, 'defaultFeCh4Res', 0.048);
      const gwp = getTableSetting(table, 'defaultGwpCh4', 27);
      return activityValue * fe * gwp;
    }
    default:
      return 0;
  }
};

const recalculateTable = (table) => {
  const rows = Array.from(table.querySelectorAll('tbody tr'));
  let total = 0;
  const activityUncertaintyPct = resolveActivityUncertainty(table);
  const factorUncertaintyPct = resolveFactorUncertainty(resolveSourceCode(table));
  const sourceUncertaintyPct = combinedUncertainty(
    activityUncertaintyPct,
    factorUncertaintyPct
  );
  const rowUncertaintyValues = [];

  rows.forEach((row) => {
    const activityInput = row.querySelector('[data-carbon-field]');
    const resultInput = row.querySelector('[data-carbon-result]');
    const uncertaintyInputs = row.querySelectorAll('input[placeholder*="+/-"]');

    if (!activityInput || !resultInput) {
      return;
    }

    const activityValue = numberFrom(activityInput.value, 0);
    const result = evaluateFormula(table, activityValue);
    const rounded = Number.isFinite(result) ? Number(result.toFixed(6)) : 0;

    resultInput.value = activityInput.value ? formatResultValue(rounded) : '';
    if (activityInput.value) {
      if (uncertaintyInputs[0]) {
        uncertaintyInputs[0].value = formatUncertaintyText(activityUncertaintyPct);
      }
      if (uncertaintyInputs[1]) {
        uncertaintyInputs[1].value = formatUncertaintyText(sourceUncertaintyPct);
      }
      rowUncertaintyValues.push(sourceUncertaintyPct);
    } else {
      uncertaintyInputs.forEach((input) => {
        input.value = '';
      });
    }
    total += rounded;
  });

  const totalCell = table.querySelector('[data-carbon-total]');
  if (totalCell) {
    totalCell.textContent = toDisplayNumber(total);
  }

  const footerUncertaintyCell = Array.from(table.querySelectorAll('tfoot td')).find((cell) =>
    cell.textContent.includes('+/-')
  );
  if (footerUncertaintyCell) {
    const avgSourceUncertainty = rowUncertaintyValues.length
      ? rowUncertaintyValues.reduce((acc, value) => acc + value, 0) /
        rowUncertaintyValues.length
      : 0;
    footerUncertaintyCell.textContent = formatUncertaintyText(avgSourceUncertainty);
  }
};

const bindFormulaRecalculation = (table) => {
  if (table.dataset.calcBound === '1') {
    return;
  }
  table.dataset.calcBound = '1';

  table.addEventListener('input', (event) => {
    if (event.target instanceof HTMLInputElement) {
      recalculateTable(table);
    }
  });

  table.addEventListener('change', () => {
    recalculateTable(table);
  });

  table.addEventListener('carbon:refresh', () => {
    recalculateTable(table);
  });

  preloadFactorUncertainty(table);
};

const csvEscape = (value) => {
  const clean = (value ?? '').toString().replace(/\r?\n|\r/g, ' ').trim();
  return `"${clean.replace(/"/g, '""')}"`;
};

const cellToExportValue = (cell) => {
  const select = cell.querySelector('select');
  if (select) {
    const selected = select.options[select.selectedIndex];
    return selected ? selected.textContent : '';
  }
  const input = cell.querySelector('input');
  if (input) {
    return input.value || input.placeholder || '';
  }
  return cell.textContent || '';
};

const buildCsvContent = (table) => {
  const rows = Array.from(table.querySelectorAll('tr'));
  const delimiter = ';';
  const content = rows
    .map((row) =>
      Array.from(row.querySelectorAll('th,td'))
        .map((cell) => csvEscape(cellToExportValue(cell)))
        .join(delimiter)
    )
    .join('\n');
  return `\uFEFF${content}`;
};

const exportFilename = (table) => {
  const sectionId = table.closest('section')?.id || 'inventario';
  const subSectionId = table.closest('.subscreen')?.id || 'tabla';
  const now = new Date();
  const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
  return `${sectionId}_${subSectionId}_${stamp}.csv`;
};

const ensureLocalEditButtons = (actions) => {
  if (!actions) {
    return;
  }

  const exportButton = actions.querySelector('[data-carbon-action="export"]');
  if (!actions.querySelector('[data-carbon-action="add-row"]')) {
    const addButton = document.createElement('button');
    addButton.dataset.carbonAction = 'add-row';
    addButton.textContent = 'Agregar fila';
    actions.insertBefore(addButton, exportButton || actions.firstChild);
  }

  if (!actions.querySelector('[data-carbon-action="remove-row"]')) {
    const removeButton = document.createElement('button');
    removeButton.dataset.carbonAction = 'remove-row';
    removeButton.textContent = 'Quitar fila';
    actions.insertBefore(removeButton, exportButton || actions.firstChild);
  }
};

export const setupTableActions = (table) => {
  const scope =
    table.closest('.subscreen') ||
    table.closest('section') ||
    table.parentElement ||
    table;

  const scopedActions = scope?.querySelector('.action-buttons');
  const siblingActions = table.nextElementSibling?.classList?.contains('action-buttons')
    ? table.nextElementSibling
    : null;
  const actions = scopedActions || siblingActions;

  if (!actions) {
    return;
  }

  const calculateButton = actions.querySelector('[data-carbon-action="calculate"]');
  if (calculateButton) {
    calculateButton.remove();
  }

  ensureLocalEditButtons(actions);

  const addRow = () => {
    const tbody = table.querySelector('tbody');
    const templateRow = tbody?.querySelector('tr');
    if (!tbody || !templateRow) {
      return;
    }
    const newRow = templateRow.cloneNode(true);
    resetRowInputs(newRow);
    tbody.appendChild(newRow);
    hydrateTable(table).catch((error) => console.error(error));
    recalculateTable(table);
  };

  const removeRow = () => {
    const tbody = table.querySelector('tbody');
    if (!tbody || !tbody.lastElementChild) {
      return;
    }
    if (tbody.children.length > 1) {
      tbody.removeChild(tbody.lastElementChild);
    } else {
      resetRowInputs(tbody.firstElementChild);
      const output = tbody.firstElementChild?.querySelector('[data-carbon-result]');
      if (output) {
        output.value = '';
      }
    }
    recalculateTable(table);
  };

  const exportTable = () => {
    const csv = buildCsvContent(table);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = exportFilename(table);
    anchor.click();
    URL.revokeObjectURL(url);
  };

  actions.querySelectorAll('[data-carbon-action]').forEach((button) => {
    const action = button.dataset.carbonAction;
    button.type = 'button';
    if (action === 'add-row') {
      button.addEventListener('click', addRow);
    } else if (action === 'remove-row') {
      button.addEventListener('click', removeRow);
    } else if (action === 'export') {
      button.addEventListener('click', exportTable);
    }
  });

  bindFormulaRecalculation(table);
  recalculateTable(table);
};

export const initCarbonTables = () => {
  document.querySelectorAll('table.emisiones-table').forEach((table) => {
    setupTableActions(table);
  });
};
