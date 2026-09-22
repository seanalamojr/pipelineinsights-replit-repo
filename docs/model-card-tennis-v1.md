# Tennis player-prop model card v1

This document describes what was evaluated, how it was evaluated, and when the predictions should not be trusted. It is written for a reader who did not build the pipeline.

## Evaluation window and training rule

- Sport: `tennis`.
- Training/test window: `2015-01-01` through `2026-10-01`.
- Fold cadence: every 1 month(s).
- Scored monthly folds: aces=129, double_faults=129, service_games=129. Calendar windows without a test row or without strictly earlier training rows are not scored.
- For each fold, training uses only eligible rows before the cutoff; the following monthly window is the test set.
- The three targets are aces, double faults, and service games.

## Model versions

- `baseline_v1_<target>` is a transparent rolling-mean reference with training-period context adjustments.
- `gbm_v1_<target>` is a LightGBM quantile model with 0.1, 0.5, and 0.9 quantiles. The median is the point prediction and the outer quantiles form the interval.
- `ensemble_v1_<target>` combines the versioned baseline and GBM outputs. Evaluation-only weights may be fitted from earlier folds; production uses the configured static weights.

## Production versus evaluation weights (read before using ensemble metrics)

The ensemble scores in this document are not the exact artifact that production currently runs. Walk-forward evaluation fits weights from strictly earlier scored folds so it can measure a time-safe adaptive ensemble. Production prediction generation uses the configured static weights from `config/tennis.yaml`; those fitted evaluation weights are not persisted as a production model artifact.

### Fitted weight summary

| Target | OOF objective | Member | Folds | Mean weight | Range |
|---|---|---|---:|---:|---:|
| unavailable | unavailable | unavailable | 0 | unavailable | unavailable |

The persisted append-only run used to rebuild this card predates objective-specific weight instrumentation; the corrected evaluator will populate this table on its next full run.

### OOF objective comparison

| Target | OOF objective | Pooled ensemble MAE |
|---|---|---:|
| aces | absolute error | unavailable |
| aces | squared error | unavailable |
| double_faults | absolute error | unavailable |
| double_faults | squared error | unavailable |
| service_games | absolute error | unavailable |
| service_games | squared error | unavailable |

## Features

### Baseline

- Base feature: `rolling_mean_10`.
- Training-only context ratios: surface, best_of, tourney_level.
- Bounds: approximately one prior rolling standard deviation around the point prediction; not calibrated by construction.

### GBM

The GBM uses the configured feature list independently for each target:
- `aces`: `rolling_mean_3`, `rolling_std_3`, `rolling_mean_5`, `rolling_std_5`, `rolling_mean_10`, `rolling_std_10`, `rolling_mean_20`, `rolling_std_20`, `surface_rolling_mean`, `surface_rolling_n_observations`, `rolling_aces_per_service_game`, `rolling_first_serve_in_pct`, `rest_days`, `head_to_head_average`, `head_to_head_matches`, `head_to_head_win_rate`, `opponent_aces_conceded_rate`, `career_to_date_mean`, `history_observations`, `best_of`, `surface`, `tourney_level`, `player_rank`, `opponent_rank`, `rank_difference`, `player_height_cm`
- `double_faults`: `rolling_mean_3`, `rolling_std_3`, `rolling_mean_5`, `rolling_std_5`, `rolling_mean_10`, `rolling_std_10`, `rolling_mean_20`, `rolling_std_20`, `surface_rolling_mean`, `surface_rolling_n_observations`, `rolling_double_faults_per_service_game`, `rolling_first_serve_in_pct`, `rest_days`, `head_to_head_average`, `head_to_head_matches`, `head_to_head_win_rate`, `opponent_double_faults_conceded_rate`, `career_to_date_mean`, `history_observations`, `best_of`, `surface`, `tourney_level`, `player_rank`, `opponent_rank`, `rank_difference`, `player_height_cm`
- `service_games`: `rolling_mean_3`, `rolling_std_3`, `rolling_mean_5`, `rolling_std_5`, `rolling_mean_10`, `rolling_std_10`, `rolling_mean_20`, `rolling_std_20`, `surface_rolling_mean`, `surface_rolling_n_observations`, `rolling_service_games_per_minute`, `rolling_first_serve_in_pct`, `rest_days`, `head_to_head_average`, `head_to_head_matches`, `head_to_head_win_rate`, `opponent_service_games_conceded_rate`, `career_to_date_mean`, `history_observations`, `best_of`, `surface`, `tourney_level`, `player_rank`, `opponent_rank`, `rank_difference`, `player_height_cm`

