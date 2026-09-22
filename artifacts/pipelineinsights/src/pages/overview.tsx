import { useMemo } from 'react';
import { useGetPipelineOverview } from '@workspace/api-client-react';
import { Activity, ArrowRight, CalendarDays, CheckCircle2, Clock3, ExternalLink, Layers3, ShieldCheck, Target, Zap } from 'lucide-react';
import { Link } from 'wouter';
import { Delta, EmptyState, ErrorState, ExportButton, LoadingBlock, Panel, SectionHeading, SourceNote } from '@/components/dashboard-ui';
import { formatDate, formatEdge, formatMetric, formatPrice, formatPropLabel, formatTimestamp, rowKey } from '@/lib/pipeline';

function MetricCard({ label, value, delta, hint, icon: Icon, kind, inverse }: { label: string; value: number | null; delta: number | null; hint: string; icon: typeof Target; kind: 'count' | 'decimal' | 'percent'; inverse?: boolean }) {
  return <Panel className="relative overflow-hidden p-5" testId={`card-metric-${label.toLowerCase().replaceAll(' ', '-')}`}>
    <div className="absolute right-4 top-4 text-primary/35"><Icon className="h-5 w-5" /></div>
    <p className="font-mono text-[10px] uppercase tracking-[0.13em] text-muted-foreground">{label}</p>
    <p data-testid={`value-metric-${label.toLowerCase().replaceAll(' ', '-')}`} className="mt-3 font-display text-[30px] font-semibold tracking-tight text-primary tabular-nums">{formatMetric(value, kind)}</p>
    <div className="mt-2 flex items-center gap-2"><Delta value={delta} inverse={inverse} /><span className="text-[11px] text-muted-foreground">{hint}</span></div>
  </Panel>;
}

