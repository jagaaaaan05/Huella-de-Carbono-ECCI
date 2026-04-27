import { getApiBase } from '../state.js';
import { fetchCatalog } from './api.js';
import { formatNumber, formatPeriodLabel } from '../utils.js';

const DIRECT_PREFIX = 'ED';
const INDIRECT_PREFIX = 'EI';
const REMOVALS_CODE = 'RE1';

const setText = (id, value) => {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value;
  }
};

const setWidth = (id, percent) => {
  const element = document.getElementById(id);
  if (element) {
    element.style.width = `${Math.max(0, Math.min(100, percent))}%`;
  }
};

const renderSourceBreakdown = (sources = []) => {
  const container = document.getElementById('official-source-breakdown');
  if (!container) {
    return;
  }

  if (!sources.length) {
    container.innerHTML = '<p class="muted">No hay resultados para mostrar.</p>';
    return;
  }

  const rows = sources
    .map((source) => {
      const warnings = source.warnings?.length || 0;
      const warningText = warnings ? `<span class="source-warning">${warnings} advertencia(s)</span>` : '';
      return `
        <article class="source-item">
          <div>
            <strong>${source.source_name}</strong>
            <small>${source.source_code}</small>
          </div>
          <div>
            <span>${formatNumber(source.total_tco2e)} tCO₂e</span>
            <small>incertidumbre: +/- ${formatNumber(source.uncertainty_pct)}%</small>
            ${warningText}
          </div>
        </article>
      `;
    })
    .join('');

  container.innerHTML = `<div class="source-breakdown-list">${rows}</div>`;
};

const renderRunHistory = (runs = []) => {
  const container = document.getElementById('official-run-history');
  if (!container) {
    return;
  }
  if (!runs.length) {
    container.innerHTML = '<p class="muted">No hay corridas históricas para los filtros seleccionados.</p>';
    return;
  }

  const html = runs
    .map((run) => {
      const campus = run.campus?.name || 'Todas las sedes';
      const period = run.period ? formatPeriodLabel(run.period) : `Periodo ${run.period_id || ''}`;
      return `
        <article class="history-item">
          <div class="history-item-head">
            <div>
              <strong>Run #${run.id}</strong>
              <small>${period} · ${campus}</small>
            </div>
            <small>${new Date(run.created_at).toLocaleString('es-CO')}</small>
          </div>
          <div class="history-item-grid">
            <div class="history-metric"><span>Bruto</span><strong>${formatNumber(run.gross_tco2e)} tCO₂e</strong></div>
            <div class="history-metric"><span>Remociones</span><strong>${formatNumber(Math.abs(run.removals_tco2e || 0))} tCO₂e</strong></div>
            <div class="history-metric"><span>Neto</span><strong>${formatNumber(run.net_tco2e)} tCO₂e</strong></div>
            <div class="history-metric"><span>Incertidumbre</span><strong>+/- ${formatNumber(run.uncertainty_pct)}%</strong></div>
          </div>
        </article>
      `;
    })
    .join('');

  container.innerHTML = html;
};

const loadRunHistory = async () => {
  const periodSelect = document.getElementById('official-period');
  const campusSelect = document.getElementById('official-campus');
  const historyContainer = document.getElementById('official-run-history');
  if (!historyContainer) {
    return;
  }

  const params = new URLSearchParams({ ordering: '-created_at' });
  if (periodSelect?.value) {
    params.set('period_id', periodSelect.value);
  }
  if (campusSelect?.value) {
    params.set('campus_id', campusSelect.value);
  }

  try {
    const response = await fetch(`${getApiBase()}/calculation-runs-history/?${params.toString()}`, {
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`No fue posible cargar histórico (${response.status}).`);
    }
    const data = await response.json();
    const runs = Array.isArray(data) ? data : data.results || [];
    renderRunHistory(runs.slice(0, 20));
  } catch (error) {
    console.error(error);
    historyContainer.innerHTML = `<p class="muted">${error.message}</p>`;
  }
};

