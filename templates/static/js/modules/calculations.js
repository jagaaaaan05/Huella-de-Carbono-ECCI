// Table actions engine: export and optional local row management.
import { hydrateTable, resetRowInputs } from './loaders.js';

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

  const isBackendOfficial = table.dataset.factorPolicy === 'backend-official';

  const calculateButton = actions.querySelector('[data-carbon-action="calculate"]');
  if (calculateButton) {
    calculateButton.remove();
  }

  if (isBackendOfficial) {
    actions.querySelector('[data-carbon-action="add-row"]')?.remove();
    actions.querySelector('[data-carbon-action="remove-row"]')?.remove();

    // Operational tables are read-only; official records must be entered via API forms.
    table.querySelectorAll('tbody input, tbody select').forEach((field) => {
      if (field.tagName === 'SELECT') {
        field.disabled = true;
      } else {
        field.readOnly = true;
      }
    });
  }

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
};

export const initCarbonTables = () => {
  document.querySelectorAll('table.emisiones-table').forEach((table) => {
    setupTableActions(table);
  });
};
