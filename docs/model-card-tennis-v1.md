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
| aces | absolute error | baseline_v1_aces | 129 | 0.4893 | 0.4682–0.7673 |
| aces | absolute error | gbm_v1_aces | 129 | 0.5107 | 0.2327–0.5318 |
| aces | squared error | baseline_v1_aces | 129 | 0.4976 | 0.4645–0.7544 |
| aces | squared error | gbm_v1_aces | 129 | 0.5024 | 0.2456–0.5355 |
| double_faults | absolute error | baseline_v1_double_faults | 129 | 0.4944 | 0.4892–0.5569 |
| double_faults | absolute error | gbm_v1_double_faults | 129 | 0.5056 | 0.4431–0.5108 |
| double_faults | squared error | baseline_v1_double_faults | 129 | 0.4994 | 0.4963–0.5580 |
| double_faults | squared error | gbm_v1_double_faults | 129 | 0.5006 | 0.4420–0.5037 |
| service_games | absolute error | baseline_v1_service_games | 129 | 0.4906 | 0.4777–0.6551 |
| service_games | absolute error | gbm_v1_service_games | 129 | 0.5094 | 0.3449–0.5223 |
| service_games | squared error | baseline_v1_service_games | 129 | 0.4993 | 0.4907–0.6181 |
| service_games | squared error | gbm_v1_service_games | 129 | 0.5007 | 0.3819–0.5093 |

### OOF objective comparison

| Target | OOF objective | Pooled ensemble MAE |
|---|---|---:|
| aces | absolute error | 3.0313 |
| aces | squared error | 3.0377 |
| double_faults | absolute error | 1.6579 |
| double_faults | squared error | 1.6588 |
| service_games | absolute error | 2.9450 |
| service_games | squared error | 2.9552 |

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

| Target | Model | MAE | RMSE | Signed bias | Coverage | Rows | Interval crossings | Interval repairs | MAE improvement vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| aces | baseline_v1_aces | 3.5613 | 5.3793 | 0.3964 | 63.8% | 66108 | 0.0000 | 0.0000 | 0.00% |
| aces | gbm_v1_aces | 2.8526 | 4.0191 | -0.6111 | 77.3% | 66108 | 0.0000 | 0.0000 | 19.90% |
| aces | ensemble_v1_aces | 3.0313 | 4.2621 | -0.1200 | 71.0% | 66108 | 0.0000 | 0.0000 | 14.88% |
| double_faults | baseline_v1_double_faults | 1.7774 | 2.3818 | 0.0562 | 63.9% | 66108 | 0.0000 | 0.0000 | 0.00% |
| double_faults | gbm_v1_double_faults | 1.6292 | 2.1935 | -0.2993 | 78.5% | 66108 | 0.0000 | 0.0000 | 8.34% |
| double_faults | ensemble_v1_double_faults | 1.6579 | 2.1980 | -0.1237 | 70.8% | 66108 | 0.0000 | 0.0000 | 6.72% |
| service_games | baseline_v1_service_games | 3.7270 | 5.2500 | 0.3873 | 62.0% | 66093 | 0.0000 | 0.0000 | 0.00% |
| service_games | gbm_v1_service_games | 2.6965 | 3.4593 | -0.4997 | 77.1% | 66093 | 0.0000 | 0.0000 | 27.65% |
| service_games | ensemble_v1_service_games | 2.9450 | 3.8670 | -0.0673 | 71.6% | 66093 | 0.0000 | 0.0000 | 20.98% |

## Calibration

The headline metric is interval coverage: the fraction of realized outcomes inside `[lowerci, upperci]`. With 0.1 and 0.9 quantiles, a useful target is near 80%. Coverage that is too high usually means intervals are too wide or conservative. Coverage that is too low means intervals are too narrow.
Pooled metric rows also report interval crossings and repaired rows. Unavailable means the append-only run predates that instrumentation.

### Prediction-ranked bins

