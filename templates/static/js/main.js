// Application entry point – initialises all modules on DOMContentLoaded.
import { setApiBase } from './state.js';
import {
  hydrateAllTables,
  initTableDataLoaders,
} from './modules/loaders.js?v=20260427a';
import { initCarbonTables } from './modules/calculations.js?v=20260427a';
import { initDataEntryForm } from './modules/forms.js';
import { initDownloadButton } from './modules/download.js';
import { initNavigation } from './modules/navigation.js';
import { initOfficialInventory } from './modules/officialInventory.js';

document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  if (!body) {
    return;
  }
  setApiBase((body.dataset.apiBase || '/api/').replace(/\/$/, ''));

  hydrateAllTables();
  initCarbonTables();
  initTableDataLoaders();
  initDataEntryForm();
  initDownloadButton();
  initNavigation();
  initOfficialInventory();
});
