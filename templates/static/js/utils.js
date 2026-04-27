// Pure utility functions – no side effects, no DOM at module load time.

const monthFormatter = new Intl.DateTimeFormat('es', { month: 'long' });

export const normalise = (text) =>
  (text || '')
    .toString()
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s/]/g, '');

export const capitalise = (text) =>
  (text ? text.charAt(0).toUpperCase() + text.slice(1) : '');

export const formatPeriodLabel = (period) => {
  if (!period) {
    return '';
  }
  if (period.month) {
    const month = capitalise(
      monthFormatter.format(new Date(period.year, period.month - 1, 1))
    );
    return `${month} ${period.year}`;
  }
  return `Anual ${period.year}`;
};

export const formatNumber = (value, decimals = 3) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '';
  }
  return Number(value).toFixed(decimals);
};

export const toCamelCase = (text) =>
  (text || '')
    .toString()
    .toLowerCase()
    .split(/[_-]+/)
    .map((part, index) =>
      index === 0 ? part : part.charAt(0).toUpperCase() + part.slice(1)
    )
    .join('');

export const formatRecordContext = (record, extra) => {
  const parts = [];
  if (record.campus && record.campus.name) {
    parts.push(record.campus.name);
  }
  if (record.period) {
    parts.push(formatPeriodLabel(record.period));
  }
  if (extra) {
    parts.push(extra);
  }
  return parts.join(' · ');
};

export const clearElement = (element) => {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
};
