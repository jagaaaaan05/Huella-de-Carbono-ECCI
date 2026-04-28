// Form rendering, submission, and CRUD record management.
import { clearElement } from '../utils.js';
import { catalogCache, getApiBase } from '../state.js';
import { RECORD_CONFIG } from '../config/records.js';
import { TABLE_DATA_CONFIG } from '../config/tables.js';
import { SELECT_SOURCE_CONFIG } from '../config/catalogs.js';
import { fetchCatalog } from './api.js';
import { populateTableFromRecords } from './loaders.js';
import { initBulkUpload } from './forms/bulkUpload.js';
import { extractErrorMessage } from './forms/errors.js';
import {
  attachPeriodBuilder,
  ensurePeriodIdForPayload,
  ensurePeriodIdInPayload,
  ensurePeriodOption,
} from './forms/periods.js';

const FACTOR_SOURCE_BY_RECORD_KEY = {
  electricity: 'EI1',
  naturalGas: 'ED1',
  fuelStationary: 'ED1',
  fuelMobile: 'ED2',
  extinguisherRefill: 'ED4',
  waste: 'EI4',
  paper: 'EI3',
  flights: 'EI2',
  fieldPractice: 'EI2',
  groundTransport: 'EI2',
  lodging: 'EI2',
};

const filterOptionsByRecordKey = (items, sourceKey, recordKey, fieldName) => {
  if (sourceKey !== 'emissionFactors' || fieldName !== 'emission_factor_id') {
    return items;
  }
  const sourceCode = FACTOR_SOURCE_BY_RECORD_KEY[recordKey];
  if (!sourceCode) {
    return items;
  }
  return items.filter((item) => item.source_code === sourceCode);
};

export const getCsrfToken = () => {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta && meta.content) {
    return meta.content;
  }
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
};

