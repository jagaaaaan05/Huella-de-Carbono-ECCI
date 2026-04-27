// Shared mutable state: API base URL and catalog cache.
export const catalogCache = new Map();

let _apiBase = '/api';

export const getApiBase = () => _apiBase;

export const setApiBase = (base) => {
  _apiBase = base;
};
