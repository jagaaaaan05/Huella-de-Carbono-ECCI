// API fetch helpers – thin wrappers around fetch() with caching.
import { catalogCache, getApiBase } from '../state.js';

const buildCatalogKey = (endpoint, queryParams = {}) => {
  const params = new URLSearchParams();
  Object.entries(queryParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}` !== '') {
      params.set(key, `${value}`);
    }
  });
  const query = params.toString();
  return query ? `${endpoint}?${query}` : endpoint;
};

export const fetchCatalog = async (
  endpoint,
  { force = false, queryParams = {} } = {}
) => {
  if (!endpoint) {
    return [];
  }

  const catalogKey = buildCatalogKey(endpoint, queryParams);

  if (!force && catalogCache.has(catalogKey)) {
    return catalogCache.get(catalogKey);
  }

  const query = catalogKey.includes('?') ? catalogKey.slice(catalogKey.indexOf('?')) : '';

  const response = await fetch(`${getApiBase()}/${endpoint}/${query}`, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(
      `No se pudo obtener la información de ${endpoint} (${response.status})`
    );
  }

  const data = await response.json();
  const results = Array.isArray(data) ? data : data.results || [];
  catalogCache.set(catalogKey, results);
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
  placeholder.textContent = 'Selecciona una opción';
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
