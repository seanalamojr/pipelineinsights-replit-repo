import { useMemo } from 'react';
import { useGetPipelineBacktest, type BacktestAccuracy } from '@workspace/api-client-react';
import { Activity, CalendarClock, ChartNoAxesCombined, CircleHelp, ShieldCheck } from 'lucide-react';
import { EmptyState, ErrorState, LoadingBlock, Panel, SectionHeading, SourceNote } from '@/components/dashboard-ui';
import { formatDate, formatMetric, formatPropLabel, formatTimestamp } from '@/lib/pipeline';

type MetricKind = 'decimal' | 'percent';

const modelFamilyOrder: Record<string, number> = {
  baseline: 0,
  GBM: 1,
  ensemble: 2,
};

function metricLabel(value: number | null, rowCount: number, kind: MetricKind, testId: string) {
  return <div data-testid={testId} className="flex min-w-[102px] flex-col gap-1">
    <span className="font-mono text-[14px] font-medium tabular-nums text-foreground">{formatMetric(value, kind)}</span>
    <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-muted-foreground">{rowCount.toLocaleString()} scored rows</span>
  </div>;
}

function ModelRow({ model, targetKey }: { model: BacktestAccuracy; targetKey: string }) {
  const rowKey = `${targetKey}-${model.modelVersion}`;
  const repairText = model.intervalRepairCount === null
    ? 'Unavailable for this run'
    : `${model.intervalRepairCount.toLocaleString()} repaired`;
  const crossingText = model.intervalCrossingCount === null
    ? null
    : `${model.intervalCrossingCount.toLocaleString()} crossed`;
  return <tr data-testid={`row-backtest-model-${rowKey}`} className="border-t border-border/70 align-top">
    <th scope="row" className="min-w-[176px] px-4 py-4 text-left">
      <div className="flex items-center gap-2">
        <span className={`h-1.5 w-1.5 rounded-full ${model.modelFamily.toLowerCase() === 'baseline' ? 'bg-muted-foreground' : model.modelFamily.toLowerCase() === 'gbm' ? 'bg-primary' : 'bg-accent'}`} />
        <span className="text-[12px] font-semibold">{model.modelFamily}</span>
      </div>
      <span className="mt-1 block max-w-[160px] truncate font-mono text-[9px] font-normal text-muted-foreground" title={model.modelVersion}>{model.modelVersion}</span>
      <span className="mt-1 block font-mono text-[9px] text-muted-foreground">{model.foldCount} folds</span>
      {model.firstCutoff && model.lastTestEnd && (
        <span className="mt-1 block font-mono text-[9px] text-muted-foreground">
          {formatDate(model.firstCutoff)} → {formatDate(model.lastTestEnd)}
        </span>
      )}
    </th>
    <td className="px-4 py-4">{metricLabel(model.mae, model.scoredRows, 'decimal', `value-backtest-mae-${rowKey}`)}</td>
    <td className="px-4 py-4">{metricLabel(model.rmse, model.scoredRows, 'decimal', `value-backtest-rmse-${rowKey}`)}</td>
    <td className="px-4 py-4">{metricLabel(model.meanBias, model.scoredRows, 'decimal', `value-backtest-bias-${rowKey}`)}</td>
    <td className="px-4 py-4">{metricLabel(model.intervalCoverage, model.intervalScoredRows, 'percent', `value-backtest-coverage-${rowKey}`)}</td>
    <td className="px-4 py-4">
      <div className="flex min-w-[118px] flex-col gap-1" data-testid={`value-backtest-repairs-${rowKey}`}>
        <span className="font-mono text-[12px] font-medium tabular-nums text-foreground">{repairText}</span>
        {crossingText && <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-muted-foreground">{crossingText}</span>}
      </div>
    </td>
    <td className="px-4 py-4">{metricLabel(model.maeImprovementOverBaseline, model.scoredRows, 'percent', `value-backtest-improvement-${rowKey}`)}</td>
  </tr>;
}

function TargetSection({ targetKey, label, models }: { targetKey: string; label: string; models: BacktestAccuracy[] }) {
  const sortedModels = [...models].sort((left, right) => {
    const leftOrder = modelFamilyOrder[left.modelFamily] ?? 3;
    const rightOrder = modelFamilyOrder[right.modelFamily] ?? 3;
    return leftOrder - rightOrder || left.modelFamily.localeCompare(right.modelFamily);
  });

  return <section data-testid={`section-backtest-target-${targetKey}`} className="overflow-hidden rounded-xl border border-border/80 bg-background/45">
    <div className="flex flex-col gap-3 border-b border-border/80 px-4 py-4 sm:flex-row sm:items-start sm:justify-between sm:px-5">
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">Stat target</p>
        <h3 data-testid={`text-backtest-target-${targetKey}`} className="mt-1 font-display text-[19px] font-semibold tracking-tight">{label}</h3>
        <p className="mt-1 font-mono text-[10px] text-muted-foreground">{targetKey}</p>
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-muted-foreground">
        <span>{models.length} model {models.length === 1 ? 'row' : 'rows'}</span>
        <span aria-hidden="true" className="text-border">/</span>
        <span>baseline and GBM stay target-matched</span>
      </div>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full min-w-[940px] border-collapse text-left">
        <caption className="sr-only">{label} backtest comparison by model family</caption>
        <thead className="bg-muted/35">
          <tr>
            <th scope="col" className="px-4 py-3 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">Model</th>
            <th scope="col" className="px-4 py-3 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">MAE</th>
            <th scope="col" className="px-4 py-3 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">RMSE</th>
            <th scope="col" className="px-4 py-3 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">Mean bias</th>
            <th scope="col" className="px-4 py-3 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">Interval coverage</th>
            <th scope="col" className="px-4 py-3 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">Interval repairs</th>
            <th scope="col" className="px-4 py-3 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">MAE vs baseline</th>
          </tr>
        </thead>
        <tbody>{sortedModels.map((model) => <ModelRow key={model.modelVersion} model={model} targetKey={targetKey} />)}</tbody>
      </table>
    </div>
    <div className="flex flex-col gap-2 border-t border-border/70 bg-muted/20 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
      <SourceNote>Interval coverage is observed coverage against the model&apos;s 80% interval target.</SourceNote>
      <SourceNote>MAE, RMSE, bias, coverage, and improvement show their scored row count.</SourceNote>
    </div>
  </section>;
}

export default function BacktestPage() {
  const query = useGetPipelineBacktest();
  const backtest = query.data;
  const loading = query.isLoading || query.isFetching;
  const targetGroups = useMemo(() => {
    const groups = new Map<string, { label: string; models: BacktestAccuracy[] }>();
    for (const model of backtest?.models ?? []) {
      const current = groups.get(model.statTarget);
      if (current) {
        current.models.push(model);
      } else {
        groups.set(model.statTarget, {
          label: model.propLabel || formatPropLabel(model.statTarget),
          models: [model],
        });
      }
    }
    return Array.from(groups, ([targetKey, group]) => ({ targetKey, ...group }));
  }, [backtest?.models]);

  return <div className="space-y-7">
    <header className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
      <div>
        <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-primary">Validation lab / 05</p>
        <h1 className="font-display text-[34px] font-semibold leading-none tracking-[-0.045em] sm:text-[42px]">Backtest, without the blur.</h1>
        <p className="mt-3 max-w-[690px] text-[14px] leading-relaxed text-muted-foreground">Compare model families against realized tennis outcomes, target by target. The API owns the scoring; this view only reports the returned values.</p>
        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
          {backtest?.runTimestamp && <SourceNote>Run {formatTimestamp(backtest.runTimestamp)}</SourceNote>}
           {backtest?.models.length ? <SourceNote>{targetGroups.length} stat targets with scored rows</SourceNote> : <SourceNote>Awaiting scored outcomes</SourceNote>}
        </div>
      </div>
      <div className="flex max-w-[330px] items-start gap-2 rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-[12px] leading-relaxed text-primary">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span>Only server-scored outcomes belong in this comparison.</span>
      </div>
    </header>

    <Panel className="border-primary/20 bg-primary/[0.035]">
      <div className="flex items-start gap-3 px-5 py-4">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10 text-primary"><CircleHelp className="h-4 w-4" aria-hidden="true" /></div>
        <div>
          <h2 className="font-display text-[14px] font-semibold">Accuracy is not edge</h2>
          <p className="mt-1 max-w-[760px] text-[12px] leading-relaxed text-muted-foreground">These figures measure closeness to realized outcomes, not profitability against a sportsbook. Keep model accuracy and sportsbook edge as separate questions.</p>
        </div>
      </div>
    </Panel>

    {query.isError ? <Panel><ErrorState onRetry={() => void query.refetch()} /></Panel> : loading ? <Panel className="overflow-hidden">
      <SectionHeading eyebrow="Model validation" title="Backtest results" detail="Loading server-scored metrics." />
      <LoadingBlock rows={6} height="h-12" />
    </Panel> : !backtest || !backtest.models.length ? <Panel className="overflow-hidden">
      <SectionHeading eyebrow="Model validation" title="Backtest results" detail="No scored model rows were returned by the reporting view." />
      <EmptyState icon="data" title="No realized outcomes are scored yet" description="This view will populate when the API returns a scored PipelineBacktest run. No metrics are estimated in the browser." />
    </Panel> : <Panel className="overflow-hidden">
      <SectionHeading eyebrow="Model validation" title="Backtest results" detail="Each stat target is shown independently so baseline and GBM are directly comparable." action={<span data-testid="status-backtest-available" className="inline-flex items-center gap-1.5 rounded-full border border-primary/25 bg-primary/10 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.1em] text-primary"><Activity className="h-3 w-3" aria-hidden="true" />Scored</span>} />
      <div className="space-y-4 p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-border/70 pb-4 text-[11px] text-muted-foreground">
          <span className="inline-flex items-center gap-1.5"><ChartNoAxesCombined className="h-3.5 w-3.5 text-primary" aria-hidden="true" />{targetGroups.length} separate stat targets</span>
          {backtest.runTimestamp && <span className="inline-flex items-center gap-1.5"><CalendarClock className="h-3.5 w-3.5" aria-hidden="true" />Scored {formatDate(backtest.runTimestamp, 'long')}</span>}
        </div>
        <div className="space-y-4">{targetGroups.map((group) => <TargetSection key={group.targetKey} {...group} />)}</div>
      </div>
    </Panel>}
  </div>;
}