const postRecord = async (endpoint, payload, csrfToken) => {
  const response = await fetch(`${getApiBase()}/${endpoint}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (response.ok) {
    return response;
  }

  let message = `No pudimos guardar el dato (${response.status}).`;
  try {
    const errorData = await response.json();
    message = extractErrorMessage(errorData, message);
  } catch (jsonError) {
    console.error(jsonError);
  }
  throw new Error(message);
};

export const populateSelectFromSource = async (
  select,
  sourceKey,
  fieldConfig = {},
  context = {},
) => {
  const source = SELECT_SOURCE_CONFIG[sourceKey];
  if (!source) {
    return;
  }

  let items = [];
  try {
    items = await fetchCatalog(source.endpoint);
  } catch (error) {
    console.error(error);
    return;
  }

  items = filterOptionsByRecordKey(
    items,
    sourceKey,
    context.recordKey,
    fieldConfig.name,
  );

  const previousValue = select.value;
  while (select.options.length > 1) {
    select.remove(1);
  }

  const labelFn = fieldConfig.optionLabel || source.label;
  const valueFn = fieldConfig.optionValue || source.value;

  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = `${valueFn(item)}`;
    option.textContent = labelFn(item);
    select.appendChild(option);
  });

  if (fieldConfig.name === 'period_id') {
    const createOption = document.createElement('option');
    createOption.value = '__new__';
    createOption.textContent = 'Crear un periodo nuevo...';
    select.appendChild(createOption);

    const currentOfficialPeriod = document.getElementById('official-period')?.value;
    if (currentOfficialPeriod && Array.from(select.options).some((option) => option.value === currentOfficialPeriod)) {
      select.value = currentOfficialPeriod;
      return;
    }
  }

  if (fieldConfig.name === 'campus_id') {
    const currentCampus = document.getElementById('official-campus')?.value;
    if (currentCampus && Array.from(select.options).some((option) => option.value === currentCampus)) {
      select.value = currentCampus;
      return;
    }
  }

  if (fieldConfig.default !== undefined) {
    const defaultValue = `${fieldConfig.default}`;
    const defaultOption = Array.from(select.options).find(
      (option) => option.value === defaultValue
    );
    if (defaultOption) {
      defaultOption.defaultSelected = true;
      select.value = defaultValue;
      return;
    }
  }

  if (previousValue) {
    const exists = items.some((item) => `${valueFn(item)}` === previousValue);
    select.value = exists ? previousValue : '';
  } else {
    select.selectedIndex = 0;
  }
};

export const renderRecordForm = async (recordKey) => {
  const form = document.getElementById('recordForm');
  const selector = document.getElementById('recordType');
  if (!form || !selector) {
    return;
  }

  const config = RECORD_CONFIG[recordKey];
  const fieldsWrapper = form.querySelector('[data-form-fields]');
  const status = form.querySelector('.form-status');

  if (!config) {
    form.hidden = true;
    form.dataset.endpoint = '';
    form.dataset.recordKey = '';
    if (fieldsWrapper) {
      clearElement(fieldsWrapper);
    }
    if (status) {
      status.textContent = '';
      status.classList.remove('success', 'error');
    }
    return;
  }

  form.hidden = false;
  form.dataset.endpoint = config.endpoint;
  form.dataset.recordKey = recordKey;

  if (status) {
    status.textContent = '';
    status.classList.remove('success', 'error');
  }

  if (fieldsWrapper) {
    clearElement(fieldsWrapper);
    fieldsWrapper.classList.toggle('two-cols', (config.fields || []).length > 3);
  }

  const asyncTasks = [];

  (config.fields || []).forEach((field) => {
    if (!fieldsWrapper) {
      return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'form-field';

    if (field.type === 'checkbox') {
      const label = document.createElement('label');
      label.className = 'checkbox-field';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.name = field.name;
      input.id = `field-${field.name}`;
      if (field.default) {
        input.checked = true;
        input.defaultChecked = true;
      }
      label.appendChild(input);
      const span = document.createElement('span');
      span.textContent = field.label;
      label.appendChild(span);
      wrapper.appendChild(label);
    } else {
      const label = document.createElement('label');
      label.setAttribute('for', `field-${field.name}`);
      label.textContent = field.label;
      wrapper.appendChild(label);

      let input;

      if (field.type === 'select') {
        input = document.createElement('select');
        input.name = field.name;
        input.id = `field-${field.name}`;
        input.classList.add('form-select');
        if (field.required) {
          input.required = true;
        }
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = field.placeholder || 'Selecciona una opción';
        input.appendChild(placeholder);
        if (field.source) {
          asyncTasks.push(
            populateSelectFromSource(input, field.source, field, { recordKey })
          );
        }

        if (field.name === 'period_id') {
          attachPeriodBuilder(wrapper, input);
        }
      } else {
        input = document.createElement('input');
        input.type = field.type || 'text';
        input.name = field.name;
        input.id = `field-${field.name}`;
        if (field.required) {
          input.required = true;
        }
        if (field.placeholder) {
          input.placeholder = field.placeholder;
        }
        if (field.step) {
          input.step = field.step;
        }
        if (field.min !== undefined) {
          input.min = field.min;
        }
        if (field.max !== undefined) {
          input.max = field.max;
        }
        if (field.default !== undefined) {
          input.value = field.default;
          input.defaultValue = field.default;
        }
      }

      wrapper.appendChild(input);
    }

    fieldsWrapper.appendChild(wrapper);
  });

  try {
    await Promise.all(asyncTasks);
  } catch (error) {
    console.error(error);
  }
};

const updateRecordSelector = (recordKey) => {
  const selector = document.getElementById('recordType');
  const form = document.getElementById('recordForm');
  if (!selector || !form) {
    return;
  }

  if (!recordKey) {
    selector.value = '';
    form.hidden = true;
    form.dataset.endpoint = '';
    form.dataset.recordKey = '';
    form.reset();
    const status = form.querySelector('.form-status');
    const fieldsWrapper = form.querySelector('[data-form-fields]');
    if (fieldsWrapper) {
      clearElement(fieldsWrapper);
      fieldsWrapper.classList.remove('two-cols');
    }
    if (status) {
      status.textContent = '';
      status.classList.remove('success', 'error');
    }
    return;
  }

  if (selector.value === recordKey && !form.hidden) {
    return;
  }

  selector.value = recordKey;
  renderRecordForm(recordKey).catch((error) => console.error(error));
};

export const refreshTablesForRecord = (recordKey) => {
  document.querySelectorAll(`table[data-record-key="${recordKey}"]`).forEach((table) => {
    const config = TABLE_DATA_CONFIG[recordKey];
    if (!config) {
      return;
    }
    populateTableFromRecords(table, config).catch((error) => console.error(error));
  });
};

export const submitRecordForm = async (event) => {
  event.preventDefault();

  const form = event.currentTarget;
  const status = form.querySelector('.form-status');
  const endpoint = form.dataset.endpoint;
  const recordKey = form.dataset.recordKey;
  const config = RECORD_CONFIG[recordKey];

  if (!endpoint || !config || !config.fields) {
    return;
  }
  if (!form.reportValidity()) {
    return;
  }

  if (status) {
    status.textContent = '';
    status.classList.remove('success', 'error');
  }

  let payload = {};

  config.fields.forEach((field) => {
    const input = form.elements[field.name];
    if (!input) {
      return;
    }
    if (field.type === 'checkbox') {
      payload[field.name] = input.checked;
      return;
    }
    const value = input.value.trim();
    if (!value) {
      if (field.required) {
        payload[field.name] = value;
      }
      return;
    }
    if (field.cast === 'int') {
      const parsed = parseInt(value, 10);
      if (!Number.isNaN(parsed)) {
        payload[field.name] = parsed;
      }
      return;
    }
    if (field.cast === 'float' || field.type === 'number') {
      const parsed = parseFloat(value);
      if (!Number.isNaN(parsed)) {
        payload[field.name] = parsed;
      }
      return;
    }
    payload[field.name] = value;
  });

  const csrfToken = getCsrfToken();
  form.classList.add('loading');
  if (status) {
    status.textContent = 'Guardando información...';
  }

  try {
    payload = await ensurePeriodIdForPayload(form, payload, { getCsrfToken });
    await postRecord(endpoint, payload, csrfToken);

    form.reset();
    catalogCache.delete(endpoint);

    if (status) {
      status.textContent = 'Dato guardado correctamente.';
      status.classList.remove('error');
      status.classList.add('success');
    }
    if (recordKey) {
      refreshTablesForRecord(recordKey);
    }
  } catch (error) {
    console.error(error);
    if (status) {
      status.textContent = error.message;
      status.classList.remove('success');
      status.classList.add('error');
    }
  } finally {
    form.classList.remove('loading');
  }
};

export const initDataEntryForm = () => {
  const selector = document.getElementById('recordType');
  const form = document.getElementById('recordForm');
  if (!selector || !form) {
    return;
  }

  selector.addEventListener('change', () => {
    const value = selector.value;
    if (!value) {
      form.hidden = true;
      form.dataset.endpoint = '';
      form.dataset.recordKey = '';
      form.reset();
      const status = form.querySelector('.form-status');
      if (status) {
        status.textContent = '';
        status.classList.remove('success', 'error');
      }
      return;
    }
    renderRecordForm(value).catch((error) => console.error(error));
  });

  const resetButton = form.querySelector('[data-reset]');
  if (resetButton) {
    resetButton.addEventListener('click', () => {
      form.reset();
      const status = form.querySelector('.form-status');
      if (status) {
        status.textContent = '';
        status.classList.remove('success', 'error');
      }
    });
  }

  form.addEventListener('submit', submitRecordForm);

  document.addEventListener('record-context-change', (event) => {
    updateRecordSelector(event.detail?.recordKey || '');
  });

  updateRecordSelector(selector.value || '');
  initBulkUpload({
    getCsrfToken,
    ensurePeriodIdInPayload: (payload, options = {}) =>
      ensurePeriodIdInPayload(payload, {
        ...options,
        getCsrfToken,
      }),
    postRecord,
    refreshTablesForRecord,
  });
};
