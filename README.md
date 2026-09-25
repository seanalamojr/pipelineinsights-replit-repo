# PipelineInsights

PipelineInsights is a sport-agnostic player-prop prediction pipeline. Tennis is the
first reference implementation; the shared model, backtesting, prediction, API, and
dashboard layers are designed to support MLB and NFL without a rewrite.

## Current checkpoint: 9, the quantile GBM

Checkpoint 1 established:

- the architecture rules in `RULES.md`;
- a pinned Python dependency contract in `requirements.txt`;
- a safe environment-variable template in `.env.example`;
- the reusable SQLAlchemy/Postgres connection in `db/connection.py`;
- the config and repository boundaries needed by later checkpoints.

Checkpoint 2 adds:

- the core player, match, odds, and injuries tables;
- the feature table that forms the only model input boundary;
- append-only prediction storage with model-version uniqueness;
- the dashboard-only reporting view `vw_fact_player_prop_odds`;
- a repeatable migration runner at `db/migrate.py`.

Checkpoint 3 adds:

- deterministic, clearly tagged demo records for the dashboard;
- an aces-first tennis configuration, matching the first real market target;
- a dashboard artifact with overview, predictions, lines, trends, and backtest routes;
- a read-only API that returns only reporting-view data;
- explicit empty, loading, and unavailable-metric states instead of fabricated model results.

The readiness hardening adds stable snake_case prop keys, version-aware feature rows,
pre-match odds provenance, nullable future-match outcomes, real source counts, and
an API model-version registry. RMSE and agreement remain unavailable until realized
outcomes support a verified evaluation window.

Checkpoint 4 adds a real Sackmann ATP match loader. It expands each source match into
one row per player, keeps missing match statistics as NULL, flags retirements and
walkovers with `match_completed = false`, and records the source tournament date
separately from an explicitly estimated event date. The configured `Kadantte/tennis_atp`
fork is the source for the requested 2015–2025 seasons; unavailable seasons are
reported explicitly rather than silently substituted.

Checkpoints 5–6 build `player_game_features`, the only table models may read. The
`tennis_v1` feature definitions for aces, double faults, and service games are all
defined in `config/tennis.yaml`; reusable transforms exclude the current event,
incomplete matches, and all outcomes sharing the current estimated event date. The
builder emits rows even when the target is missing, marks minimum-history and
training eligibility explicitly, and runs four leakage audits against values read
back from PostgreSQL before committing.

Checkpoint 7 adds the deliberately simple baseline model in `models/baseline.py`.
It reads only `player_game_features`, uses the configured rolling mean as its base,
and applies training-period context ratios for surface, best-of, and tournament
level. Undersized context groups use an exact `1.0` multiplier. The model emits
versioned predictions for every active configured target, skips rows without
sufficient history, and reports excluded rows and the actual context multipliers.
Its one-standard-deviation descriptive bounds are not calibrated confidence
intervals, and no accuracy metrics are computed at this checkpoint.

## Verify the database connection

Provide `DATABASE_URL` through Replit Secrets or a local `.env` file, then run:

```bash
python -m db.connection
```

The command runs `SELECT 1` and reports the result without printing credentials.

To apply or re-apply the versioned development migrations:

```bash
python -m db.migrate
```

The migration runner records each applied filename and skips it on later runs. It
does not insert demo data. After migrations, load the demo slate with:

```bash
python -m scripts.seed_demo
```

The demo loader is safe to re-run. It uses `demo_` IDs and a stable daily
snapshot timestamp, so it cannot overwrite future live records.

Load real tennis match history from the configured Kadantte/Sackmann fork with:

```bash
python -m etl.tennis.sackmann --seasons 2015-2025
```

The loader is idempotent. It covers the requested 2015–2025 window from Kadantte.
Use `--refresh` to redownload cached CSVs, and
`--inspect-season 2015` to print Novak Djokovic's loaded history for a specific
season. When a current-season file is explicitly requested, ingestion refuses to
load it if its newest estimated event date is more than 21 days old. The configured
Kadantte source remains pinned until a verified maintained replacement is found;
stale data is rejected rather than silently replaced with another mirror.

To extend the database with attached current-season ATP and Challenger files,
repeat `--attached-file` once per CSV:

```bash
python -m etl.tennis.sackmann \
  --attached-file attached_assets/2026.csv \
  --attached-file attached_assets/ongoing_tourneys.csv \
  --attached-file attached_assets/2026_challenger.csv \
  --attached-file attached_assets/challenger_ongoing_tourneys.csv
```

Attached files use the same Sackmann column contract. Exact duplicate match keys
are skipped, while conflicting duplicate keys receive deterministic IDs so
neither match is silently lost. Current-season inputs still have to pass the
21-day freshness guard.

Build and audit the approved ace feature rows with:

```bash
python -m features.build_features
```

The command replaces only real `tennis_v1` feature rows, preserves demo versions,
prints null rates and target distributions for every configured target, validates a
random 50-row recomputation, checks first-match NULLs, inflates one current target
to prove invariance, and rejects any feature correlated above 0.99 with its target.
It does not train or run a model.

Run the baseline for all active targets with:

```bash
python -m models.baseline
```

Use `--dry-run` to print the same summaries without writing predictions. The
baseline writes `baseline_v1_<stat_target>` rows and safely replaces only an
existing row with the same player, match, prop, and model version.

Checkpoint 8 adds `evaluation/backtest.py` and the append-only
`model_backtest_results` table. It evaluates the baseline with monthly
walk-forward folds: each fold trains only on eligible feature rows before its
cutoff and scores the following month. Reports include MAE, RMSE, signed mean
bias, interval coverage, scored-row counts, and percentage MAE improvement over
`baseline_v1` on the identical test rows. The harness also includes
shuffled-target and future-cutoff safeguards.

