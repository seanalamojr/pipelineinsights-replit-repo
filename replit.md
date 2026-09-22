# PipelineInsights

An auditable, sport-agnostic player-prop prediction pipeline, starting with tennis.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string
- Python checkpoint verification: `python -m db.connection`
- Python migration command: `python -m db.migrate`

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)
- Python: Python 3.11, SQLAlchemy 2.x, pandas, scikit-learn, and LightGBM

## Where things live

- `RULES.md` — non-negotiable architecture and data-boundary rules
- `config/` — sport configuration and its Pydantic validation boundary
- `db/` — SQLAlchemy connection plus versioned SQL migrations
- `etl/`, `features/`, `models/`, `backtest/`, `api/` — planned Python pipeline layers
- `dashboard/` — reserved for the React dashboard checkpoint

## Architecture decisions

- Models will read only the feature table so sport-specific ETL cannot leak into shared model code.
- Prediction history is append-only by model version for side-by-side evaluation.
- The dashboard will read only from the reporting view, not directly from database tables.
- All DDL is stored in `db/migrations/` and applied in filename order; the runner skips versions already recorded in `pipelineinsights_schema_migrations`.

## Product

The finished product will let an analyst inspect model predictions, confidence bands,
market edges, player trends, and time-based backtest results across supported sports.

## User preferences

The build follows the attached PipelineInsights brief and pauses for review after each
checkpoint. Explanations should assume an MSBA student who is new to coding and ML.

## Gotchas

- Do not add demo data before checkpoint 3 approval.
- Do not use random train/test splits; time ordering is part of model correctness.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