### Ensemble

The ensemble combines the versioned baseline and GBM predictions. Production weights remain configured static weights; evaluation-only weights use strictly earlier folds.

## Pooled metrics

| Target | Model | MAE | RMSE | Signed bias | Coverage | Rows | MAE improvement vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| aces | baseline_v1_aces | 3.5814 | 5.4118 | 0.4136 | 63.6% | 66610 | 0.00% |
| aces | gbm_v1_aces | 2.8561 | 4.0241 | -0.6138 | 77.2% | 66610 | 20.25% |
| aces | ensemble_v1_aces | 3.0484 | 4.2904 | -0.1024 | 70.7% | 66610 | 14.88% |
| double_faults | baseline_v1_double_faults | 1.7825 | 2.3887 | 0.0628 | 63.8% | 66610 | 0.00% |
| double_faults | gbm_v1_double_faults | 1.6332 | 2.2003 | -0.3045 | 78.5% | 66610 | 8.38% |
| double_faults | ensemble_v1_double_faults | 1.6620 | 2.2034 | -0.1210 | 70.7% | 66610 | 6.76% |
| service_games | baseline_v1_service_games | 3.7423 | 5.2720 | 0.4095 | 61.8% | 66595 | 0.00% |
| service_games | gbm_v1_service_games | 2.6997 | 3.4626 | -0.4998 | 77.0% | 66595 | 27.86% |
| service_games | ensemble_v1_service_games | 2.9630 | 3.8955 | -0.0463 | 71.4% | 66595 | 20.82% |

## Calibration

The headline metric is interval coverage: the fraction of realized outcomes inside `[lowerci, upperci]`. With 0.1 and 0.9 quantiles, a useful target is near 80%. Coverage that is too high usually means intervals are too wide or conservative. Coverage that is too low means intervals are too narrow.

### Prediction-ranked bins

