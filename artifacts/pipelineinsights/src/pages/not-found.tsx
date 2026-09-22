import { ArrowLeft, CircleAlert } from 'lucide-react';
import { Link } from 'wouter';

export default function NotFound() {
  return (
    <div className="flex min-h-[60dvh] w-full items-center justify-center">
      <div className="mx-4 w-full max-w-md rounded-xl border border-border bg-card p-7 shadow-[var(--shadow-sm)]">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-accent/35 bg-accent/10 text-accent-foreground">
            <CircleAlert className="h-5 w-5" />
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-primary">Route registry</p>
            <h1 className="mt-1 font-display text-2xl font-semibold tracking-tight">This view is not registered.</h1>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">The requested path is outside the PipelineInsights reporting surface.</p>
          </div>
        </div>
        <Link href="/" data-testid="link-not-found-home" className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5">
          <ArrowLeft className="h-3.5 w-3.5" /> Return to overview
        </Link>
      </div>
    </div>
  );
}