Run the configured evaluation with:

```bash
python -m evaluation.backtest
```

Use `--dry-run` to print fold and pooled metrics without appending results.
The current configured 2025 evaluation window produced pooled MAE of 3.7513
for aces, 1.7915 for double faults, and 3.7941 for service games across 5,177
scored rows per target. These are baseline reference numbers, not claims of
production accuracy.

Checkpoint 9 adds `models/gbm.py`, using LightGBM quantile regression with
model versions `gbm_v1_aces`, `gbm_v1_double_faults`, and
`gbm_v1_service_games`. Each target trains three models from the configured
feature list: lower quantile, median prediction, and upper quantile. The
quantile levels are `[0.1, 0.5, 0.9]` in `config/tennis.yaml`; features are
selected there as well, and missing numeric values are passed to LightGBM as
nulls without zero imputation.

Quantile regression gives an uncertainty range by learning different points
of the observed outcome distribution. The median model supplies one point
prediction, while the lower and upper models show how wide the plausible
outcome range is. A single point-estimate model can only say what it expects;
it cannot distinguish a high-confidence prediction from a genuinely uncertain
one.

The configured GBM parameters are deliberately conservative:
`n_estimators=600`, `learning_rate=0.03`, `num_leaves=15`, `max_depth=4`,
`min_child_samples=50`, `reg_alpha=0.5`, `reg_lambda=2.0`, and
`colsample_bytree=0.8`. Early stopping uses the final 20% of each training
window by date, never a random validation split.

Run the GBM and its walk-forward report with:

```bash
python -m models.gbm
```

The run writes predictions to `player_prop_predictions`, appends quantile
feature importances to `model_feature_importances`, and appends fold and pooled
metrics to `model_backtest_results`. It also prints the top fifteen features
with their config descriptions and runs the GBM-specific shuffled-target
sabotage check.

The first GBM evaluation on the configured 2025 window was:

| Target | MAE | RMSE | Mean bias | Interval coverage | MAE improvement |
|---|---:|---:|---:|---:|---:|
| Aces | 2.9385 | 4.0293 | -0.5682 | 78.0% | 21.67% |
| Double faults | 1.6417 | 2.2041 | -0.2732 | 77.4% | 8.36% |
| Service games | 2.7126 | 3.4908 | -0.4716 | 78.2% | 28.51% |

Each comparison used 5,177 identical test rows. The shuffled-target check
increased first-fold MAE from 3.5248 to 4.9949 for aces, from 1.7492 to
2.0155 for double faults, and from 3.2021 to 4.5774 for service games.

The top feature audit did not show a match-outcome field dominating the model.
The leading features were prior same-surface performance, career-to-date
history, opponent concessions, match format, and pre-match rankings. These
are all available before the predicted match.

Checkpoint 12 uses the full configured historical window (`2015-01-01` through
`2026-10-01`) and scores baseline, GBM, and ensemble predictions on identical
monthly walk-forward test rows. Run the complete evaluation and write the
calibration report and model card with:

```bash
python -m evaluation.checkpoint12
```

Use `--fold-detail` to print every scored fold's MAE, RMSE, signed bias, interval
coverage, prediction-bin coverage, and ensemble weight source. The run appends
fold and pooled metrics, including prediction-ranked calibration bins, to
`model_backtest_results`; it does not replace earlier runs. It writes the
human-readable evaluation to `backtest/reports/checkpoint12-latest.md` and the
plain-language model card to `docs/model-card-tennis-v1.md`. Market comparison
reports raw paired counts only and does not claim hit rate or ROI when the
captured odds sample is too small.

### Verified WTA odds results

After applying migrations (`python -m db.migrate`), reconcile the attached
2026 WTA odds archive with official WTA result pages:

```bash
python -m etl.tennis.wta_results 'attached_assets/Tennis_prop_odds_—_pivoted_(over_under_per_row)_1789956870194.csv'
```

Use `--dry-run` to check official fixture coverage without changing the
database. The importer requires an unambiguous official scorecard, both
official player identities, an exact match date, final score and winner before
writing results. The odds loader then requires both WTA players and the
scheduled date before filling either internal odds key; post-start captures
are excluded. Re-running the command updates rather than duplicates rows.
Query `vw_wta_odds_results` for paired prices, winners, confirmed game/set
totals and the official source URL. Missing prop totals remain NULL; no model
predictions are fabricated to populate the prediction-anchored dashboard view.

The web dashboard is served by the managed PipelineInsights workflow. The API
workflow must be running as well for live dashboard data:

```bash
pnpm --filter @workspace/api-server run dev
pnpm --filter @workspace/pipelineinsights run dev
```

The Replit workspace keeps the existing Express/Node API adapter for the
dashboard artifact. It uses the same Postgres reporting view and generated
OpenAPI client as the Python pipeline scripts, so this compatibility choice
does not change the sport-agnostic model boundary or the time-based evaluation
rules.

## Planned build order

1. Scaffold and database connectivity
2. Core tables and reporting view
3. Demo data and dashboard shell
4. Tennis match ETL
5. Leakage-safe feature engineering
6. Odds ETL
7. Baseline model
8. Reusable backtesting harness
9. LightGBM and quantile intervals
10. Ensemble and real-data dashboard

## Repository map

- `config/` — validated sport configuration
- `db/` — database connection and versioned migrations
- `etl/` — source-specific ingestion
- `features/` — reusable feature transforms
- `models/` — shared prediction runners
- `evaluation/` — sport-agnostic walk-forward evaluation
- `backtest/` — reserved report output directory
- `api/` — thin read-only API layer
- `dashboard/` — React dashboard, added at the UI checkpoint
- `scripts/` — pipeline entry points
- `tests/` — acceptance and regression tests