| Target | Model | Prediction bin | Rows | Coverage |
|---|---|---:|---:|---:|
| aces | baseline_v1_aces | 01 | 6610 | 67.0% |
| aces | baseline_v1_aces | 02 | 6611 | 69.5% |
| aces | baseline_v1_aces | 03 | 6611 | 69.4% |
| aces | baseline_v1_aces | 04 | 6611 | 71.7% |
| aces | baseline_v1_aces | 05 | 6611 | 69.2% |
| aces | baseline_v1_aces | 06 | 6610 | 68.9% |
| aces | baseline_v1_aces | 07 | 6611 | 66.4% |
| aces | baseline_v1_aces | 08 | 6611 | 65.3% |
| aces | baseline_v1_aces | 09 | 6611 | 58.4% |
| aces | baseline_v1_aces | 10 | 6611 | 31.7% |
| aces | ensemble_v1_aces | 01 | 6610 | 68.4% |
| aces | ensemble_v1_aces | 02 | 6611 | 72.5% |
| aces | ensemble_v1_aces | 03 | 6611 | 75.5% |
| aces | ensemble_v1_aces | 04 | 6611 | 76.6% |
| aces | ensemble_v1_aces | 05 | 6611 | 74.1% |
| aces | ensemble_v1_aces | 06 | 6610 | 74.4% |
| aces | ensemble_v1_aces | 07 | 6611 | 72.5% |
| aces | ensemble_v1_aces | 08 | 6611 | 71.1% |
| aces | ensemble_v1_aces | 09 | 6611 | 68.6% |
| aces | ensemble_v1_aces | 10 | 6611 | 56.5% |
| aces | gbm_v1_aces | 01 | 6610 | 75.8% |
| aces | gbm_v1_aces | 02 | 6611 | 76.6% |
| aces | gbm_v1_aces | 03 | 6611 | 79.5% |
| aces | gbm_v1_aces | 04 | 6611 | 77.3% |
| aces | gbm_v1_aces | 05 | 6611 | 77.1% |
| aces | gbm_v1_aces | 06 | 6610 | 77.9% |
| aces | gbm_v1_aces | 07 | 6611 | 77.7% |
| aces | gbm_v1_aces | 08 | 6611 | 78.9% |
| aces | gbm_v1_aces | 09 | 6611 | 76.4% |
| aces | gbm_v1_aces | 10 | 6611 | 75.3% |
| double_faults | baseline_v1_double_faults | 01 | 6610 | 62.2% |
| double_faults | baseline_v1_double_faults | 02 | 6611 | 65.8% |
| double_faults | baseline_v1_double_faults | 03 | 6611 | 67.9% |
| double_faults | baseline_v1_double_faults | 04 | 6611 | 68.2% |
| double_faults | baseline_v1_double_faults | 05 | 6611 | 68.9% |
| double_faults | baseline_v1_double_faults | 06 | 6610 | 69.5% |
| double_faults | baseline_v1_double_faults | 07 | 6611 | 69.1% |
| double_faults | baseline_v1_double_faults | 08 | 6611 | 67.0% |
| double_faults | baseline_v1_double_faults | 09 | 6611 | 60.0% |
| double_faults | baseline_v1_double_faults | 10 | 6611 | 40.1% |
| double_faults | ensemble_v1_double_faults | 01 | 6610 | 68.7% |
| double_faults | ensemble_v1_double_faults | 02 | 6611 | 69.4% |
| double_faults | ensemble_v1_double_faults | 03 | 6611 | 70.4% |
| double_faults | ensemble_v1_double_faults | 04 | 6611 | 73.0% |
| double_faults | ensemble_v1_double_faults | 05 | 6611 | 73.4% |
| double_faults | ensemble_v1_double_faults | 06 | 6610 | 75.4% |
| double_faults | ensemble_v1_double_faults | 07 | 6611 | 74.3% |
| double_faults | ensemble_v1_double_faults | 08 | 6611 | 71.5% |
| double_faults | ensemble_v1_double_faults | 09 | 6611 | 69.7% |
| double_faults | ensemble_v1_double_faults | 10 | 6611 | 62.6% |
| double_faults | gbm_v1_double_faults | 01 | 6610 | 79.6% |
| double_faults | gbm_v1_double_faults | 02 | 6611 | 77.9% |
| double_faults | gbm_v1_double_faults | 03 | 6611 | 78.5% |
| double_faults | gbm_v1_double_faults | 04 | 6611 | 77.8% |
| double_faults | gbm_v1_double_faults | 05 | 6611 | 78.4% |
| double_faults | gbm_v1_double_faults | 06 | 6610 | 79.3% |
| double_faults | gbm_v1_double_faults | 07 | 6611 | 79.8% |
| double_faults | gbm_v1_double_faults | 08 | 6611 | 79.4% |
| double_faults | gbm_v1_double_faults | 09 | 6611 | 76.8% |
| double_faults | gbm_v1_double_faults | 10 | 6611 | 78.0% |
| service_games | baseline_v1_service_games | 01 | 6609 | 49.7% |
| service_games | baseline_v1_service_games | 02 | 6609 | 59.9% |
| service_games | baseline_v1_service_games | 03 | 6609 | 64.4% |
| service_games | baseline_v1_service_games | 04 | 6610 | 68.0% |
| service_games | baseline_v1_service_games | 05 | 6609 | 73.2% |
| service_games | baseline_v1_service_games | 06 | 6609 | 77.4% |
| service_games | baseline_v1_service_games | 07 | 6610 | 83.4% |
| service_games | baseline_v1_service_games | 08 | 6609 | 86.5% |
| service_games | baseline_v1_service_games | 09 | 6609 | 41.9% |
| service_games | baseline_v1_service_games | 10 | 6610 | 15.2% |
| service_games | ensemble_v1_service_games | 01 | 6609 | 69.8% |
| service_games | ensemble_v1_service_games | 02 | 6609 | 70.9% |
| service_games | ensemble_v1_service_games | 03 | 6609 | 72.1% |
| service_games | ensemble_v1_service_games | 04 | 6610 | 76.6% |
| service_games | ensemble_v1_service_games | 05 | 6609 | 78.7% |
| service_games | ensemble_v1_service_games | 06 | 6609 | 80.6% |
| service_games | ensemble_v1_service_games | 07 | 6610 | 83.8% |
| service_games | ensemble_v1_service_games | 08 | 6609 | 85.7% |
| service_games | ensemble_v1_service_games | 09 | 6609 | 53.6% |
| service_games | ensemble_v1_service_games | 10 | 6610 | 44.0% |
| service_games | gbm_v1_service_games | 01 | 6609 | 78.2% |
| service_games | gbm_v1_service_games | 02 | 6609 | 77.6% |
| service_games | gbm_v1_service_games | 03 | 6609 | 77.3% |
| service_games | gbm_v1_service_games | 04 | 6610 | 76.8% |
| service_games | gbm_v1_service_games | 05 | 6609 | 77.6% |
| service_games | gbm_v1_service_games | 06 | 6609 | 78.6% |
| service_games | gbm_v1_service_games | 07 | 6610 | 78.9% |
| service_games | gbm_v1_service_games | 08 | 6609 | 78.2% |
| service_games | gbm_v1_service_games | 09 | 6609 | 73.4% |
| service_games | gbm_v1_service_games | 10 | 6610 | 74.1% |

