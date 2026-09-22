import type { ReactNode } from 'react';
import { ArrowDownRight, ArrowUpRight, Database, Download, Info, TriangleAlert } from 'lucide-react';
import { downloadCsv } from '@/lib/pipeline';

export function Panel({ children, className = '', testId }: { children: ReactNode; className?: string; testId?: string }) {
  return <section data-testid={testId} className={`rounded-xl border border-card-border bg-card shadow-[var(--shadow-sm)] ${className}`}>{children}</section>;
}

export function SectionHeading({ eyebrow, title, detail, action }: { eyebrow?: string; title: string; detail?: string; action?: ReactNode }) {
  return <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border/80 px-5 py-4">
    <div>
      {eyebrow && <p className="mb-1 font-mono text-[10px] uppercase tracking-[0.16em] text-primary">{eyebrow}</p>}
      <h2 className="font-display text-[17px] font-semibold tracking-tight">{title}</h2>
      {detail && <p className="mt-1 text-[12px] text-muted-foreground">{detail}</p>}
    </div>
    {action}
  </div>;
}

export function LoadingBlock({ rows = 4, height = 'h-10' }: { rows?: number; height?: string }) {
  return <div data-testid="status-loading" className="space-y-2 p-5" aria-label="Loading data">
    {Array.from({ length: rows }).map((_, index) => <div key={index} className={`${height} animate-pulse rounded-lg bg-muted/75`} />)}
  </div>;
}

export function EmptyState({ title, description, icon = 'data', action }: { title: string; description: string; icon?: 'data' | 'warning'; action?: ReactNode }) {
  return <div data-testid="status-empty" className="flex min-h-[190px] flex-col items-center justify-center px-6 py-10 text-center">
    <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl border border-border bg-muted text-muted-foreground">{icon === 'warning' ? <TriangleAlert className="h-5 w-5" /> : <Database className="h-5 w-5" />}</div>
    <h3 className="font-display text-[15px] font-semibold">{title}</h3>
    <p className="mt-1 max-w-sm text-[12px] leading-relaxed text-muted-foreground">{description}</p>
    {action && <div className="mt-4">{action}</div>}
  </div>;
}

export function ErrorState({ onRetry }: { onRetry: () => void }) {
  return <div data-testid="status-error" className="flex min-h-[190px] flex-col items-center justify-center px-6 text-center">
    <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl border border-destructive/25 bg-destructive/10 text-destructive"><TriangleAlert className="h-5 w-5" /></div>
    <h3 className="font-display text-[15px] font-semibold">Source unavailable</h3>
    <p className="mt-1 max-w-sm text-[12px] text-muted-foreground">The reporting view did not respond. Retry without changing any model inputs.</p>
    <button type="button" data-testid="button-retry" onClick={onRetry} className="mt-4 rounded-lg bg-primary px-3 py-2 text-[12px] font-semibold text-primary-foreground">Retry query</button>
  </div>;
}

export function Delta({ value, inverse = false }: { value: number | null | undefined; inverse?: boolean }) {
  if (value === null || value === undefined) {
    return <span data-testid="text-delta" className="font-mono text-[11px] text-muted-foreground">—</span>;
  }
  const positive = inverse ? value < 0 : value > 0;
  const neutral = value === 0;
  return <span data-testid="text-delta" className={`inline-flex items-center gap-1 font-mono text-[11px] ${neutral ? 'text-muted-foreground' : positive ? 'text-emerald-700 dark:text-emerald-400' : 'text-destructive'}`}>
    {!neutral && (positive ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />)}
    {value > 0 ? '+' : ''}{value.toFixed(1)}%
  </span>;
}

export function ExportButton({ filename, rows }: { filename: string; rows: Array<Record<string, unknown>> }) {
  return <button type="button" data-testid={`button-export-${filename.replace('.csv', '')}`} disabled={!rows.length} onClick={() => downloadCsv(filename, rows)} className="inline-flex items-center gap-1.5 rounded-md border border-border bg-background px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-muted-foreground transition-colors hover:border-primary/50 hover:text-primary disabled:cursor-not-allowed disabled:opacity-40"><Download className="h-3 w-3" />CSV</button>;
}

export function SourceNote({ children }: { children: ReactNode }) {
  return <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground"><Info className="h-3 w-3" />{children}</span>;
}