| Target | Model | Prediction bin | Rows | Coverage |
|---|---|---:|---:|---:|
| aces | baseline_v1_aces | 01 | 6661 | 66.8% |
| aces | baseline_v1_aces | 02 | 6661 | 69.4% |
| aces | baseline_v1_aces | 03 | 6661 | 69.3% |
| aces | baseline_v1_aces | 04 | 6661 | 71.7% |
| aces | baseline_v1_aces | 05 | 6661 | 69.1% |
| aces | baseline_v1_aces | 06 | 6661 | 68.9% |
| aces | baseline_v1_aces | 07 | 6661 | 66.4% |
| aces | baseline_v1_aces | 08 | 6661 | 65.1% |
| aces | baseline_v1_aces | 09 | 6661 | 57.9% |
| aces | baseline_v1_aces | 10 | 6661 | 31.0% |
| aces | ensemble_v1_aces | 01 | 6661 | 68.3% |
| aces | ensemble_v1_aces | 02 | 6661 | 72.1% |
| aces | ensemble_v1_aces | 03 | 6661 | 75.2% |
| aces | ensemble_v1_aces | 04 | 6661 | 76.5% |
| aces | ensemble_v1_aces | 05 | 6661 | 74.1% |
| aces | ensemble_v1_aces | 06 | 6661 | 74.2% |
| aces | ensemble_v1_aces | 07 | 6661 | 72.4% |
| aces | ensemble_v1_aces | 08 | 6661 | 70.7% |
| aces | ensemble_v1_aces | 09 | 6661 | 68.3% |
| aces | ensemble_v1_aces | 10 | 6661 | 55.6% |
| aces | gbm_v1_aces | 01 | 6661 | 75.8% |
| aces | gbm_v1_aces | 02 | 6661 | 76.5% |
| aces | gbm_v1_aces | 03 | 6661 | 79.5% |
| aces | gbm_v1_aces | 04 | 6661 | 77.2% |
| aces | gbm_v1_aces | 05 | 6661 | 77.2% |
| aces | gbm_v1_aces | 06 | 6661 | 77.9% |
| aces | gbm_v1_aces | 07 | 6661 | 77.6% |
| aces | gbm_v1_aces | 08 | 6661 | 78.8% |
| aces | gbm_v1_aces | 09 | 6661 | 76.5% |
| aces | gbm_v1_aces | 10 | 6661 | 75.4% |
| double_faults | baseline_v1_double_faults | 01 | 6661 | 62.3% |
| double_faults | baseline_v1_double_faults | 02 | 6661 | 65.6% |
| double_faults | baseline_v1_double_faults | 03 | 6661 | 68.0% |
| double_faults | baseline_v1_double_faults | 04 | 6661 | 68.1% |
| double_faults | baseline_v1_double_faults | 05 | 6661 | 68.9% |
| double_faults | baseline_v1_double_faults | 06 | 6661 | 69.5% |
| double_faults | baseline_v1_double_faults | 07 | 6661 | 69.0% |
| double_faults | baseline_v1_double_faults | 08 | 6661 | 66.9% |
| double_faults | baseline_v1_double_faults | 09 | 6661 | 59.9% |
| double_faults | baseline_v1_double_faults | 10 | 6661 | 39.5% |
| double_faults | ensemble_v1_double_faults | 01 | 6661 | 68.6% |
| double_faults | ensemble_v1_double_faults | 02 | 6661 | 69.3% |
| double_faults | ensemble_v1_double_faults | 03 | 6661 | 70.3% |
| double_faults | ensemble_v1_double_faults | 04 | 6661 | 73.1% |
| double_faults | ensemble_v1_double_faults | 05 | 6661 | 73.2% |
| double_faults | ensemble_v1_double_faults | 06 | 6661 | 75.3% |
| double_faults | ensemble_v1_double_faults | 07 | 6661 | 74.2% |
| double_faults | ensemble_v1_double_faults | 08 | 6661 | 71.4% |
| double_faults | ensemble_v1_double_faults | 09 | 6661 | 69.6% |
| double_faults | ensemble_v1_double_faults | 10 | 6661 | 62.2% |
| double_faults | gbm_v1_double_faults | 01 | 6661 | 79.7% |
| double_faults | gbm_v1_double_faults | 02 | 6661 | 77.9% |
| double_faults | gbm_v1_double_faults | 03 | 6661 | 78.5% |
| double_faults | gbm_v1_double_faults | 04 | 6661 | 77.8% |
| double_faults | gbm_v1_double_faults | 05 | 6661 | 78.4% |
| double_faults | gbm_v1_double_faults | 06 | 6661 | 79.3% |
| double_faults | gbm_v1_double_faults | 07 | 6661 | 79.9% |
| double_faults | gbm_v1_double_faults | 08 | 6661 | 79.3% |
| double_faults | gbm_v1_double_faults | 09 | 6661 | 76.7% |
| double_faults | gbm_v1_double_faults | 10 | 6661 | 77.9% |
| service_games | baseline_v1_service_games | 01 | 6659 | 49.7% |
| service_games | baseline_v1_service_games | 02 | 6660 | 60.0% |
| service_games | baseline_v1_service_games | 03 | 6659 | 64.4% |
| service_games | baseline_v1_service_games | 04 | 6660 | 67.9% |
| service_games | baseline_v1_service_games | 05 | 6659 | 73.1% |
| service_games | baseline_v1_service_games | 06 | 6660 | 77.5% |
| service_games | baseline_v1_service_games | 07 | 6659 | 83.5% |
| service_games | baseline_v1_service_games | 08 | 6660 | 86.5% |
| service_games | baseline_v1_service_games | 09 | 6659 | 40.4% |
| service_games | baseline_v1_service_games | 10 | 6660 | 15.2% |
| service_games | ensemble_v1_service_games | 01 | 6659 | 69.8% |
| service_games | ensemble_v1_service_games | 02 | 6660 | 70.8% |
| service_games | ensemble_v1_service_games | 03 | 6659 | 71.9% |
| service_games | ensemble_v1_service_games | 04 | 6660 | 76.5% |
| service_games | ensemble_v1_service_games | 05 | 6659 | 78.6% |
| service_games | ensemble_v1_service_games | 06 | 6660 | 80.6% |
| service_games | ensemble_v1_service_games | 07 | 6659 | 83.9% |
| service_games | ensemble_v1_service_games | 08 | 6660 | 85.6% |
| service_games | ensemble_v1_service_games | 09 | 6659 | 52.5% |
| service_games | ensemble_v1_service_games | 10 | 6660 | 43.2% |
| service_games | gbm_v1_service_games | 01 | 6659 | 78.1% |
| service_games | gbm_v1_service_games | 02 | 6660 | 77.5% |
| service_games | gbm_v1_service_games | 03 | 6659 | 77.3% |
| service_games | gbm_v1_service_games | 04 | 6660 | 76.7% |
| service_games | gbm_v1_service_games | 05 | 6659 | 77.5% |
| service_games | gbm_v1_service_games | 06 | 6660 | 78.7% |
| service_games | gbm_v1_service_games | 07 | 6659 | 79.0% |
| service_games | gbm_v1_service_games | 08 | 6660 | 78.0% |
| service_games | gbm_v1_service_games | 09 | 6659 | 73.5% |
| service_games | gbm_v1_service_games | 10 | 6660 | 74.2% |

