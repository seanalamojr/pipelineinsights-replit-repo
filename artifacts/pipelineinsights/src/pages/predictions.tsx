import { useMemo, useState } from 'react';
import { useGetPipelineModelVersions, useGetPipelinePredictions } from '@workspace/api-client-react';
import { Filter, Layers, Search, SlidersHorizontal } from 'lucide-react';
import { EmptyState, ErrorState, ExportButton, LoadingBlock, Panel, SectionHeading, SourceNote } from '@/components/dashboard-ui';
import { PaginationHint } from '@/components/prediction-table';
import { PredictionTable } from '@/components/prediction-table';
import { formatDate, formatEdge, formatPropLabel } from '@/lib/pipeline';

export default function PredictionsPage() {
  const [modelVersion, setModelVersion] = useState('all');
  const [search, setSearch] = useState('');
  const query = useGetPipelinePredictions(modelVersion === 'all' ? undefined : { modelVersion });
  const versionsQuery = useGetPipelineModelVersions();
  const rows = query.data ?? [];
  const versions = useMemo(() => Array.from(new Set((versionsQuery.data ?? []).map((version) => version.modelVersion))).sort(), [versionsQuery.data]);
  const filtered = useMemo(() => rows.filter((row) => `${row.player} ${row.matchup} ${row.propLabel} ${row.propType}`.toLowerCase().includes(search.toLowerCase())), [rows, search]);
  const exportRows = filtered.map((row) => ({ player: row.player, event: row.matchup, date: formatDate(row.eventDate), market: row.propLabel, line: row.line ?? '', projection: row.projection, lower_ci: row.lowerCi, upper_ci: row.upperCi, edge: formatEdge(row.edge), side: row.side ?? '', book: row.book ?? '', model_version: row.modelVersion }));
  const loading = query.isLoading || query.isFetching;

  return <div className="space-y-7">
    <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end"><div><p className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-primary">Prediction ledger / 02</p><h1 className="font-display text-[34px] font-semibold leading-none tracking-[-0.045em] sm:text-[42px]">Model outputs, unabridged.</h1><p className="mt-3 max-w-[660px] text-[14px] leading-relaxed text-muted-foreground">Confidence bands stay attached to every forecast. Filter by model checkpoint to compare what changed and why.</p></div><SourceNote>Read-only reporting view · no frontend calculations</SourceNote></div>
    <Panel className="overflow-hidden">
      <SectionHeading eyebrow="Prediction registry" title="All generated predictions" detail="One row per model output and posted market line." action={<ExportButton filename="pipeline-predictions.csv" rows={exportRows} />} />
      <div className="flex flex-wrap items-end gap-3 border-b border-border/70 bg-muted/20 px-5 py-4">
        <div className="min-w-[230px] flex-1"><label htmlFor="prediction-search" className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">Find player or market</label><div className="relative"><Search className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" /><input id="prediction-search" data-testid="input-prediction-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="e.g. Scottie, birdies, Phoenix" className="h-9 w-full rounded-lg border border-border bg-card pl-9 pr-3 text-[12px] outline-none ring-primary/20 transition focus:ring-2" /></div></div>
        <div className="w-[210px]"><label htmlFor="model-version" className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">Model checkpoint</label><div className="relative"><Layers className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" /><select id="model-version" data-testid="select-model-version" value={modelVersion} onChange={(event) => setModelVersion(event.target.value)} className="h-9 w-full appearance-none rounded-lg border border-border bg-card pl-9 pr-3 text-[12px] outline-none focus:ring-2 focus:ring-primary/20"><option value="all">All versions</option>{versions.map((version) => <option key={version} value={version}>{version}</option>)}</select></div></div>
        <div className="flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-[11px] text-muted-foreground"><Filter className="h-3.5 w-3.5" />{filtered.length} matching rows</div>
        <button type="button" data-testid="button-clear-prediction-filters" onClick={() => { setSearch(''); setModelVersion('all'); }} className="inline-flex h-9 items-center gap-2 rounded-lg px-2 text-[11px] text-muted-foreground hover:text-primary"><SlidersHorizontal className="h-3.5 w-3.5" />Reset</button>
      </div>
      {query.isError ? <ErrorState onRetry={() => void query.refetch()} /> : loading ? <LoadingBlock rows={7} height="h-11" /> : !filtered.length ? <EmptyState title="No predictions match" description="Try a different player, market, or model checkpoint. Empty results are intentional, not inferred." /> : <><PredictionTable rows={filtered} /><PaginationHint count={filtered.length} /></>}
    </Panel>
  </div>;
}
