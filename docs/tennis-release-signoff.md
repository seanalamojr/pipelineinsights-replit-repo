# Tennis real-run release evidence

Evidence captured on 2026-09-21.

## Real-run prerequisites

- Configured source: `sackmann_kadantte`.
- Configured historical window: 2015-01-01 through 2026-10-01.
- Development match coverage: 2015-01-06 through 2026-09-19.
- Supported non-demo command:

  ```sh
  python -m scripts.run_pipeline \
    --seasons 2015-2025 \
    --attached-file attached_assets/2026_1789695249523.csv \
    --attached-file attached_assets/2026_challenger_1789695253916.csv \
    --write-predictions
  ```

## Persisted real outputs

The development database contains:

| Output | Real rows | Demo rows | Timestamp |
|---|---:|---:|---|
| Players | 2,229 | 8 | n/a |
| Matches | 77,236 | 8 | through 2026-09-19 |
| Features | 231,708 | 24 | 2026-09-18 02:29:29.811790 UTC |
| Predictions, including backtests | 1,214,061 | 72 | through 2026-09-21 02:24:43.962939 UTC |

Feature rows are split evenly across `aces`, `double_faults`, and
`service_games`: 77,236 real rows per target under `tennis_v1`.

Persisted production-model prediction rows:

| Model version | Rows | Prediction timestamp |
|---|---:|---|
| `baseline_v1_aces` | 68,294 | 2026-09-18 03:06:34.246000 UTC |
| `gbm_v1_aces` | 68,294 | 2026-09-18 03:36:19.583318 UTC |
| `ensemble_v1_aces` | 68,294 | 2026-09-18 18:38:14.476208 UTC |
| `baseline_v1_double_faults` | 68,294 | 2026-09-18 03:06:43.134839 UTC |
| `gbm_v1_double_faults` | 68,294 | 2026-09-18 03:36:19.583318 UTC |
| `ensemble_v1_double_faults` | 68,294 | 2026-09-18 18:38:14.476208 UTC |
| `baseline_v1_service_games` | 68,284 | 2026-09-18 03:06:51.040804 UTC |
| `gbm_v1_service_games` | 68,284 | 2026-09-18 03:36:19.583318 UTC |
| `ensemble_v1_service_games` | 68,284 | 2026-09-18 18:38:14.476208 UTC |

## Append-only proof

This command was run:

```sh
python -m scripts.run_pipeline \
  --skip-etl \
  --skip-features \
  --write-predictions
```

It exited with status 1 before model execution because all nine requested real
model versions already exist. The runner reported:

> Refusing to overwrite existing real prediction versions. Create new model
> versions before persisting another run.

The before counts were unchanged, and no historical prediction version was
overwritten.

## Demo separation

- Pipeline model reads exclude IDs beginning with `demo_`.
- API prediction rows expose `isDemo`.
- The dashboard shows a snapshot-level demo warning and row-level `Demo` badges.
- Development smoke data contained both real and demo rows; the first 200
  predictions contained 92 real and 108 demo rows.
- The current production database contains a demo snapshot only. Its first
  Predictions response contained 96 demo rows and no real rows, all explicitly
  labeled through `isDemo`.

## Reporting compatibility and smoke checks

The API builds reporting rows directly from base tables rather than depending
on columns missing from a stale published reporting view. Legacy production
prop labels are matched case-insensitively at the request boundary, avoiding a
destructive data migration.

Development smoke results after rebuilding the API:

| Flow | Result |
|---|---|
| Predictions | HTTP 200, 200 rows |
| Model Versions | HTTP 200, 18 rows |
| Overview | HTTP 200 |
| Backtest | HTTP 200, available, 9 models |
| Player Trends | HTTP 200, 61 rows |

Both API and dashboard TypeScript checks passed. Workflow and browser logs
showed no request, schema, database, response-shape, or console errors after
the fix.

## Production release gate

The current public deployment has a successful build at
`https://pipeline-insights-sralam02.replit.app`. Before the final compatibility
change, Predictions, Model Versions, Overview, and Backtest returned HTTP 200.
Player Trends exposed the legacy-label mismatch fixed in this change.

Publishing while this assigned task was still isolated rebuilt the pre-merge
project, so production continued to return HTTP 400 for Player Trends. The fix
must first merge through task completion. A post-merge publish is then required
before the five-flow production smoke can be signed off. After publishing,
rerun the five requests and confirm Player Trends returns HTTP 200 for a
production row.

## Unavailable metrics and operating status

- Production overview RMSE and model agreement remain unavailable until the
  reporting snapshot has suitable scored data.
- Market hit rate and ROI remain unavailable because there are no paired
  prediction, line, and realized-outcome rows.
- The real pipeline is proven in development and protected against accidental
  same-version rewrites.
- Routine production operation is not signed off until the merged compatibility
  fix is published and the final five-flow production smoke passes.
