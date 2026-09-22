# PipelineInsights Architecture Rules

These rules are non-negotiable. They keep the prediction system auditable as tennis
expands to MLB and NFL.

1. **Models never read raw data.** Models read from exactly one table:
   `player_game_features`. Nothing else.
2. **Sport-specific code is limited to data sources, ETL scripts, raw tables, and
   feature engineering.** Models, the ensemble, predictions, backtesting, and the
   dashboard are shared and sport-agnostic.
3. **Prediction history is append-only by model version.** Every prediction row has a
   `modelversion` and `predictiontimestamp`. Never overwrite or delete an old
   `modelversion`; bump the version when features, model type, hyperparameters, or
   ensemble weights change.
4. **Prop keys are normalized.** Database and API prop identifiers use stable
   snake_case keys such as `aces` and `games_won`; display labels belong at the
   presentation boundary.
5. **Splits are time-based only.** Training uses earlier dates and testing uses later
   dates. Random or shuffled splits are prohibited because they introduce lookahead
   bias.
6. **The dashboard reads only from `vw_fact_player_prop_odds`.** It never queries a
   base table and never contains business logic.
7. **Dashboard metrics are data-backed.** No metric, score, status, or quality
   indicator shown in the dashboard may be a hardcoded literal. Every displayed
   value must trace to a query result or a computed expression. If a value is
   not yet computable, render it as unavailable.

## Checkpoint discipline

Build in the order described in `README.md`. Stop after each checkpoint for review.
Checkpoints 4–9 are the current verified state: migrations, the reporting view,
labeled demo data, real tennis match ETL, leakage-safe `tennis_v1` features, the
versioned baseline, the strict walk-forward evaluation harness, and the
config-driven quantile GBM are complete. The GBM reads only
`player_game_features`, uses time-based validation, and stores versioned
predictions plus append-only evaluation and feature-importance records. The
ensemble remains disabled until its checkpoint is explicitly approved.