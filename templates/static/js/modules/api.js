// API fetch helpers – thin wrappers around fetch() with caching.
import { catalogCache, getApiBase } from '../state.js';

export const fetchCatalog = async (endpoint, { force = false } = {}) => {
  if (!endpoint) {
    return [];
  }

  if (!force && catalogCache.has(endpoint)) {
    return catalogCache.get(endpoint);
  }

  const response = await fetch(`${getApiBase()}/${endpoint}/`, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(
      `No se pudo obtener la información de ${endpoint} (${response.status})`
    );
  }

  const data = await response.json();
  const results = Array.isArray(data) ? data : data.results || [];
  catalogCache.set(endpoint, results);
  return results;
};

export const populateSelectElement = (select, options, config) => {
  if (!select) {
    return;
  }

  const previousValue = select.value;
  select.innerHTML = '';

  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Seleccione';
  select.appendChild(placeholder);

  options.forEach((item) => {
    const option = document.createElement('option');
    option.value = `${item[config.valueField]}`;
    option.textContent = config.label(item);
    select.appendChild(option);
  });

  if (previousValue) {
    const exists = options.some((item) => `${item[config.valueField]}` === previousValue);
    select.value = exists ? previousValue : '';
  }
};
