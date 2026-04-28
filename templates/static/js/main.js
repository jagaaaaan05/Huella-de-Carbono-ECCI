// Application entry point – initialises all modules on DOMContentLoaded.
import { setApiBase } from './state.js';
import {
  hydrateAllTables,
  initTableDataLoaders,
} from './modules/loaders.js?v=20260428l';
import { initCarbonTables } from './modules/calculations.js?v=20260428l';
import { initDownloadButton } from './modules/download.js';
import { initNavigation } from './modules/navigation.js?v=20260428l';
import { initOfficialInventory } from './modules/officialInventory.js?v=20260428l';
import { initDataEntryForm } from './modules/forms.js?v=20260428l';

document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  if (!body) {
    return;
  }
  setApiBase((body.dataset.apiBase || '/api/').replace(/\/$/, ''));

  hydrateAllTables();
  initCarbonTables();
  initTableDataLoaders();
  initDownloadButton();
  initNavigation();
  initOfficialInventory();
  initDataEntryForm();
});