### Fold-level bias-sign review

| Target | Model | Positive folds | Negative folds | Dominant sign share | Review |
|---|---|---:|---:|---:|---|
| aces | baseline_v1_aces | 65 | 64 | 50.4% | mixed |
| aces | gbm_v1_aces | 20 | 109 | 84.5% | FLAG: negative in most folds |
| aces | ensemble_v1_aces | 51 | 78 | 60.5% | FLAG: negative in most folds |
| double_faults | baseline_v1_double_faults | 74 | 55 | 57.4% | mixed |
| double_faults | gbm_v1_double_faults | 36 | 93 | 72.1% | FLAG: negative in most folds |
| double_faults | ensemble_v1_double_faults | 59 | 70 | 54.3% | mixed |
| service_games | baseline_v1_service_games | 68 | 61 | 52.7% | mixed |
| service_games | gbm_v1_service_games | 13 | 116 | 89.9% | FLAG: negative in most folds |
| service_games | ensemble_v1_service_games | 58 | 71 | 55.0% | mixed |

## Expectation reconciliation

- Baseline aces MAE 3.4–4.1: **PASS** (3.5814).
- GBM aces improvement 3–8%: **FAIL** (20.25%).
- Ensemble aces improvement over GBM 1–3%: **FAIL** (-6.73%).
- baseline_v1 aces interval coverage 0.75–0.85: **FAIL** (63.6%).
- gbm_v1 aces interval coverage 0.75–0.85: **PASS** (77.2%).
- ensemble_v1 aces interval coverage 0.75–0.85: **FAIL** (70.7%).
- GBM double_faults improvement 3–8%: **FAIL** (8.38%).
- Ensemble double_faults improvement over GBM 1–3%: **FAIL** (-1.77%).
- baseline_v1 double_faults interval coverage 0.75–0.85: **FAIL** (63.8%).
- gbm_v1 double_faults interval coverage 0.75–0.85: **PASS** (78.5%).
- ensemble_v1 double_faults interval coverage 0.75–0.85: **FAIL** (70.7%).
- GBM service_games improvement 3–8%: **FAIL** (27.86%).
- Ensemble service_games improvement over GBM 1–3%: **FAIL** (-9.75%).
- baseline_v1 service_games interval coverage 0.75–0.85: **FAIL** (61.8%).
- gbm_v1 service_games interval coverage 0.75–0.85: **PASS** (77.0%).
- ensemble_v1 service_games interval coverage 0.75–0.85: **FAIL** (71.4%).
- Any FAIL is not treated as success. It requires a leakage and data-boundary review before the model is trusted, including when the result is better than expected.

## Known limitations

- `games_won` and `sets_won` are conceptually empty in the current match store: the source transform leaves both fields NULL, so they are disabled targets rather than usable features.
- Event dates are estimated from tournament start dates using `ROUND_OFFSETS` in the Sackmann ETL. The round ordering is useful for chronology, but the absolute dates are approximate.
- Market comparison sample: 0 paired prediction/line/result rows. The current market comparison is empty because the feature and odds data domains do not intersect; it is not explained by the odds capture start date.
- The baseline interval is a rolling-standard-deviation heuristic, not a calibrated probability interval.

## Conditions for not trusting a prediction

- The player lacks the configured minimum history or key features are NULL.
- Fold-level coverage is unstable or materially outside 0.75–0.85.
- Mean bias has the same sign across most folds without a documented reason.
- The result is outside the pre-registered expectation ranges until leakage and data-boundary causes have been investigated.
- A market comparison or betting conclusion is based on the current tiny odds sample.

## Market comparison

Market comparison sample: 0 paired prediction/line/result rows.

Prediction/line pairs before a known result: 0. Known-result pairs: 0. Providers: none.
No hit rate or ROI is reported because the sample is not yet informative.

## Data coverage

- The feature pipeline is ATP men only: it selects `players.tour = 'ATP'`.
- The captured odds archive to date is 100% WTA.
- Captured markets are Sets Won, Games Won, and Break Points Won.
- Active model targets are aces, double faults, and service games.
- Therefore the current model/market intersection is empty. Collecting more rows under the current configuration will not create a paired row; the domain mismatch is documented here rather than changed in this cleanup.