export default function OverviewPage() {
  const query = useGetPipelineOverview();
  const overview = query.data;
  const loading = query.isLoading || query.isFetching;
  const edgeRows = useMemo(() => (overview?.topEdges ?? []).map((row) => ({ player: row.player, market: row.propLabel || formatPropLabel(row.propType), side: row.side, normalized_edge: formatEdge(row.normalizedEdge), raw_edge: formatEdge(row.edge), projection: row.projection, line: row.line, book: row.book, model: row.modelVersion, demo: row.isDemo ? 'yes' : 'no' })), [overview?.topEdges]);
  const lastRefresh = query.dataUpdatedAt ? formatTimestamp(new Date(query.dataUpdatedAt).toISOString()) : null;

  return <div className="space-y-7">
    <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
      <div>
        <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-primary">Decision surface / 01</p>
        <h1 className="font-display text-[34px] font-semibold leading-none tracking-[-0.045em] sm:text-[42px]">Good morning, analyst.</h1>
        <p className="mt-3 max-w-[650px] text-[14px] leading-relaxed text-muted-foreground">A compact read on the active prop board, model signal, and what is ready to inspect before today&apos;s slate.</p>
        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2"><SourceNote>{overview?.sources?.length ?? 0} registered sources</SourceNote>{lastRefresh && <SourceNote>Refreshed {lastRefresh}</SourceNote>}{overview?.demoData && <span data-testid="badge-demo-overview" className="rounded-md bg-accent/15 px-2 py-1 font-mono text-[10px] uppercase tracking-[0.1em] text-accent-foreground">Demo records — not live odds</span>}</div>
      </div>
      <div className="flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-[12px] text-primary"><ShieldCheck className="h-4 w-4" /><span>{overview?.sources?.length ?? 0} source records reported for this snapshot.</span></div>
    </div>

    {query.isError ? <Panel><ErrorState onRetry={() => void query.refetch()} /></Panel> : loading ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">{Array.from({ length: 5 }).map((_, index) => <Panel key={index} className="p-5"><LoadingBlock rows={2} height="h-7" /></Panel>)}</div> : overview ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
       <MetricCard label="Active prop markets" value={overview.activePropMarkets.value} delta={overview.activePropMarkets.delta} hint="current snapshot" icon={Layers3} kind="count" />
       <MetricCard label="Predictions generated" value={overview.predictionsGenerated.value} delta={overview.predictionsGenerated.delta} hint="latest checkpoint" icon={Zap} kind="count" />
       <MetricCard label="Average RMSE" value={overview.avgRmse.value} delta={overview.avgRmse.delta} hint="backtest pending" icon={Target} kind="decimal" inverse />
       <MetricCard label="Value edges found" value={overview.valueEdgesFound.value} delta={overview.valueEdgesFound.delta} hint="above threshold" icon={ArrowRight} kind="count" />
       <MetricCard label="Model agreement" value={overview.modelAgreement.value} delta={overview.modelAgreement.delta} hint="backtest pending" icon={CheckCircle2} kind="percent" />
    </div> : <Panel><EmptyState title="No overview snapshot" description="The reporting view has not produced an overview yet." /></Panel>}

     {overview && !loading && <Panel className="overflow-hidden">
        <SectionHeading eyebrow="Model health" title="Checkpoint health" detail="Reported by the pipeline snapshot; no scores are recomputed in the client." action={<div className="inline-flex items-center gap-2 rounded-md bg-primary/10 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-primary"><Activity className="h-3.5 w-3.5" />{overview.modelAgreement.value === null ? 'Backtest pending' : overview.modelAgreement.value >= 0.7 ? 'Stable signal' : 'Review signal'}</div>} />
       <div className="grid gap-0 divide-y divide-border/70 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
         <div className="px-5 py-4"><p className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">Agreement</p><div className="mt-2 flex items-baseline gap-2"><span data-testid="value-health-agreement" className="font-display text-2xl font-semibold tabular-nums text-primary">{formatMetric(overview.modelAgreement.value, 'percent')}</span><Delta value={overview.modelAgreement.delta} /></div><p className="mt-1 text-[11px] text-muted-foreground">ensemble consensus across active rows</p></div>
         <div className="px-5 py-4"><p className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">Average RMSE</p><div className="mt-2 flex items-baseline gap-2"><span data-testid="value-health-rmse" className="font-display text-2xl font-semibold tabular-nums">{formatMetric(overview.avgRmse.value, 'decimal')}</span><Delta value={overview.avgRmse.delta} inverse /></div><p className="mt-1 text-[11px] text-muted-foreground">lower is better · latest checkpoint</p></div>
          <div className="px-5 py-4"><p className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">Snapshot integrity</p><div className="mt-2 flex items-center gap-2 font-display text-[15px] font-semibold"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary"><CheckCircle2 className="h-3.5 w-3.5" /></span>{overview.sources.length} source rows reported</div><p className="mt-1 text-[11px] text-muted-foreground">counts and timestamps come from the reporting snapshot</p></div>
       </div>
     </Panel>}

     <div className="grid gap-5 xl:grid-cols-[1.4fr_.9fr]">
       <Panel className="overflow-hidden">
        <SectionHeading eyebrow="Signal monitor" title="Top value edges" detail="Sorted by modeled edge. Open a row to validate the market context." action={<ExportButton filename="pipeline-top-edges.csv" rows={edgeRows} />} />
         {loading ? <LoadingBlock rows={5} /> : !overview?.topEdges?.length ? <EmptyState title="No qualifying edges" description="No markets cleared the configured value threshold in this snapshot." /> : <div className="overflow-x-auto"><table className="w-full min-w-[690px] text-left"><thead><tr className="border-b border-border/70 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground"><th className="px-5 py-3 font-medium">Player / market</th><th className="px-3 py-3 font-medium">Projection</th><th className="px-3 py-3 font-medium">Band</th><th className="px-3 py-3 font-medium">Normalized edge</th><th className="px-5 py-3 text-right font-medium">Source</th></tr></thead><tbody>{overview?.topEdges.map((row, index) => { const normalizedEdge = row.normalizedEdge ?? null; return <tr key={rowKey(row, index)} data-testid={`row-top-edge-${index}`} className="border-b border-border/60 last:border-0 transition-colors hover:bg-muted/35"><td className="px-5 py-3.5"><div className="flex items-center gap-3"><div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary font-display text-[12px] font-semibold text-secondary-foreground">{row.player.split(' ').map((part) => part[0]).join('').slice(0, 2)}</div><div><p className="text-[13px] font-semibold">{row.player}{row.isDemo && <span className="ml-2 rounded bg-accent/15 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-[0.08em] text-accent-foreground">Demo</span>}</p><p className="mt-0.5 text-[11px] text-muted-foreground">{row.propLabel || formatPropLabel(row.propType)} · {row.matchup}</p></div></div></td><td className="px-3 py-3.5 font-mono text-[13px] tabular-nums">{row.projection.toFixed(1)} <span className="text-muted-foreground">vs {row.line ?? '—'}</span></td><td className="px-3 py-3.5 font-mono text-[11px] text-muted-foreground">{row.lowerCi.toFixed(1)}–{row.upperCi.toFixed(1)}</td><td className="px-3 py-3.5"><span className={`rounded-md px-2 py-1 font-mono text-[12px] font-medium ${normalizedEdge !== null && normalizedEdge >= 0 ? 'bg-primary/10 text-primary' : 'bg-destructive/10 text-destructive'}`}>{formatEdge(normalizedEdge)}</span><p className="mt-1 text-[10px] text-muted-foreground">raw {formatEdge(row.edge)}</p></td><td className="px-5 py-3.5 text-right"><span className="font-mono text-[11px] text-muted-foreground">{row.book ?? '—'}</span><p className="mt-1 text-[10px] text-muted-foreground">{row.side ?? '—'} · {formatPrice(row.side === 'Over' ? row.overPrice : row.underPrice)}</p></td></tr>; })}</tbody></table></div>}
      </Panel>

      <Panel className="overflow-hidden">
        <SectionHeading eyebrow="Today" title="Match slate" detail="Events represented in the current source window." action={<CalendarDays className="h-4 w-4 text-muted-foreground" />} />
        {loading ? <LoadingBlock rows={4} /> : !overview?.todaysMatches?.length ? <EmptyState title="No matches in window" description="No scheduled matches were returned for today." /> : <div className="divide-y divide-border/70">{overview.todaysMatches.map((match, index) => <div key={`${match.matchup}-${index}`} data-testid={`card-match-${index}`} className="flex items-start justify-between gap-4 px-5 py-4"><div><p className="text-[13px] font-semibold">{match.matchup}</p><p className="mt-1 text-[11px] text-muted-foreground">{match.tournament} · {match.surface}</p></div><span className="shrink-0 font-mono text-[11px] text-muted-foreground">{formatDate(match.eventDate)}</span></div>)}</div>}
        <div className="border-t border-border/70 px-5 py-3"><Link href="/lines" data-testid="link-view-lines" className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-primary hover:underline">Inspect posted lines <ArrowRight className="h-3.5 w-3.5" /></Link></div>
      </Panel>
    </div>

    <Panel className="overflow-hidden">
      <SectionHeading eyebrow="Provenance" title="Source freshness" detail="Pipeline inputs that support this snapshot." action={<SourceNote>Updated with overview</SourceNote>} />
      {loading ? <LoadingBlock rows={3} /> : !overview?.sources?.length ? <EmptyState title="No source registry" description="No upstream source metadata was returned." /> : <div className="grid gap-3 p-5 md:grid-cols-2 xl:grid-cols-4">{overview.sources.map((source, index) => <div key={`${source.name}-${index}`} data-testid={`card-source-${index}`} className="rounded-lg border border-border/80 bg-background/45 p-4"><div className="flex items-center justify-between gap-2"><p className="text-[13px] font-semibold">{source.name}</p><span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 font-mono text-[10px] uppercase tracking-[0.08em] ${source.status === 'ready' ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400' : source.status === 'stale' ? 'bg-accent/15 text-accent-foreground' : 'bg-muted text-muted-foreground'}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{source.status}</span></div><div className="mt-4 flex items-end justify-between"><div><p className="font-display text-[22px] font-semibold tabular-nums">{source.recordCount.toLocaleString()}</p><p className="text-[10px] uppercase tracking-[0.1em] text-muted-foreground">records</p></div><div className="text-right"><p className="font-mono text-[11px] text-foreground/75">{source.freshness}</p><p className="mt-1 flex items-center justify-end gap-1 text-[10px] text-muted-foreground"><Clock3 className="h-3 w-3" />{formatTimestamp(source.lastRun)}</p></div></div></div>)}</div>}
    </Panel>
    <p className="flex items-center gap-2 text-[11px] text-muted-foreground"><ExternalLink className="h-3 w-3" />Source values are reported by the API view; no predictions are calculated in this interface.</p>
  </div>;
}
