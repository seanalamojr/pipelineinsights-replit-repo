import type { PropRow } from '@workspace/api-client-react';

export function parseLocalDate(value: string) {
  const [year, month, day] = value.slice(0, 10).split('-').map(Number);
  return year && month && day ? new Date(year, month - 1, day) : new Date(value);
}

export function formatDate(value?: string, format: 'short' | 'long' = 'short') {
  if (!value) return '—';
  const date = parseLocalDate(value);
  return new Intl.DateTimeFormat('en-US', {
    month: format === 'long' ? 'long' : 'short',
    day: 'numeric',
    year: format === 'long' ? 'numeric' : undefined,
  }).format(date);
}

export function formatTimestamp(value?: string) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

export function formatEdge(value: number | null | undefined) {
  return value === null || value === undefined ? '—' : `${value > 0 ? '+' : ''}${value.toFixed(2)}`;
}

export function formatPropLabel(value: string | null | undefined) {
  if (!value) return '—';
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function formatPrice(value?: number) {
  if (value === undefined || value === null) return '—';
  return value > 0 ? `+${value}` : `${value}`;
}

export function formatMetric(value: number | null | undefined, kind: 'count' | 'decimal' | 'percent') {
  if (value === null || value === undefined) return '—';
  if (kind === 'count') return new Intl.NumberFormat('en-US').format(value);
  if (kind === 'decimal') return value.toFixed(2);
  return `${(value <= 1 ? value * 100 : value).toFixed(1)}%`;
}

export function rowKey(row: PropRow, index: number) {
  return `${row.playerId ?? row.player}-${row.eventDate}-${row.propType}-${row.book}-${index}`;
}

export function downloadCsv(filename: string, rows: Array<Record<string, unknown>>) {
  if (!rows.length) return;
  const headers = Object.keys(rows[0]);
  const escape = (value: unknown) => `"${String(value ?? '').replaceAll('"', '""')}"`;
  const csv = [headers.join(','), ...rows.map((row) => headers.map((header) => escape(row[header])).join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
