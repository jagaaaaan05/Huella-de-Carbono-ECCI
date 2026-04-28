import { catalogCache, getApiBase } from '../../state.js';
import { fetchCatalog } from '../api.js';
import { extractErrorMessage } from './errors.js';

const buildDateRangeForPeriod = (year, month) => {
  if (month) {
    const lastDay = new Date(year, month, 0).getDate();
    const mm = String(month).padStart(2, '0');
    return {
      start_date: `${year}-${mm}-01`,
      end_date: `${year}-${mm}-${String(lastDay).padStart(2, '0')}`,
    };
  }

  return {
    start_date: `${year}-01-01`,
    end_date: `${year}-12-31`,
  };
};

export const ensurePeriodOption = (select, period) => {
  if (!select || !period?.id) {
    return;
  }

  const value = `${period.id}`;
  let option = Array.from(select.options).find((item) => item.value === value);
  const label = period.month
    ? `${period.year} · ${String(period.month).padStart(2, '0')}`
    : `${period.year} · Anual`;

  if (!option) {
    option = document.createElement('option');
    option.value = value;
    option.textContent = label;
    const createOption = Array.from(select.options).find((item) => item.value === '__new__');
    if (createOption) {
      select.insertBefore(option, createOption);
    } else {
      select.appendChild(option);
    }
  } else {
    option.textContent = label;
  }
};

const ensurePeriodByYearMonth = async (yearRaw, monthRaw, getCsrfToken) => {
  const year = Number.parseInt(`${yearRaw || ''}`.trim(), 10);
  if (!Number.isInteger(year) || year < 2000 || year > 2100) {
    throw new Error('Ingresa un año válido entre 2000 y 2100 para crear el periodo.');
  }

  const monthCandidate = `${monthRaw || ''}`.trim();
  const month = monthCandidate ? Number.parseInt(monthCandidate, 10) : null;
  if (month !== null && (!Number.isInteger(month) || month < 1 || month > 12)) {
    throw new Error('El mes debe estar entre 1 y 12.');
  }

  const periods = await fetchCatalog('periods', { force: true });
  const existing = periods.find(
    (period) =>
      Number(period.year) === year && Number(period.month || 0) === Number(month || 0)
  );
  if (existing) {
    return existing;
  }

  const csrfToken = getCsrfToken();
  const dateRange = buildDateRangeForPeriod(year, month);
  const createResponse = await fetch(`${getApiBase()}/periods/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify({
      year,
      month,
      ...dateRange,
    }),
  });

  if (!createResponse.ok) {
    let message = `No pudimos crear el periodo (${createResponse.status}).`;
    try {
      const errorData = await createResponse.json();
      message = extractErrorMessage(errorData, message);
    } catch (jsonError) {
      console.error(jsonError);
    }
    throw new Error(message);
  }

  const period = await createResponse.json();
  catalogCache.delete('periods');
  return period;
};

export const ensurePeriodIdInPayload = async (
  payload,
  { periodYear, periodMonth, getCsrfToken }
) => {
  const nextPayload = { ...payload };
  const periodIdRaw = nextPayload.period_id;

  if (periodIdRaw && periodIdRaw !== '__new__') {
    const parsed = Number.parseInt(`${periodIdRaw}`, 10);
    if (Number.isInteger(parsed)) {
      nextPayload.period_id = parsed;
      return nextPayload;
    }
  }

  const yearCandidate = periodYear ?? nextPayload.period_year;
  const monthCandidate = periodMonth ?? nextPayload.period_month;

  if (periodIdRaw === '__new__' || yearCandidate) {
    const period = await ensurePeriodByYearMonth(
      yearCandidate,
      monthCandidate,
      getCsrfToken
    );
    nextPayload.period_id = period.id;
  }

  delete nextPayload.period_year;
  delete nextPayload.period_month;
  return nextPayload;
};

export const ensurePeriodIdForPayload = async (
  form,
  payload,
  { getCsrfToken }
) => {
  const periodSelect = form.elements.period_id;
  if (!periodSelect) {
    return payload;
  }

  const selectedPeriodPayload = await ensurePeriodIdInPayload(payload, {
    periodYear: form.elements.period_year?.value,
    periodMonth: form.elements.period_month?.value,
    getCsrfToken,
  });

  const selectedPeriod = await fetchCatalog('periods', { force: true }).then((items) =>
    items.find((item) => item.id === selectedPeriodPayload.period_id)
  );
  if (!selectedPeriod) {
    return selectedPeriodPayload;
  }

  ensurePeriodOption(periodSelect, selectedPeriod);
  periodSelect.value = `${selectedPeriod.id}`;

  const officialPeriodSelect = document.getElementById('official-period');
  if (officialPeriodSelect) {
    ensurePeriodOption(officialPeriodSelect, selectedPeriod);
  }

  return selectedPeriodPayload;
};

export const attachPeriodBuilder = (wrapper, periodSelect) => {
  const periodBuilder = document.createElement('div');
  periodBuilder.className = 'period-builder';
  periodBuilder.hidden = true;

  const yearField = document.createElement('div');
  yearField.className = 'form-field';
  const yearLabel = document.createElement('label');
  yearLabel.setAttribute('for', 'field-period_year');
  yearLabel.textContent = 'Año del periodo';
  const yearInput = document.createElement('input');
  yearInput.type = 'number';
  yearInput.name = 'period_year';
  yearInput.id = 'field-period_year';
  yearInput.min = '2000';
  yearInput.max = '2100';
  yearInput.step = '1';
  yearInput.value = `${new Date().getFullYear()}`;
  yearField.appendChild(yearLabel);
  yearField.appendChild(yearInput);

  const monthField = document.createElement('div');
  monthField.className = 'form-field';
  const monthLabel = document.createElement('label');
  monthLabel.setAttribute('for', 'field-period_month');
  monthLabel.textContent = 'Mes (opcional)';
  const monthSelect = document.createElement('select');
  monthSelect.name = 'period_month';
  monthSelect.id = 'field-period_month';
  monthSelect.classList.add('form-select');
  const annualOption = document.createElement('option');
  annualOption.value = '';
  annualOption.textContent = 'Anual';
  monthSelect.appendChild(annualOption);

  for (let month = 1; month <= 12; month += 1) {
    const option = document.createElement('option');
    option.value = `${month}`;
    option.textContent = `${String(month).padStart(2, '0')}`;
    monthSelect.appendChild(option);
  }

  monthField.appendChild(monthLabel);
  monthField.appendChild(monthSelect);

  periodBuilder.appendChild(yearField);
  periodBuilder.appendChild(monthField);
  wrapper.appendChild(periodBuilder);

  periodSelect.addEventListener('change', () => {
    periodBuilder.hidden = periodSelect.value !== '__new__';
  });
};
