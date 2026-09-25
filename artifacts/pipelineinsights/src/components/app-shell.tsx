import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getGetPipelineOverviewQueryKey, getGetPipelinePredictionsQueryKey, useHealthCheck } from '@workspace/api-client-react';
import { BarChart3, BookOpen, ChevronDown, CircleHelp, Database, FileChartColumn, Gauge, Menu, Moon, Printer, RefreshCw, Sun, Table2, TrendingUp, X } from 'lucide-react';
import { Link, useLocation } from 'wouter';
import { PipelineModeContext, type PipelineDataMode } from '@/contexts/pipeline-mode';

const INTERVALS = [
  { label: 'Every 5 min', value: 5 * 60 * 1000 },
  { label: 'Every 15 min', value: 15 * 60 * 1000 },
  { label: 'Every hour', value: 60 * 60 * 1000 },
];

const navItems = [
  { href: '/', label: 'Overview', icon: Gauge },
  { href: '/predictions', label: 'Predictions', icon: FileChartColumn },
  { href: '/lines', label: 'Market lines', icon: Table2 },
  { href: '/trends', label: 'Player trends', icon: TrendingUp },
  { href: '/backtest', label: 'Backtest', icon: BarChart3 },
];

function iconButtonClass() {
  return 'inline-flex h-9 w-9 items-center justify-center rounded-lg border border-sidebar-border/70 text-sidebar-foreground/75 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground disabled:cursor-not-allowed disabled:opacity-50';
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dark, setDark] = useState(() => localStorage.getItem('pipeline-theme') === 'dark');
  const [mode, setMode] = useState<PipelineDataMode>(() => localStorage.getItem('pipeline-mode') === 'demo' ? 'demo' : 'real');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [intervalMs, setIntervalMs] = useState(INTERVALS[0].value);
  const [refreshMenuOpen, setRefreshMenuOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const healthQuery = useHealthCheck();

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('pipeline-theme', dark ? 'dark' : 'light');
  }, [dark]);

  useEffect(() => {
    localStorage.setItem('pipeline-mode', mode);
  }, [mode]);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setRefreshMenuOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: getGetPipelineOverviewQueryKey({ mode }) }),
      queryClient.invalidateQueries({ queryKey: getGetPipelinePredictionsQueryKey({ mode }) }),
    ]);
    window.setTimeout(() => setRefreshing(false), 650);
  }, [mode, queryClient]);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = window.setInterval(() => void refresh(), intervalMs);
    return () => window.clearInterval(timer);
  }, [autoRefresh, intervalMs, refresh]);

  const status = healthQuery.data?.status;

  return (
    <PipelineModeContext.Provider value={{ mode, setMode }}>
    <div className="noise min-h-[100dvh] bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[244px] flex-col bg-sidebar text-sidebar-foreground md:flex">
        <div className="border-b border-sidebar-border/80 px-5 py-5">
          <Link href="/" data-testid="link-brand" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-sidebar-primary font-display text-lg font-bold text-sidebar-primary-foreground">P</span>
            <span>
              <span className="block font-display text-[16px] font-semibold tracking-tight">PipelineInsights</span>
              <span className="mt-0.5 block font-mono text-[9px] uppercase tracking-[0.19em] text-sidebar-foreground/55">Analyst cockpit</span>
            </span>
          </Link>
        </div>
        <div className="flex-1 px-3 py-6">
          <p className="px-3 pb-3 font-mono text-[10px] uppercase tracking-[0.18em] text-sidebar-foreground/45">Workspace</p>
          <nav className="space-y-1" aria-label="Main navigation">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = location === item.href;
              return (
                <Link key={item.href} href={item.href} data-testid={`link-nav-${item.label.toLowerCase().replaceAll(' ', '-')}`} className={`group flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] transition-colors ${active ? 'bg-sidebar-primary font-semibold text-sidebar-primary-foreground' : 'text-sidebar-foreground/68 hover:bg-sidebar-accent hover:text-sidebar-foreground'}`}>
                  <Icon className="h-[17px] w-[17px]" strokeWidth={active ? 2.2 : 1.7} />
                  <span>{item.label}</span>
                  {item.href === '/predictions' && <span className={`ml-auto h-1.5 w-1.5 rounded-full ${active ? 'bg-sidebar-primary-foreground' : 'bg-sidebar-foreground/30'}`} />}
                </Link>
              );
            })}
          </nav>
          <div className="mt-9 border-t border-sidebar-border/70 pt-6">
            <p className="px-3 pb-3 font-mono text-[10px] uppercase tracking-[0.18em] text-sidebar-foreground/45">Reference</p>
            <div className="space-y-1">
              <button type="button" data-testid="button-sources" onClick={() => alert('Source registry is available in the Sources panel on Overview.')} className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-[13px] text-sidebar-foreground/68 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"><Database className="h-[17px] w-[17px]" strokeWidth={1.7} />Sources</button>
              <button type="button" data-testid="button-help" onClick={() => alert('PipelineInsights makes model inputs and edges inspectable. Start with Overview, then open any prediction.')} className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-[13px] text-sidebar-foreground/68 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"><CircleHelp className="h-[17px] w-[17px]" strokeWidth={1.7} />Method notes</button>
            </div>
          </div>
        </div>
        <div className="border-t border-sidebar-border/80 px-5 py-4">
          <div data-testid="status-data-mode-sidebar" className="mb-3 flex items-center justify-between rounded-lg bg-sidebar-accent px-3 py-2 text-[11px] text-sidebar-foreground/80"><span>Data mode</span><strong>{mode === 'demo' ? 'Demo' : 'Real'}</strong></div>
          <div className="flex items-center gap-2 text-[10px] text-sidebar-foreground/45"><span className={`h-1.5 w-1.5 rounded-full ${status === 'ok' ? 'bg-emerald-400' : 'bg-sidebar-foreground/30'}`} />API {status === 'ok' ? 'operational' : 'checking status'}</div>
        </div>
      </aside>

      {mobileOpen && <div className="fixed inset-0 z-20 bg-sidebar/30 md:hidden" onClick={() => setMobileOpen(false)} />}
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-[244px] flex-col bg-sidebar text-sidebar-foreground transition-transform md:hidden ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
         <div className="border-b border-sidebar-border/80 px-5 py-5"><div className="flex items-center justify-between"><Link href="/" data-testid="link-brand-mobile" className="font-display font-semibold">PipelineInsights</Link><button type="button" aria-label="Close navigation" data-testid="button-close-mobile-nav" className={iconButtonClass()} onClick={() => setMobileOpen(false)}><X className="h-4 w-4" /></button></div></div>
        <nav className="space-y-1 px-3 py-6">{navItems.map((item) => <Link key={item.href} href={item.href} data-testid={`link-mobile-${item.label.toLowerCase().replaceAll(' ', '-')}`} onClick={() => setMobileOpen(false)} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] text-sidebar-foreground/75 hover:bg-sidebar-accent"><item.icon className="h-4 w-4" />{item.label}</Link>)}</nav>
      </aside>

      <main className="min-h-[100dvh] md:pl-[244px]">
        <header className="sticky top-0 z-10 flex h-[68px] items-center justify-between border-b border-border/80 bg-background/90 px-4 backdrop-blur-md sm:px-7">
          <div className="flex items-center gap-3">
             <button type="button" aria-label="Open navigation" data-testid="button-open-mobile-nav" className="rounded-lg border border-border p-2 md:hidden" onClick={() => setMobileOpen(true)}><Menu className="h-4 w-4" /></button>
            <div className="hidden items-center gap-2 font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground sm:flex"><span className="text-primary">PIPELINE</span><span>/</span><span>{navItems.find((item) => item.href === location)?.label ?? 'Overview'}</span></div>
            <span data-testid="status-data-mode" className="whitespace-nowrap rounded-md border border-accent/40 bg-accent/10 px-2 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-accent-foreground">{mode === 'demo' ? 'Demo' : 'Real'}</span>
          </div>
          <div className="flex items-center gap-2">
            <label className="sr-only" htmlFor="pipeline-data-mode">Data mode</label>
            <select id="pipeline-data-mode" data-testid="select-data-mode" aria-label="Data mode" value={mode} onChange={(event) => setMode(event.target.value as PipelineDataMode)} className="h-9 w-[108px] rounded-lg border border-border bg-card px-2 text-[11px] font-medium text-foreground sm:w-[118px]">
              <option value="real">Real data</option>
              <option value="demo">Demo data</option>
            </select>
            <div className="relative" ref={menuRef}>
              <div className="flex h-9 items-center rounded-lg border border-border bg-card">
                <button type="button" data-testid="button-refresh" onClick={() => void refresh()} disabled={refreshing} className="flex h-full items-center gap-2 px-3 text-[12px] font-medium text-foreground/75 transition-colors hover:text-primary disabled:opacity-50"><RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />Refresh</button>
                <span className="h-4 w-px bg-border" />
                <button type="button" data-testid="button-refresh-menu" onClick={() => setRefreshMenuOpen((open) => !open)} className="flex h-full items-center px-2 text-muted-foreground hover:text-foreground"><ChevronDown className="h-3.5 w-3.5" /></button>
              </div>
              {refreshMenuOpen && <div className="absolute right-0 top-11 z-50 w-52 rounded-xl border border-border bg-card p-3 shadow-md">
                <label className="flex items-center justify-between border-b border-border pb-3 text-[12px] font-medium"><span>Auto-refresh</span><input data-testid="switch-auto-refresh" type="checkbox" checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} className="accent-primary" /></label>
                <div className="pt-2"><p className="mb-1.5 font-mono text-[9px] uppercase tracking-widest text-muted-foreground">Interval</p>{INTERVALS.map((item) => <button key={item.value} type="button" data-testid={`button-interval-${item.value}`} onClick={() => setIntervalMs(item.value)} className={`flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-[11px] ${intervalMs === item.value ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted'}`}>{item.label}{intervalMs === item.value && <span>Selected</span>}</button>)}</div>
                <p className="mt-2 text-[10px] leading-relaxed text-muted-foreground">Automatic updates never run more often than every five minutes.</p>
              </div>}
            </div>
            <button type="button" data-testid="button-print" onClick={() => window.print()} className={`${iconButtonClass()} hidden sm:inline-flex`}><Printer className="h-4 w-4" /></button>
            <button type="button" data-testid="button-theme" onClick={() => setDark((value) => !value)} className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground transition-colors hover:text-foreground">{dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}</button>
          </div>
        </header>
        <div className="mx-auto max-w-[1520px] px-4 py-7 sm:px-7 lg:px-9">{children}</div>
      </main>
    </div>
    </PipelineModeContext.Provider>
  );
}