const updateHuellaWidgets = (payload) => {
  const sources = payload.sources || [];
  const totals = payload.totals || {};

  const direct = sources
    .filter((source) => source.source_code?.startsWith(DIRECT_PREFIX))
    .reduce((acc, source) => acc + (source.total_tco2e || 0), 0);
  const indirect = sources
    .filter((source) => source.source_code?.startsWith(INDIRECT_PREFIX))
    .reduce((acc, source) => acc + (source.total_tco2e || 0), 0);
  const removals = Math.abs(
    sources
      .filter((source) => source.source_code === REMOVALS_CODE)
      .reduce((acc, source) => acc + (source.total_tco2e || 0), 0)
  );

  setText('kpi-directas', formatNumber(direct));
  setText('kpi-indirectas', formatNumber(indirect));
  setText('kpi-remociones', formatNumber(removals));
  setText('kpi-neta', formatNumber(totals.net_tco2e || 0));

  setText('chart-directas', formatNumber(direct));
  setText('chart-indirectas', formatNumber(indirect));
  setText('chart-remociones', formatNumber(removals));

  const maxValue = Math.max(direct, indirect, removals, 0.0001);
  setWidth('bar-directas', (direct / maxValue) * 100);
  setWidth('bar-indirectas', (indirect / maxValue) * 100);
  setWidth('bar-remociones', (removals / maxValue) * 100);

  renderSourceBreakdown(sources);
};

const runOfficialCalculation = async () => {
  const periodSelect = document.getElementById('official-period');
  const campusSelect = document.getElementById('official-campus');
  const status = document.getElementById('official-calc-status');

  if (!periodSelect || !status) {
    return;
  }

  if (!periodSelect.value) {
    status.textContent = 'Selecciona un periodo para ejecutar el cálculo oficial.';
    return;
  }

  const payload = {
    period_id: Number(periodSelect.value),
    include_traces: false,
  };
  if (campusSelect && campusSelect.value) {
    payload.campus_id = Number(campusSelect.value);
  }

  status.textContent = 'Ejecutando cálculo oficial...';

  try {
    const response = await fetch(`${getApiBase()}/calculation-runs/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`No fue posible calcular inventario (${response.status}).`);
    }

    const result = await response.json();
    updateHuellaWidgets(result);
    await loadRunHistory();
    const warningCount = result.warnings?.length || 0;
    status.textContent = `Inventario oficial actualizado. Incertidumbre global: +/- ${formatNumber(result.totals?.uncertainty_pct || 0)}%${warningCount ? ` · ${warningCount} advertencia(s)` : ''}`;
  } catch (error) {
    console.error(error);
    status.textContent = error.message;
  }
};

const loadSelectOptions = async () => {
  const periodSelect = document.getElementById('official-period');
  const campusSelect = document.getElementById('official-campus');

  if (!periodSelect || !campusSelect) {
    return;
  }

  try {
    const [periods, campuses] = await Promise.all([
      fetchCatalog('periods', { force: true }),
      fetchCatalog('campus', { force: true }),
    ]);

    periodSelect.innerHTML = '<option value="">Seleccione periodo</option>';
    periods.forEach((period) => {
      const option = document.createElement('option');
      option.value = `${period.id}`;
      option.textContent = formatPeriodLabel(period);
      periodSelect.appendChild(option);
    });

    campusSelect.innerHTML = '<option value="">Todas las sedes</option>';
    campuses.forEach((campus) => {
      const option = document.createElement('option');
      option.value = `${campus.id}`;
      option.textContent = campus.name;
      campusSelect.appendChild(option);
    });

    if (periods.length) {
      periodSelect.value = `${periods[0].id}`;
    }
  } catch (error) {
    console.error(error);
    setText('official-calc-status', 'No fue posible cargar periodos/campus para el cálculo oficial.');
  }
};

export const initOfficialInventory = async () => {
  const runButton = document.getElementById('run-official-calculation');
  if (!runButton) {
    return;
  }

  await loadSelectOptions();
  await loadRunHistory();

  runButton.addEventListener('click', () => {
    runOfficialCalculation();
  });

  const refreshHistoryButton = document.getElementById('refresh-history');
  if (refreshHistoryButton) {
    refreshHistoryButton.addEventListener('click', () => {
      loadRunHistory();
    });
  }
};