### Fold-level bias-sign review

| Target | Model | Positive folds | Negative folds | Dominant sign share | Review |
|---|---|---:|---:|---:|---|
| aces | baseline_v1_aces | 65 | 64 | 50.4% | mixed |
| aces | gbm_v1_aces | 20 | 109 | 84.5% | FLAG: negative in most folds |
| aces | ensemble_v1_aces | 51 | 78 | 60.5% | FLAG: negative in most folds |
| double_faults | baseline_v1_double_faults | 73 | 56 | 56.6% | mixed |
| double_faults | gbm_v1_double_faults | 36 | 93 | 72.1% | FLAG: negative in most folds |
| double_faults | ensemble_v1_double_faults | 59 | 70 | 54.3% | mixed |
| service_games | baseline_v1_service_games | 68 | 61 | 52.7% | mixed |
| service_games | gbm_v1_service_games | 13 | 116 | 89.9% | FLAG: negative in most folds |
| service_games | ensemble_v1_service_games | 58 | 71 | 55.0% | mixed |

## Expectation reconciliation

- Baseline aces MAE 3.4–4.1: **PASS** (3.5613).
- GBM aces improvement 3–8%: **FAIL** (19.90%).
- Ensemble aces improvement over GBM 1–3%: **FAIL** (-6.26%).
- baseline_v1 aces interval coverage 0.75–0.85: **FAIL** (63.8%).
- gbm_v1 aces interval coverage 0.75–0.85: **PASS** (77.3%).
- ensemble_v1 aces interval coverage 0.75–0.85: **FAIL** (71.0%).
- GBM double_faults improvement 3–8%: **FAIL** (8.34%).
- Ensemble double_faults improvement over GBM 1–3%: **FAIL** (-1.77%).
- baseline_v1 double_faults interval coverage 0.75–0.85: **FAIL** (63.9%).
- gbm_v1 double_faults interval coverage 0.75–0.85: **PASS** (78.5%).
- ensemble_v1 double_faults interval coverage 0.75–0.85: **FAIL** (70.8%).
- GBM service_games improvement 3–8%: **FAIL** (27.65%).
- Ensemble service_games improvement over GBM 1–3%: **FAIL** (-9.21%).
- baseline_v1 service_games interval coverage 0.75–0.85: **FAIL** (62.0%).
- gbm_v1 service_games interval coverage 0.75–0.85: **PASS** (77.1%).
- ensemble_v1 service_games interval coverage 0.75–0.85: **FAIL** (71.6%).
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
