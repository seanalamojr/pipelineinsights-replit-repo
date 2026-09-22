# Checkpoint 12 — Historical backtest and calibration

Evaluation window: `2015-01-01` through `2026-10-01` (monthly folds; test end is exclusive).
Scored monthly folds: aces=129, double_faults=129, service_games=129. Calendar windows without a test row or without strictly earlier training rows are not scored.

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

## Fold-level interval coverage

| Target | Model | Fold | Cutoff | Test end | Rows | Coverage |
|---|---|---:|---|---|---:|---:|
| aces | baseline_v1_aces | 2 | 2015-02-01 | 2015-03-01 | 426 | 59.2% |
| aces | baseline_v1_aces | 3 | 2015-03-01 | 2015-04-01 | 344 | 66.3% |
| aces | baseline_v1_aces | 4 | 2015-04-01 | 2015-05-01 | 413 | 76.3% |
| aces | baseline_v1_aces | 5 | 2015-05-01 | 2015-06-01 | 580 | 44.3% |
| aces | baseline_v1_aces | 6 | 2015-06-01 | 2015-07-01 | 476 | 52.7% |
| aces | baseline_v1_aces | 7 | 2015-07-01 | 2015-08-01 | 368 | 60.3% |
| aces | baseline_v1_aces | 8 | 2015-08-01 | 2015-09-01 | 574 | 62.5% |
| aces | baseline_v1_aces | 9 | 2015-09-01 | 2015-10-01 | 262 | 48.5% |
| aces | baseline_v1_aces | 10 | 2015-10-01 | 2015-11-01 | 544 | 71.7% |
| aces | baseline_v1_aces | 11 | 2015-11-01 | 2015-12-01 | 128 | 65.6% |
| aces | baseline_v1_aces | 13 | 2016-01-01 | 2016-02-01 | 479 | 50.7% |
| aces | baseline_v1_aces | 14 | 2016-02-01 | 2016-03-01 | 631 | 74.3% |
| aces | baseline_v1_aces | 15 | 2016-03-01 | 2016-04-01 | 431 | 71.9% |
| aces | baseline_v1_aces | 16 | 2016-04-01 | 2016-05-01 | 486 | 79.4% |
| aces | baseline_v1_aces | 17 | 2016-05-01 | 2016-06-01 | 560 | 60.4% |
| aces | baseline_v1_aces | 18 | 2016-06-01 | 2016-07-01 | 526 | 39.7% |
| aces | baseline_v1_aces | 19 | 2016-07-01 | 2016-08-01 | 564 | 68.8% |
| aces | baseline_v1_aces | 20 | 2016-08-01 | 2016-09-01 | 633 | 54.3% |
| aces | baseline_v1_aces | 21 | 2016-09-01 | 2016-10-01 | 278 | 53.2% |
| aces | baseline_v1_aces | 22 | 2016-10-01 | 2016-11-01 | 514 | 72.2% |
| aces | baseline_v1_aces | 23 | 2016-11-01 | 2016-12-01 | 130 | 64.6% |
| aces | baseline_v1_aces | 25 | 2017-01-01 | 2017-02-01 | 492 | 46.5% |
| aces | baseline_v1_aces | 26 | 2017-02-01 | 2017-03-01 | 562 | 71.4% |
| aces | baseline_v1_aces | 27 | 2017-03-01 | 2017-04-01 | 544 | 71.5% |
| aces | baseline_v1_aces | 28 | 2017-04-01 | 2017-05-01 | 434 | 76.0% |
| aces | baseline_v1_aces | 29 | 2017-05-01 | 2017-06-01 | 676 | 62.0% |
| aces | baseline_v1_aces | 30 | 2017-06-01 | 2017-07-01 | 346 | 56.9% |
| aces | baseline_v1_aces | 31 | 2017-07-01 | 2017-08-01 | 573 | 47.6% |
| aces | baseline_v1_aces | 32 | 2017-08-01 | 2017-09-01 | 720 | 55.1% |
| aces | baseline_v1_aces | 33 | 2017-09-01 | 2017-10-01 | 289 | 59.9% |
| aces | baseline_v1_aces | 34 | 2017-10-01 | 2017-11-01 | 550 | 68.7% |
| aces | baseline_v1_aces | 35 | 2017-11-01 | 2017-12-01 | 123 | 67.5% |
| aces | baseline_v1_aces | 37 | 2018-01-01 | 2018-02-01 | 498 | 51.6% |
| aces | baseline_v1_aces | 38 | 2018-02-01 | 2018-03-01 | 670 | 74.0% |
| aces | baseline_v1_aces | 39 | 2018-03-01 | 2018-04-01 | 458 | 73.1% |
| aces | baseline_v1_aces | 40 | 2018-04-01 | 2018-05-01 | 451 | 78.0% |
| aces | baseline_v1_aces | 41 | 2018-05-01 | 2018-06-01 | 712 | 60.8% |
| aces | baseline_v1_aces | 42 | 2018-06-01 | 2018-07-01 | 335 | 57.0% |
| aces | baseline_v1_aces | 43 | 2018-07-01 | 2018-08-01 | 592 | 51.0% |
| aces | baseline_v1_aces | 44 | 2018-08-01 | 2018-09-01 | 711 | 60.3% |
| aces | baseline_v1_aces | 45 | 2018-09-01 | 2018-10-01 | 286 | 68.9% |
| aces | baseline_v1_aces | 46 | 2018-10-01 | 2018-11-01 | 559 | 68.2% |
| aces | baseline_v1_aces | 47 | 2018-11-01 | 2018-12-01 | 95 | 67.4% |
| aces | baseline_v1_aces | 49 | 2019-01-01 | 2019-02-01 | 521 | 55.1% |
| aces | baseline_v1_aces | 50 | 2019-02-01 | 2019-03-01 | 683 | 76.3% |
| aces | baseline_v1_aces | 51 | 2019-03-01 | 2019-04-01 | 409 | 77.0% |
| aces | baseline_v1_aces | 52 | 2019-04-01 | 2019-05-01 | 362 | 80.9% |
| aces | baseline_v1_aces | 53 | 2019-05-01 | 2019-06-01 | 658 | 63.5% |
| aces | baseline_v1_aces | 54 | 2019-06-01 | 2019-07-01 | 333 | 62.2% |
| aces | baseline_v1_aces | 55 | 2019-07-01 | 2019-08-01 | 672 | 50.9% |
| aces | baseline_v1_aces | 56 | 2019-08-01 | 2019-09-01 | 639 | 51.6% |
| aces | baseline_v1_aces | 57 | 2019-09-01 | 2019-10-01 | 214 | 70.6% |
| aces | baseline_v1_aces | 58 | 2019-10-01 | 2019-11-01 | 590 | 68.8% |
| aces | baseline_v1_aces | 59 | 2019-11-01 | 2019-12-01 | 169 | 63.3% |
| aces | baseline_v1_aces | 61 | 2020-01-01 | 2020-02-01 | 562 | 53.0% |
| aces | baseline_v1_aces | 62 | 2020-02-01 | 2020-03-01 | 641 | 72.1% |
| aces | baseline_v1_aces | 63 | 2020-03-01 | 2020-04-01 | 108 | 64.8% |
| aces | baseline_v1_aces | 68 | 2020-08-01 | 2020-09-01 | 229 | 52.4% |
| aces | baseline_v1_aces | 69 | 2020-09-01 | 2020-10-01 | 552 | 56.9% |
| aces | baseline_v1_aces | 70 | 2020-10-01 | 2020-11-01 | 400 | 73.2% |
| aces | baseline_v1_aces | 71 | 2020-11-01 | 2020-12-01 | 192 | 64.6% |
| aces | baseline_v1_aces | 73 | 2021-01-01 | 2021-02-01 | 102 | 85.3% |
| aces | baseline_v1_aces | 74 | 2021-02-01 | 2021-03-01 | 633 | 54.7% |
| aces | baseline_v1_aces | 75 | 2021-03-01 | 2021-04-01 | 602 | 70.6% |
| aces | baseline_v1_aces | 76 | 2021-04-01 | 2021-05-01 | 451 | 84.0% |
| aces | baseline_v1_aces | 77 | 2021-05-01 | 2021-06-01 | 550 | 67.6% |
| aces | baseline_v1_aces | 78 | 2021-06-01 | 2021-07-01 | 619 | 44.4% |
| aces | baseline_v1_aces | 79 | 2021-07-01 | 2021-08-01 | 433 | 64.9% |
| aces | baseline_v1_aces | 80 | 2021-08-01 | 2021-09-01 | 578 | 57.1% |
| aces | baseline_v1_aces | 81 | 2021-09-01 | 2021-10-01 | 306 | 61.4% |
| aces | baseline_v1_aces | 82 | 2021-10-01 | 2021-11-01 | 436 | 73.9% |
| aces | baseline_v1_aces | 83 | 2021-11-01 | 2021-12-01 | 296 | 68.6% |
| aces | baseline_v1_aces | 84 | 2021-12-01 | 2022-01-01 | 20 | 85.0% |
| aces | baseline_v1_aces | 85 | 2022-01-01 | 2022-02-01 | 564 | 52.0% |
| aces | baseline_v1_aces | 86 | 2022-02-01 | 2022-03-01 | 708 | 75.0% |
| aces | baseline_v1_aces | 87 | 2022-03-01 | 2022-04-01 | 458 | 73.4% |
| aces | baseline_v1_aces | 88 | 2022-04-01 | 2022-05-01 | 460 | 77.8% |
| aces | baseline_v1_aces | 89 | 2022-05-01 | 2022-06-01 | 562 | 59.4% |
| aces | baseline_v1_aces | 90 | 2022-06-01 | 2022-07-01 | 552 | 42.8% |
| aces | baseline_v1_aces | 91 | 2022-07-01 | 2022-08-01 | 368 | 71.5% |
| aces | baseline_v1_aces | 92 | 2022-08-01 | 2022-09-01 | 661 | 60.8% |
| aces | baseline_v1_aces | 93 | 2022-09-01 | 2022-10-01 | 261 | 64.8% |
| aces | baseline_v1_aces | 94 | 2022-10-01 | 2022-11-01 | 507 | 72.0% |
| aces | baseline_v1_aces | 95 | 2022-11-01 | 2022-12-01 | 163 | 62.6% |
| aces | baseline_v1_aces | 97 | 2023-01-01 | 2023-02-01 | 543 | 49.2% |
| aces | baseline_v1_aces | 98 | 2023-02-01 | 2023-03-01 | 475 | 70.7% |
| aces | baseline_v1_aces | 99 | 2023-03-01 | 2023-04-01 | 543 | 71.6% |
| aces | baseline_v1_aces | 100 | 2023-04-01 | 2023-05-01 | 638 | 74.8% |
| aces | baseline_v1_aces | 101 | 2023-05-01 | 2023-06-01 | 494 | 64.0% |
| aces | baseline_v1_aces | 102 | 2023-06-01 | 2023-07-01 | 350 | 61.7% |
| aces | baseline_v1_aces | 103 | 2023-07-01 | 2023-08-01 | 567 | 51.0% |
| aces | baseline_v1_aces | 104 | 2023-08-01 | 2023-09-01 | 719 | 56.5% |
| aces | baseline_v1_aces | 105 | 2023-09-01 | 2023-10-01 | 296 | 69.6% |
| aces | baseline_v1_aces | 106 | 2023-10-01 | 2023-11-01 | 527 | 71.5% |
| aces | baseline_v1_aces | 107 | 2023-11-01 | 2023-12-01 | 238 | 58.4% |
| aces | baseline_v1_aces | 108 | 2023-12-01 | 2024-01-01 | 6 | 66.7% |
| aces | baseline_v1_aces | 109 | 2024-01-01 | 2024-02-01 | 532 | 51.3% |
| aces | baseline_v1_aces | 110 | 2024-02-01 | 2024-03-01 | 743 | 73.8% |
| aces | baseline_v1_aces | 111 | 2024-03-01 | 2024-04-01 | 412 | 73.3% |
| aces | baseline_v1_aces | 112 | 2024-04-01 | 2024-05-01 | 642 | 77.9% |
| aces | baseline_v1_aces | 113 | 2024-05-01 | 2024-06-01 | 527 | 60.7% |
| aces | baseline_v1_aces | 114 | 2024-06-01 | 2024-07-01 | 329 | 60.2% |
| aces | baseline_v1_aces | 115 | 2024-07-01 | 2024-08-01 | 756 | 55.4% |
| aces | baseline_v1_aces | 116 | 2024-08-01 | 2024-09-01 | 603 | 55.2% |
| aces | baseline_v1_aces | 117 | 2024-09-01 | 2024-10-01 | 342 | 67.3% |
| aces | baseline_v1_aces | 118 | 2024-10-01 | 2024-11-01 | 568 | 72.7% |
| aces | baseline_v1_aces | 119 | 2024-11-01 | 2024-12-01 | 175 | 60.6% |
| aces | baseline_v1_aces | 120 | 2024-12-01 | 2025-01-01 | 69 | 55.1% |
| aces | baseline_v1_aces | 121 | 2025-01-01 | 2025-02-01 | 518 | 48.6% |
| aces | baseline_v1_aces | 122 | 2025-02-01 | 2025-03-01 | 563 | 68.7% |
| aces | baseline_v1_aces | 123 | 2025-03-01 | 2025-04-01 | 387 | 69.8% |
| aces | baseline_v1_aces | 124 | 2025-04-01 | 2025-05-01 | 570 | 79.5% |
| aces | baseline_v1_aces | 125 | 2025-05-01 | 2025-06-01 | 540 | 69.3% |
| aces | baseline_v1_aces | 126 | 2025-06-01 | 2025-07-01 | 455 | 51.9% |
| aces | baseline_v1_aces | 127 | 2025-07-01 | 2025-08-01 | 635 | 61.7% |
| aces | baseline_v1_aces | 128 | 2025-08-01 | 2025-09-01 | 531 | 46.3% |
| aces | baseline_v1_aces | 129 | 2025-09-01 | 2025-10-01 | 247 | 61.1% |
| aces | baseline_v1_aces | 130 | 2025-10-01 | 2025-11-01 | 570 | 69.5% |
| aces | baseline_v1_aces | 131 | 2025-11-01 | 2025-12-01 | 134 | 64.2% |
| aces | baseline_v1_aces | 132 | 2025-12-01 | 2026-01-01 | 27 | 33.3% |
| aces | baseline_v1_aces | 133 | 2026-01-01 | 2026-02-01 | 217 | 52.5% |
| aces | baseline_v1_aces | 134 | 2026-02-01 | 2026-03-01 | 1009 | 65.1% |
| aces | baseline_v1_aces | 135 | 2026-03-01 | 2026-04-01 | 1365 | 68.9% |
| aces | baseline_v1_aces | 136 | 2026-04-01 | 2026-05-01 | 1857 | 69.8% |
| aces | baseline_v1_aces | 137 | 2026-05-01 | 2026-06-01 | 1546 | 70.2% |
| aces | baseline_v1_aces | 138 | 2026-06-01 | 2026-07-01 | 1542 | 60.7% |
| aces | baseline_v1_aces | 139 | 2026-07-01 | 2026-08-01 | 1862 | 60.6% |
| aces | baseline_v1_aces | 140 | 2026-08-01 | 2026-09-01 | 1606 | 65.3% |
| aces | baseline_v1_aces | 141 | 2026-09-01 | 2026-10-01 | 1088 | 57.7% |
| aces | ensemble_v1_aces | 2 | 2015-02-01 | 2015-03-01 | 426 | 61.5% |
| aces | ensemble_v1_aces | 3 | 2015-03-01 | 2015-04-01 | 344 | 70.1% |
| aces | ensemble_v1_aces | 4 | 2015-04-01 | 2015-05-01 | 413 | 76.3% |
| aces | ensemble_v1_aces | 5 | 2015-05-01 | 2015-06-01 | 580 | 56.7% |
| aces | ensemble_v1_aces | 6 | 2015-06-01 | 2015-07-01 | 476 | 61.1% |
| aces | ensemble_v1_aces | 7 | 2015-07-01 | 2015-08-01 | 368 | 64.1% |
| aces | ensemble_v1_aces | 8 | 2015-08-01 | 2015-09-01 | 574 | 69.0% |
| aces | ensemble_v1_aces | 9 | 2015-09-01 | 2015-10-01 | 262 | 64.5% |
| aces | ensemble_v1_aces | 10 | 2015-10-01 | 2015-11-01 | 544 | 77.0% |
| aces | ensemble_v1_aces | 11 | 2015-11-01 | 2015-12-01 | 128 | 71.9% |
| aces | ensemble_v1_aces | 13 | 2016-01-01 | 2016-02-01 | 479 | 67.4% |
| aces | ensemble_v1_aces | 14 | 2016-02-01 | 2016-03-01 | 631 | 75.9% |
| aces | ensemble_v1_aces | 15 | 2016-03-01 | 2016-04-01 | 431 | 72.4% |
| aces | ensemble_v1_aces | 16 | 2016-04-01 | 2016-05-01 | 486 | 77.0% |
| aces | ensemble_v1_aces | 17 | 2016-05-01 | 2016-06-01 | 560 | 71.4% |
| aces | ensemble_v1_aces | 18 | 2016-06-01 | 2016-07-01 | 526 | 58.9% |
| aces | ensemble_v1_aces | 19 | 2016-07-01 | 2016-08-01 | 564 | 72.7% |
| aces | ensemble_v1_aces | 20 | 2016-08-01 | 2016-09-01 | 633 | 64.9% |
| aces | ensemble_v1_aces | 21 | 2016-09-01 | 2016-10-01 | 278 | 65.5% |
| aces | ensemble_v1_aces | 22 | 2016-10-01 | 2016-11-01 | 514 | 74.5% |
| aces | ensemble_v1_aces | 23 | 2016-11-01 | 2016-12-01 | 130 | 74.6% |
| aces | ensemble_v1_aces | 25 | 2017-01-01 | 2017-02-01 | 492 | 63.4% |
| aces | ensemble_v1_aces | 26 | 2017-02-01 | 2017-03-01 | 562 | 77.9% |
| aces | ensemble_v1_aces | 27 | 2017-03-01 | 2017-04-01 | 544 | 77.0% |
| aces | ensemble_v1_aces | 28 | 2017-04-01 | 2017-05-01 | 434 | 72.6% |
| aces | ensemble_v1_aces | 29 | 2017-05-01 | 2017-06-01 | 676 | 68.6% |
| aces | ensemble_v1_aces | 30 | 2017-06-01 | 2017-07-01 | 346 | 62.7% |
| aces | ensemble_v1_aces | 31 | 2017-07-01 | 2017-08-01 | 573 | 60.4% |
| aces | ensemble_v1_aces | 32 | 2017-08-01 | 2017-09-01 | 720 | 67.8% |
| aces | ensemble_v1_aces | 33 | 2017-09-01 | 2017-10-01 | 289 | 69.6% |
| aces | ensemble_v1_aces | 34 | 2017-10-01 | 2017-11-01 | 550 | 74.9% |
| aces | ensemble_v1_aces | 35 | 2017-11-01 | 2017-12-01 | 123 | 71.5% |
| aces | ensemble_v1_aces | 37 | 2018-01-01 | 2018-02-01 | 498 | 62.0% |
| aces | ensemble_v1_aces | 38 | 2018-02-01 | 2018-03-01 | 670 | 77.8% |
| aces | ensemble_v1_aces | 39 | 2018-03-01 | 2018-04-01 | 458 | 75.8% |
| aces | ensemble_v1_aces | 40 | 2018-04-01 | 2018-05-01 | 451 | 79.2% |
| aces | ensemble_v1_aces | 41 | 2018-05-01 | 2018-06-01 | 712 | 72.8% |
| aces | ensemble_v1_aces | 42 | 2018-06-01 | 2018-07-01 | 335 | 71.9% |
| aces | ensemble_v1_aces | 43 | 2018-07-01 | 2018-08-01 | 592 | 63.3% |
| aces | ensemble_v1_aces | 44 | 2018-08-01 | 2018-09-01 | 711 | 71.3% |
| aces | ensemble_v1_aces | 45 | 2018-09-01 | 2018-10-01 | 286 | 72.4% |
| aces | ensemble_v1_aces | 46 | 2018-10-01 | 2018-11-01 | 559 | 73.2% |
| aces | ensemble_v1_aces | 47 | 2018-11-01 | 2018-12-01 | 95 | 75.8% |
| aces | ensemble_v1_aces | 49 | 2019-01-01 | 2019-02-01 | 521 | 66.0% |
| aces | ensemble_v1_aces | 50 | 2019-02-01 | 2019-03-01 | 683 | 76.7% |
| aces | ensemble_v1_aces | 51 | 2019-03-01 | 2019-04-01 | 409 | 78.2% |
| aces | ensemble_v1_aces | 52 | 2019-04-01 | 2019-05-01 | 362 | 77.9% |
| aces | ensemble_v1_aces | 53 | 2019-05-01 | 2019-06-01 | 658 | 71.9% |
| aces | ensemble_v1_aces | 54 | 2019-06-01 | 2019-07-01 | 333 | 74.8% |
| aces | ensemble_v1_aces | 55 | 2019-07-01 | 2019-08-01 | 672 | 66.5% |
| aces | ensemble_v1_aces | 56 | 2019-08-01 | 2019-09-01 | 639 | 63.7% |
| aces | ensemble_v1_aces | 57 | 2019-09-01 | 2019-10-01 | 214 | 73.8% |
| aces | ensemble_v1_aces | 58 | 2019-10-01 | 2019-11-01 | 590 | 73.2% |
| aces | ensemble_v1_aces | 59 | 2019-11-01 | 2019-12-01 | 169 | 70.4% |
| aces | ensemble_v1_aces | 61 | 2020-01-01 | 2020-02-01 | 562 | 66.5% |
| aces | ensemble_v1_aces | 62 | 2020-02-01 | 2020-03-01 | 641 | 74.9% |
| aces | ensemble_v1_aces | 63 | 2020-03-01 | 2020-04-01 | 108 | 71.3% |
| aces | ensemble_v1_aces | 68 | 2020-08-01 | 2020-09-01 | 229 | 65.5% |
| aces | ensemble_v1_aces | 69 | 2020-09-01 | 2020-10-01 | 552 | 66.5% |
| aces | ensemble_v1_aces | 70 | 2020-10-01 | 2020-11-01 | 400 | 74.2% |
| aces | ensemble_v1_aces | 71 | 2020-11-01 | 2020-12-01 | 192 | 64.6% |
| aces | ensemble_v1_aces | 73 | 2021-01-01 | 2021-02-01 | 102 | 84.3% |
| aces | ensemble_v1_aces | 74 | 2021-02-01 | 2021-03-01 | 633 | 69.0% |
| aces | ensemble_v1_aces | 75 | 2021-03-01 | 2021-04-01 | 602 | 73.4% |
| aces | ensemble_v1_aces | 76 | 2021-04-01 | 2021-05-01 | 451 | 80.0% |
| aces | ensemble_v1_aces | 77 | 2021-05-01 | 2021-06-01 | 550 | 73.3% |
| aces | ensemble_v1_aces | 78 | 2021-06-01 | 2021-07-01 | 619 | 61.1% |
| aces | ensemble_v1_aces | 79 | 2021-07-01 | 2021-08-01 | 433 | 69.3% |
| aces | ensemble_v1_aces | 80 | 2021-08-01 | 2021-09-01 | 578 | 71.3% |
| aces | ensemble_v1_aces | 81 | 2021-09-01 | 2021-10-01 | 306 | 72.2% |
| aces | ensemble_v1_aces | 82 | 2021-10-01 | 2021-11-01 | 436 | 74.5% |
| aces | ensemble_v1_aces | 83 | 2021-11-01 | 2021-12-01 | 296 | 72.0% |
| aces | ensemble_v1_aces | 84 | 2021-12-01 | 2022-01-01 | 20 | 90.0% |
| aces | ensemble_v1_aces | 85 | 2022-01-01 | 2022-02-01 | 564 | 67.2% |
| aces | ensemble_v1_aces | 86 | 2022-02-01 | 2022-03-01 | 708 | 77.5% |
| aces | ensemble_v1_aces | 87 | 2022-03-01 | 2022-04-01 | 458 | 76.0% |
| aces | ensemble_v1_aces | 88 | 2022-04-01 | 2022-05-01 | 460 | 78.7% |
| aces | ensemble_v1_aces | 89 | 2022-05-01 | 2022-06-01 | 562 | 68.5% |
| aces | ensemble_v1_aces | 90 | 2022-06-01 | 2022-07-01 | 552 | 59.8% |
| aces | ensemble_v1_aces | 91 | 2022-07-01 | 2022-08-01 | 368 | 76.6% |
| aces | ensemble_v1_aces | 92 | 2022-08-01 | 2022-09-01 | 661 | 70.8% |
| aces | ensemble_v1_aces | 93 | 2022-09-01 | 2022-10-01 | 261 | 75.9% |
| aces | ensemble_v1_aces | 94 | 2022-10-01 | 2022-11-01 | 507 | 76.5% |
| aces | ensemble_v1_aces | 95 | 2022-11-01 | 2022-12-01 | 163 | 71.2% |
| aces | ensemble_v1_aces | 97 | 2023-01-01 | 2023-02-01 | 543 | 64.1% |
| aces | ensemble_v1_aces | 98 | 2023-02-01 | 2023-03-01 | 475 | 75.6% |
| aces | ensemble_v1_aces | 99 | 2023-03-01 | 2023-04-01 | 543 | 76.2% |
| aces | ensemble_v1_aces | 100 | 2023-04-01 | 2023-05-01 | 638 | 76.6% |
| aces | ensemble_v1_aces | 101 | 2023-05-01 | 2023-06-01 | 494 | 70.4% |
| aces | ensemble_v1_aces | 102 | 2023-06-01 | 2023-07-01 | 350 | 71.1% |
| aces | ensemble_v1_aces | 103 | 2023-07-01 | 2023-08-01 | 567 | 64.7% |
| aces | ensemble_v1_aces | 104 | 2023-08-01 | 2023-09-01 | 719 | 67.2% |
| aces | ensemble_v1_aces | 105 | 2023-09-01 | 2023-10-01 | 296 | 75.3% |
| aces | ensemble_v1_aces | 106 | 2023-10-01 | 2023-11-01 | 527 | 74.8% |
| aces | ensemble_v1_aces | 107 | 2023-11-01 | 2023-12-01 | 238 | 67.2% |
| aces | ensemble_v1_aces | 108 | 2023-12-01 | 2024-01-01 | 6 | 83.3% |
| aces | ensemble_v1_aces | 109 | 2024-01-01 | 2024-02-01 | 532 | 67.7% |
| aces | ensemble_v1_aces | 110 | 2024-02-01 | 2024-03-01 | 743 | 76.3% |
| aces | ensemble_v1_aces | 111 | 2024-03-01 | 2024-04-01 | 412 | 76.9% |
| aces | ensemble_v1_aces | 112 | 2024-04-01 | 2024-05-01 | 642 | 79.3% |
| aces | ensemble_v1_aces | 113 | 2024-05-01 | 2024-06-01 | 527 | 71.3% |
| aces | ensemble_v1_aces | 114 | 2024-06-01 | 2024-07-01 | 329 | 72.9% |
| aces | ensemble_v1_aces | 115 | 2024-07-01 | 2024-08-01 | 756 | 64.9% |
| aces | ensemble_v1_aces | 116 | 2024-08-01 | 2024-09-01 | 603 | 67.0% |
| aces | ensemble_v1_aces | 117 | 2024-09-01 | 2024-10-01 | 342 | 73.4% |
| aces | ensemble_v1_aces | 118 | 2024-10-01 | 2024-11-01 | 568 | 79.0% |
| aces | ensemble_v1_aces | 119 | 2024-11-01 | 2024-12-01 | 175 | 70.3% |
| aces | ensemble_v1_aces | 120 | 2024-12-01 | 2025-01-01 | 69 | 75.4% |
| aces | ensemble_v1_aces | 121 | 2025-01-01 | 2025-02-01 | 518 | 62.7% |
| aces | ensemble_v1_aces | 122 | 2025-02-01 | 2025-03-01 | 563 | 71.4% |
| aces | ensemble_v1_aces | 123 | 2025-03-01 | 2025-04-01 | 387 | 71.8% |
| aces | ensemble_v1_aces | 124 | 2025-04-01 | 2025-05-01 | 570 | 80.4% |
| aces | ensemble_v1_aces | 125 | 2025-05-01 | 2025-06-01 | 540 | 76.1% |
| aces | ensemble_v1_aces | 126 | 2025-06-01 | 2025-07-01 | 455 | 64.8% |
| aces | ensemble_v1_aces | 127 | 2025-07-01 | 2025-08-01 | 635 | 70.9% |
| aces | ensemble_v1_aces | 128 | 2025-08-01 | 2025-09-01 | 531 | 60.1% |
| aces | ensemble_v1_aces | 129 | 2025-09-01 | 2025-10-01 | 247 | 71.7% |
| aces | ensemble_v1_aces | 130 | 2025-10-01 | 2025-11-01 | 570 | 74.7% |
| aces | ensemble_v1_aces | 131 | 2025-11-01 | 2025-12-01 | 134 | 70.1% |
| aces | ensemble_v1_aces | 132 | 2025-12-01 | 2026-01-01 | 27 | 55.6% |
| aces | ensemble_v1_aces | 133 | 2026-01-01 | 2026-02-01 | 217 | 63.6% |
| aces | ensemble_v1_aces | 134 | 2026-02-01 | 2026-03-01 | 1009 | 71.5% |
| aces | ensemble_v1_aces | 135 | 2026-03-01 | 2026-04-01 | 1365 | 70.4% |
| aces | ensemble_v1_aces | 136 | 2026-04-01 | 2026-05-01 | 1857 | 71.8% |
| aces | ensemble_v1_aces | 137 | 2026-05-01 | 2026-06-01 | 1546 | 73.5% |
| aces | ensemble_v1_aces | 138 | 2026-06-01 | 2026-07-01 | 1542 | 68.9% |
| aces | ensemble_v1_aces | 139 | 2026-07-01 | 2026-08-01 | 1862 | 66.8% |
| aces | ensemble_v1_aces | 140 | 2026-08-01 | 2026-09-01 | 1606 | 72.0% |
| aces | ensemble_v1_aces | 141 | 2026-09-01 | 2026-10-01 | 1088 | 66.7% |
| aces | gbm_v1_aces | 2 | 2015-02-01 | 2015-03-01 | 426 | 61.7% |
| aces | gbm_v1_aces | 3 | 2015-03-01 | 2015-04-01 | 344 | 70.1% |
| aces | gbm_v1_aces | 4 | 2015-04-01 | 2015-05-01 | 413 | 76.0% |
| aces | gbm_v1_aces | 5 | 2015-05-01 | 2015-06-01 | 580 | 77.9% |
| aces | gbm_v1_aces | 6 | 2015-06-01 | 2015-07-01 | 476 | 65.8% |
| aces | gbm_v1_aces | 7 | 2015-07-01 | 2015-08-01 | 368 | 67.9% |
| aces | gbm_v1_aces | 8 | 2015-08-01 | 2015-09-01 | 574 | 70.7% |
| aces | gbm_v1_aces | 9 | 2015-09-01 | 2015-10-01 | 262 | 70.6% |
| aces | gbm_v1_aces | 10 | 2015-10-01 | 2015-11-01 | 544 | 80.1% |
| aces | gbm_v1_aces | 11 | 2015-11-01 | 2015-12-01 | 128 | 79.7% |
| aces | gbm_v1_aces | 13 | 2016-01-01 | 2016-02-01 | 479 | 76.8% |
| aces | gbm_v1_aces | 14 | 2016-02-01 | 2016-03-01 | 631 | 75.6% |
| aces | gbm_v1_aces | 15 | 2016-03-01 | 2016-04-01 | 431 | 69.8% |
| aces | gbm_v1_aces | 16 | 2016-04-01 | 2016-05-01 | 486 | 78.4% |
| aces | gbm_v1_aces | 17 | 2016-05-01 | 2016-06-01 | 560 | 80.4% |
| aces | gbm_v1_aces | 18 | 2016-06-01 | 2016-07-01 | 526 | 81.2% |
| aces | gbm_v1_aces | 19 | 2016-07-01 | 2016-08-01 | 564 | 76.8% |
| aces | gbm_v1_aces | 20 | 2016-08-01 | 2016-09-01 | 633 | 77.3% |
| aces | gbm_v1_aces | 21 | 2016-09-01 | 2016-10-01 | 278 | 75.2% |
| aces | gbm_v1_aces | 22 | 2016-10-01 | 2016-11-01 | 514 | 75.5% |
| aces | gbm_v1_aces | 23 | 2016-11-01 | 2016-12-01 | 130 | 78.5% |
| aces | gbm_v1_aces | 25 | 2017-01-01 | 2017-02-01 | 492 | 75.8% |
| aces | gbm_v1_aces | 26 | 2017-02-01 | 2017-03-01 | 562 | 79.2% |
| aces | gbm_v1_aces | 27 | 2017-03-01 | 2017-04-01 | 544 | 79.2% |
| aces | gbm_v1_aces | 28 | 2017-04-01 | 2017-05-01 | 434 | 76.3% |
| aces | gbm_v1_aces | 29 | 2017-05-01 | 2017-06-01 | 676 | 75.7% |
| aces | gbm_v1_aces | 30 | 2017-06-01 | 2017-07-01 | 346 | 69.4% |
| aces | gbm_v1_aces | 31 | 2017-07-01 | 2017-08-01 | 573 | 78.7% |
| aces | gbm_v1_aces | 32 | 2017-08-01 | 2017-09-01 | 720 | 79.0% |
| aces | gbm_v1_aces | 33 | 2017-09-01 | 2017-10-01 | 289 | 75.8% |
| aces | gbm_v1_aces | 34 | 2017-10-01 | 2017-11-01 | 550 | 77.8% |
| aces | gbm_v1_aces | 35 | 2017-11-01 | 2017-12-01 | 123 | 74.8% |
| aces | gbm_v1_aces | 37 | 2018-01-01 | 2018-02-01 | 498 | 73.3% |
| aces | gbm_v1_aces | 38 | 2018-02-01 | 2018-03-01 | 670 | 79.1% |
| aces | gbm_v1_aces | 39 | 2018-03-01 | 2018-04-01 | 458 | 78.2% |
| aces | gbm_v1_aces | 40 | 2018-04-01 | 2018-05-01 | 451 | 80.0% |
| aces | gbm_v1_aces | 41 | 2018-05-01 | 2018-06-01 | 712 | 80.1% |
| aces | gbm_v1_aces | 42 | 2018-06-01 | 2018-07-01 | 335 | 77.9% |
| aces | gbm_v1_aces | 43 | 2018-07-01 | 2018-08-01 | 592 | 77.0% |
| aces | gbm_v1_aces | 44 | 2018-08-01 | 2018-09-01 | 711 | 80.7% |
| aces | gbm_v1_aces | 45 | 2018-09-01 | 2018-10-01 | 286 | 74.8% |
| aces | gbm_v1_aces | 46 | 2018-10-01 | 2018-11-01 | 559 | 78.0% |
| aces | gbm_v1_aces | 47 | 2018-11-01 | 2018-12-01 | 95 | 77.9% |
| aces | gbm_v1_aces | 49 | 2019-01-01 | 2019-02-01 | 521 | 74.5% |
| aces | gbm_v1_aces | 50 | 2019-02-01 | 2019-03-01 | 683 | 76.0% |
| aces | gbm_v1_aces | 51 | 2019-03-01 | 2019-04-01 | 409 | 77.5% |
| aces | gbm_v1_aces | 52 | 2019-04-01 | 2019-05-01 | 362 | 80.4% |
| aces | gbm_v1_aces | 53 | 2019-05-01 | 2019-06-01 | 658 | 77.1% |
| aces | gbm_v1_aces | 54 | 2019-06-01 | 2019-07-01 | 333 | 81.1% |
| aces | gbm_v1_aces | 55 | 2019-07-01 | 2019-08-01 | 672 | 81.8% |
| aces | gbm_v1_aces | 56 | 2019-08-01 | 2019-09-01 | 639 | 75.0% |
| aces | gbm_v1_aces | 57 | 2019-09-01 | 2019-10-01 | 214 | 77.6% |
| aces | gbm_v1_aces | 58 | 2019-10-01 | 2019-11-01 | 590 | 78.5% |
| aces | gbm_v1_aces | 59 | 2019-11-01 | 2019-12-01 | 169 | 78.7% |
| aces | gbm_v1_aces | 61 | 2020-01-01 | 2020-02-01 | 562 | 76.7% |
| aces | gbm_v1_aces | 62 | 2020-02-01 | 2020-03-01 | 641 | 78.3% |
| aces | gbm_v1_aces | 63 | 2020-03-01 | 2020-04-01 | 108 | 74.1% |
| aces | gbm_v1_aces | 68 | 2020-08-01 | 2020-09-01 | 229 | 77.3% |
| aces | gbm_v1_aces | 69 | 2020-09-01 | 2020-10-01 | 552 | 72.6% |
| aces | gbm_v1_aces | 70 | 2020-10-01 | 2020-11-01 | 400 | 76.0% |
| aces | gbm_v1_aces | 71 | 2020-11-01 | 2020-12-01 | 192 | 67.2% |
| aces | gbm_v1_aces | 73 | 2021-01-01 | 2021-02-01 | 102 | 82.4% |
| aces | gbm_v1_aces | 74 | 2021-02-01 | 2021-03-01 | 633 | 79.1% |
| aces | gbm_v1_aces | 75 | 2021-03-01 | 2021-04-01 | 602 | 74.8% |
| aces | gbm_v1_aces | 76 | 2021-04-01 | 2021-05-01 | 451 | 78.0% |
| aces | gbm_v1_aces | 77 | 2021-05-01 | 2021-06-01 | 550 | 79.3% |
| aces | gbm_v1_aces | 78 | 2021-06-01 | 2021-07-01 | 619 | 81.7% |
| aces | gbm_v1_aces | 79 | 2021-07-01 | 2021-08-01 | 433 | 75.1% |
| aces | gbm_v1_aces | 80 | 2021-08-01 | 2021-09-01 | 578 | 77.3% |
| aces | gbm_v1_aces | 81 | 2021-09-01 | 2021-10-01 | 306 | 81.4% |
| aces | gbm_v1_aces | 82 | 2021-10-01 | 2021-11-01 | 436 | 73.2% |
| aces | gbm_v1_aces | 83 | 2021-11-01 | 2021-12-01 | 296 | 73.3% |
| aces | gbm_v1_aces | 84 | 2021-12-01 | 2022-01-01 | 20 | 85.0% |
| aces | gbm_v1_aces | 85 | 2022-01-01 | 2022-02-01 | 564 | 78.2% |
| aces | gbm_v1_aces | 86 | 2022-02-01 | 2022-03-01 | 708 | 80.8% |
| aces | gbm_v1_aces | 87 | 2022-03-01 | 2022-04-01 | 458 | 79.5% |
| aces | gbm_v1_aces | 88 | 2022-04-01 | 2022-05-01 | 460 | 81.3% |
| aces | gbm_v1_aces | 89 | 2022-05-01 | 2022-06-01 | 562 | 77.6% |
| aces | gbm_v1_aces | 90 | 2022-06-01 | 2022-07-01 | 552 | 76.4% |
| aces | gbm_v1_aces | 91 | 2022-07-01 | 2022-08-01 | 368 | 81.5% |
| aces | gbm_v1_aces | 92 | 2022-08-01 | 2022-09-01 | 661 | 79.9% |
| aces | gbm_v1_aces | 93 | 2022-09-01 | 2022-10-01 | 261 | 80.1% |
| aces | gbm_v1_aces | 94 | 2022-10-01 | 2022-11-01 | 507 | 78.5% |
| aces | gbm_v1_aces | 95 | 2022-11-01 | 2022-12-01 | 163 | 76.7% |
| aces | gbm_v1_aces | 97 | 2023-01-01 | 2023-02-01 | 543 | 79.2% |
| aces | gbm_v1_aces | 98 | 2023-02-01 | 2023-03-01 | 475 | 78.3% |
| aces | gbm_v1_aces | 99 | 2023-03-01 | 2023-04-01 | 543 | 77.3% |
| aces | gbm_v1_aces | 100 | 2023-04-01 | 2023-05-01 | 638 | 77.7% |
| aces | gbm_v1_aces | 101 | 2023-05-01 | 2023-06-01 | 494 | 78.3% |
| aces | gbm_v1_aces | 102 | 2023-06-01 | 2023-07-01 | 350 | 78.6% |
| aces | gbm_v1_aces | 103 | 2023-07-01 | 2023-08-01 | 567 | 79.2% |
| aces | gbm_v1_aces | 104 | 2023-08-01 | 2023-09-01 | 719 | 78.3% |
| aces | gbm_v1_aces | 105 | 2023-09-01 | 2023-10-01 | 296 | 78.4% |
| aces | gbm_v1_aces | 106 | 2023-10-01 | 2023-11-01 | 527 | 77.6% |
| aces | gbm_v1_aces | 107 | 2023-11-01 | 2023-12-01 | 238 | 72.7% |
| aces | gbm_v1_aces | 108 | 2023-12-01 | 2024-01-01 | 6 | 83.3% |
| aces | gbm_v1_aces | 109 | 2024-01-01 | 2024-02-01 | 532 | 80.1% |
| aces | gbm_v1_aces | 110 | 2024-02-01 | 2024-03-01 | 743 | 80.3% |
| aces | gbm_v1_aces | 111 | 2024-03-01 | 2024-04-01 | 412 | 78.6% |
| aces | gbm_v1_aces | 112 | 2024-04-01 | 2024-05-01 | 642 | 80.4% |
| aces | gbm_v1_aces | 113 | 2024-05-01 | 2024-06-01 | 527 | 79.9% |
| aces | gbm_v1_aces | 114 | 2024-06-01 | 2024-07-01 | 329 | 79.0% |
| aces | gbm_v1_aces | 115 | 2024-07-01 | 2024-08-01 | 756 | 73.1% |
| aces | gbm_v1_aces | 116 | 2024-08-01 | 2024-09-01 | 603 | 76.5% |
| aces | gbm_v1_aces | 117 | 2024-09-01 | 2024-10-01 | 342 | 78.9% |
| aces | gbm_v1_aces | 118 | 2024-10-01 | 2024-11-01 | 568 | 82.4% |
| aces | gbm_v1_aces | 119 | 2024-11-01 | 2024-12-01 | 175 | 77.1% |
| aces | gbm_v1_aces | 120 | 2024-12-01 | 2025-01-01 | 69 | 81.2% |
| aces | gbm_v1_aces | 121 | 2025-01-01 | 2025-02-01 | 518 | 79.0% |
| aces | gbm_v1_aces | 122 | 2025-02-01 | 2025-03-01 | 563 | 75.8% |
| aces | gbm_v1_aces | 123 | 2025-03-01 | 2025-04-01 | 387 | 72.6% |
| aces | gbm_v1_aces | 124 | 2025-04-01 | 2025-05-01 | 570 | 80.2% |
| aces | gbm_v1_aces | 125 | 2025-05-01 | 2025-06-01 | 540 | 81.1% |
| aces | gbm_v1_aces | 126 | 2025-06-01 | 2025-07-01 | 455 | 77.4% |
| aces | gbm_v1_aces | 127 | 2025-07-01 | 2025-08-01 | 635 | 80.2% |
| aces | gbm_v1_aces | 128 | 2025-08-01 | 2025-09-01 | 531 | 75.1% |
| aces | gbm_v1_aces | 129 | 2025-09-01 | 2025-10-01 | 247 | 76.9% |
| aces | gbm_v1_aces | 130 | 2025-10-01 | 2025-11-01 | 570 | 78.4% |
| aces | gbm_v1_aces | 131 | 2025-11-01 | 2025-12-01 | 134 | 78.4% |
| aces | gbm_v1_aces | 132 | 2025-12-01 | 2026-01-01 | 27 | 88.9% |
| aces | gbm_v1_aces | 133 | 2026-01-01 | 2026-02-01 | 217 | 80.6% |
| aces | gbm_v1_aces | 134 | 2026-02-01 | 2026-03-01 | 1009 | 76.7% |
| aces | gbm_v1_aces | 135 | 2026-03-01 | 2026-04-01 | 1365 | 73.4% |
| aces | gbm_v1_aces | 136 | 2026-04-01 | 2026-05-01 | 1857 | 75.1% |
| aces | gbm_v1_aces | 137 | 2026-05-01 | 2026-06-01 | 1546 | 77.9% |
| aces | gbm_v1_aces | 138 | 2026-06-01 | 2026-07-01 | 1542 | 77.4% |
| aces | gbm_v1_aces | 139 | 2026-07-01 | 2026-08-01 | 1862 | 75.6% |
| aces | gbm_v1_aces | 140 | 2026-08-01 | 2026-09-01 | 1606 | 78.5% |
| aces | gbm_v1_aces | 141 | 2026-09-01 | 2026-10-01 | 1088 | 78.3% |
| double_faults | baseline_v1_double_faults | 2 | 2015-02-01 | 2015-03-01 | 426 | 65.3% |
| double_faults | baseline_v1_double_faults | 3 | 2015-03-01 | 2015-04-01 | 344 | 61.9% |
| double_faults | baseline_v1_double_faults | 4 | 2015-04-01 | 2015-05-01 | 413 | 68.8% |
| double_faults | baseline_v1_double_faults | 5 | 2015-05-01 | 2015-06-01 | 580 | 62.1% |
| double_faults | baseline_v1_double_faults | 6 | 2015-06-01 | 2015-07-01 | 476 | 60.5% |
| double_faults | baseline_v1_double_faults | 7 | 2015-07-01 | 2015-08-01 | 368 | 63.3% |
| double_faults | baseline_v1_double_faults | 8 | 2015-08-01 | 2015-09-01 | 574 | 60.1% |
| double_faults | baseline_v1_double_faults | 9 | 2015-09-01 | 2015-10-01 | 262 | 53.1% |
| double_faults | baseline_v1_double_faults | 10 | 2015-10-01 | 2015-11-01 | 544 | 73.2% |
| double_faults | baseline_v1_double_faults | 11 | 2015-11-01 | 2015-12-01 | 128 | 64.8% |
| double_faults | baseline_v1_double_faults | 13 | 2016-01-01 | 2016-02-01 | 479 | 52.4% |
| double_faults | baseline_v1_double_faults | 14 | 2016-02-01 | 2016-03-01 | 631 | 69.6% |
| double_faults | baseline_v1_double_faults | 15 | 2016-03-01 | 2016-04-01 | 431 | 65.9% |
| double_faults | baseline_v1_double_faults | 16 | 2016-04-01 | 2016-05-01 | 486 | 77.0% |
| double_faults | baseline_v1_double_faults | 17 | 2016-05-01 | 2016-06-01 | 560 | 62.5% |
| double_faults | baseline_v1_double_faults | 18 | 2016-06-01 | 2016-07-01 | 526 | 54.6% |
| double_faults | baseline_v1_double_faults | 19 | 2016-07-01 | 2016-08-01 | 564 | 67.4% |
| double_faults | baseline_v1_double_faults | 20 | 2016-08-01 | 2016-09-01 | 633 | 56.6% |
| double_faults | baseline_v1_double_faults | 21 | 2016-09-01 | 2016-10-01 | 278 | 61.9% |
| double_faults | baseline_v1_double_faults | 22 | 2016-10-01 | 2016-11-01 | 514 | 72.6% |
| double_faults | baseline_v1_double_faults | 23 | 2016-11-01 | 2016-12-01 | 130 | 70.8% |
| double_faults | baseline_v1_double_faults | 25 | 2017-01-01 | 2017-02-01 | 492 | 54.1% |
| double_faults | baseline_v1_double_faults | 26 | 2017-02-01 | 2017-03-01 | 562 | 69.0% |
| double_faults | baseline_v1_double_faults | 27 | 2017-03-01 | 2017-04-01 | 544 | 66.2% |
| double_faults | baseline_v1_double_faults | 28 | 2017-04-01 | 2017-05-01 | 434 | 69.6% |
| double_faults | baseline_v1_double_faults | 29 | 2017-05-01 | 2017-06-01 | 676 | 64.6% |
| double_faults | baseline_v1_double_faults | 30 | 2017-06-01 | 2017-07-01 | 346 | 65.6% |
| double_faults | baseline_v1_double_faults | 31 | 2017-07-01 | 2017-08-01 | 573 | 51.0% |
| double_faults | baseline_v1_double_faults | 32 | 2017-08-01 | 2017-09-01 | 720 | 54.6% |
| double_faults | baseline_v1_double_faults | 33 | 2017-09-01 | 2017-10-01 | 289 | 65.7% |
| double_faults | baseline_v1_double_faults | 34 | 2017-10-01 | 2017-11-01 | 550 | 65.3% |
| double_faults | baseline_v1_double_faults | 35 | 2017-11-01 | 2017-12-01 | 123 | 62.6% |
| double_faults | baseline_v1_double_faults | 37 | 2018-01-01 | 2018-02-01 | 498 | 54.2% |
| double_faults | baseline_v1_double_faults | 38 | 2018-02-01 | 2018-03-01 | 670 | 67.6% |
| double_faults | baseline_v1_double_faults | 39 | 2018-03-01 | 2018-04-01 | 458 | 67.0% |
| double_faults | baseline_v1_double_faults | 40 | 2018-04-01 | 2018-05-01 | 451 | 67.2% |
| double_faults | baseline_v1_double_faults | 41 | 2018-05-01 | 2018-06-01 | 712 | 67.4% |
| double_faults | baseline_v1_double_faults | 42 | 2018-06-01 | 2018-07-01 | 335 | 74.6% |
| double_faults | baseline_v1_double_faults | 43 | 2018-07-01 | 2018-08-01 | 592 | 56.1% |
| double_faults | baseline_v1_double_faults | 44 | 2018-08-01 | 2018-09-01 | 711 | 58.6% |
| double_faults | baseline_v1_double_faults | 45 | 2018-09-01 | 2018-10-01 | 286 | 70.3% |
| double_faults | baseline_v1_double_faults | 46 | 2018-10-01 | 2018-11-01 | 559 | 73.7% |
| double_faults | baseline_v1_double_faults | 47 | 2018-11-01 | 2018-12-01 | 95 | 68.4% |
| double_faults | baseline_v1_double_faults | 49 | 2019-01-01 | 2019-02-01 | 521 | 52.2% |
| double_faults | baseline_v1_double_faults | 50 | 2019-02-01 | 2019-03-01 | 683 | 64.6% |
| double_faults | baseline_v1_double_faults | 51 | 2019-03-01 | 2019-04-01 | 409 | 74.3% |
| double_faults | baseline_v1_double_faults | 52 | 2019-04-01 | 2019-05-01 | 362 | 67.7% |
| double_faults | baseline_v1_double_faults | 53 | 2019-05-01 | 2019-06-01 | 658 | 63.5% |
| double_faults | baseline_v1_double_faults | 54 | 2019-06-01 | 2019-07-01 | 333 | 65.5% |
| double_faults | baseline_v1_double_faults | 55 | 2019-07-01 | 2019-08-01 | 672 | 54.6% |
| double_faults | baseline_v1_double_faults | 56 | 2019-08-01 | 2019-09-01 | 639 | 57.6% |
| double_faults | baseline_v1_double_faults | 57 | 2019-09-01 | 2019-10-01 | 214 | 69.2% |
| double_faults | baseline_v1_double_faults | 58 | 2019-10-01 | 2019-11-01 | 590 | 72.4% |
| double_faults | baseline_v1_double_faults | 59 | 2019-11-01 | 2019-12-01 | 169 | 69.2% |
| double_faults | baseline_v1_double_faults | 61 | 2020-01-01 | 2020-02-01 | 562 | 55.3% |
| double_faults | baseline_v1_double_faults | 62 | 2020-02-01 | 2020-03-01 | 641 | 67.7% |
| double_faults | baseline_v1_double_faults | 63 | 2020-03-01 | 2020-04-01 | 108 | 74.1% |
| double_faults | baseline_v1_double_faults | 68 | 2020-08-01 | 2020-09-01 | 229 | 50.7% |
| double_faults | baseline_v1_double_faults | 69 | 2020-09-01 | 2020-10-01 | 552 | 52.4% |
| double_faults | baseline_v1_double_faults | 70 | 2020-10-01 | 2020-11-01 | 400 | 71.0% |
| double_faults | baseline_v1_double_faults | 71 | 2020-11-01 | 2020-12-01 | 192 | 74.5% |
| double_faults | baseline_v1_double_faults | 73 | 2021-01-01 | 2021-02-01 | 102 | 70.6% |
| double_faults | baseline_v1_double_faults | 74 | 2021-02-01 | 2021-03-01 | 633 | 57.0% |
| double_faults | baseline_v1_double_faults | 75 | 2021-03-01 | 2021-04-01 | 602 | 64.8% |
| double_faults | baseline_v1_double_faults | 76 | 2021-04-01 | 2021-05-01 | 451 | 69.2% |
| double_faults | baseline_v1_double_faults | 77 | 2021-05-01 | 2021-06-01 | 550 | 66.7% |
| double_faults | baseline_v1_double_faults | 78 | 2021-06-01 | 2021-07-01 | 619 | 54.0% |
| double_faults | baseline_v1_double_faults | 79 | 2021-07-01 | 2021-08-01 | 433 | 63.7% |
| double_faults | baseline_v1_double_faults | 80 | 2021-08-01 | 2021-09-01 | 578 | 60.6% |
| double_faults | baseline_v1_double_faults | 81 | 2021-09-01 | 2021-10-01 | 306 | 61.8% |
| double_faults | baseline_v1_double_faults | 82 | 2021-10-01 | 2021-11-01 | 436 | 68.6% |
| double_faults | baseline_v1_double_faults | 83 | 2021-11-01 | 2021-12-01 | 296 | 67.9% |
| double_faults | baseline_v1_double_faults | 84 | 2021-12-01 | 2022-01-01 | 20 | 75.0% |
| double_faults | baseline_v1_double_faults | 85 | 2022-01-01 | 2022-02-01 | 564 | 57.8% |
| double_faults | baseline_v1_double_faults | 86 | 2022-02-01 | 2022-03-01 | 708 | 68.6% |
| double_faults | baseline_v1_double_faults | 87 | 2022-03-01 | 2022-04-01 | 458 | 65.7% |
| double_faults | baseline_v1_double_faults | 88 | 2022-04-01 | 2022-05-01 | 460 | 67.6% |
| double_faults | baseline_v1_double_faults | 89 | 2022-05-01 | 2022-06-01 | 562 | 59.3% |
| double_faults | baseline_v1_double_faults | 90 | 2022-06-01 | 2022-07-01 | 552 | 53.4% |
| double_faults | baseline_v1_double_faults | 91 | 2022-07-01 | 2022-08-01 | 368 | 70.7% |
| double_faults | baseline_v1_double_faults | 92 | 2022-08-01 | 2022-09-01 | 661 | 60.7% |
| double_faults | baseline_v1_double_faults | 93 | 2022-09-01 | 2022-10-01 | 261 | 67.0% |
| double_faults | baseline_v1_double_faults | 94 | 2022-10-01 | 2022-11-01 | 507 | 73.8% |
| double_faults | baseline_v1_double_faults | 95 | 2022-11-01 | 2022-12-01 | 163 | 60.7% |
| double_faults | baseline_v1_double_faults | 97 | 2023-01-01 | 2023-02-01 | 543 | 57.3% |
| double_faults | baseline_v1_double_faults | 98 | 2023-02-01 | 2023-03-01 | 475 | 70.9% |
| double_faults | baseline_v1_double_faults | 99 | 2023-03-01 | 2023-04-01 | 543 | 63.4% |
| double_faults | baseline_v1_double_faults | 100 | 2023-04-01 | 2023-05-01 | 638 | 70.4% |
| double_faults | baseline_v1_double_faults | 101 | 2023-05-01 | 2023-06-01 | 494 | 60.1% |
| double_faults | baseline_v1_double_faults | 102 | 2023-06-01 | 2023-07-01 | 350 | 67.7% |
| double_faults | baseline_v1_double_faults | 103 | 2023-07-01 | 2023-08-01 | 567 | 57.5% |
| double_faults | baseline_v1_double_faults | 104 | 2023-08-01 | 2023-09-01 | 719 | 54.4% |
| double_faults | baseline_v1_double_faults | 105 | 2023-09-01 | 2023-10-01 | 296 | 72.0% |
| double_faults | baseline_v1_double_faults | 106 | 2023-10-01 | 2023-11-01 | 527 | 75.1% |
| double_faults | baseline_v1_double_faults | 107 | 2023-11-01 | 2023-12-01 | 238 | 72.7% |
| double_faults | baseline_v1_double_faults | 108 | 2023-12-01 | 2024-01-01 | 6 | 50.0% |
| double_faults | baseline_v1_double_faults | 109 | 2024-01-01 | 2024-02-01 | 532 | 53.8% |
| double_faults | baseline_v1_double_faults | 110 | 2024-02-01 | 2024-03-01 | 743 | 72.4% |
| double_faults | baseline_v1_double_faults | 111 | 2024-03-01 | 2024-04-01 | 412 | 69.2% |
| double_faults | baseline_v1_double_faults | 112 | 2024-04-01 | 2024-05-01 | 642 | 69.9% |
| double_faults | baseline_v1_double_faults | 113 | 2024-05-01 | 2024-06-01 | 527 | 60.5% |
| double_faults | baseline_v1_double_faults | 114 | 2024-06-01 | 2024-07-01 | 329 | 64.1% |
| double_faults | baseline_v1_double_faults | 115 | 2024-07-01 | 2024-08-01 | 756 | 57.4% |
| double_faults | baseline_v1_double_faults | 116 | 2024-08-01 | 2024-09-01 | 603 | 56.1% |
| double_faults | baseline_v1_double_faults | 117 | 2024-09-01 | 2024-10-01 | 342 | 76.6% |
| double_faults | baseline_v1_double_faults | 118 | 2024-10-01 | 2024-11-01 | 568 | 79.0% |
| double_faults | baseline_v1_double_faults | 119 | 2024-11-01 | 2024-12-01 | 175 | 77.1% |
| double_faults | baseline_v1_double_faults | 120 | 2024-12-01 | 2025-01-01 | 69 | 69.6% |
| double_faults | baseline_v1_double_faults | 121 | 2025-01-01 | 2025-02-01 | 518 | 57.1% |
| double_faults | baseline_v1_double_faults | 122 | 2025-02-01 | 2025-03-01 | 563 | 70.5% |
| double_faults | baseline_v1_double_faults | 123 | 2025-03-01 | 2025-04-01 | 387 | 69.3% |
| double_faults | baseline_v1_double_faults | 124 | 2025-04-01 | 2025-05-01 | 570 | 68.4% |
| double_faults | baseline_v1_double_faults | 125 | 2025-05-01 | 2025-06-01 | 540 | 59.1% |
| double_faults | baseline_v1_double_faults | 126 | 2025-06-01 | 2025-07-01 | 455 | 61.1% |
| double_faults | baseline_v1_double_faults | 127 | 2025-07-01 | 2025-08-01 | 635 | 55.3% |
| double_faults | baseline_v1_double_faults | 128 | 2025-08-01 | 2025-09-01 | 531 | 50.1% |
| double_faults | baseline_v1_double_faults | 129 | 2025-09-01 | 2025-10-01 | 247 | 75.7% |
| double_faults | baseline_v1_double_faults | 130 | 2025-10-01 | 2025-11-01 | 570 | 73.3% |
| double_faults | baseline_v1_double_faults | 131 | 2025-11-01 | 2025-12-01 | 134 | 69.4% |
| double_faults | baseline_v1_double_faults | 132 | 2025-12-01 | 2026-01-01 | 27 | 51.9% |
| double_faults | baseline_v1_double_faults | 133 | 2026-01-01 | 2026-02-01 | 217 | 57.6% |
| double_faults | baseline_v1_double_faults | 134 | 2026-02-01 | 2026-03-01 | 1009 | 67.0% |
| double_faults | baseline_v1_double_faults | 135 | 2026-03-01 | 2026-04-01 | 1365 | 64.0% |
| double_faults | baseline_v1_double_faults | 136 | 2026-04-01 | 2026-05-01 | 1857 | 65.0% |
| double_faults | baseline_v1_double_faults | 137 | 2026-05-01 | 2026-06-01 | 1546 | 64.7% |
| double_faults | baseline_v1_double_faults | 138 | 2026-06-01 | 2026-07-01 | 1542 | 62.8% |
| double_faults | baseline_v1_double_faults | 139 | 2026-07-01 | 2026-08-01 | 1862 | 62.9% |
| double_faults | baseline_v1_double_faults | 140 | 2026-08-01 | 2026-09-01 | 1606 | 62.1% |
| double_faults | baseline_v1_double_faults | 141 | 2026-09-01 | 2026-10-01 | 1088 | 62.2% |
| double_faults | ensemble_v1_double_faults | 2 | 2015-02-01 | 2015-03-01 | 426 | 71.6% |
| double_faults | ensemble_v1_double_faults | 3 | 2015-03-01 | 2015-04-01 | 344 | 69.5% |
| double_faults | ensemble_v1_double_faults | 4 | 2015-04-01 | 2015-05-01 | 413 | 70.0% |
| double_faults | ensemble_v1_double_faults | 5 | 2015-05-01 | 2015-06-01 | 580 | 73.4% |
| double_faults | ensemble_v1_double_faults | 6 | 2015-06-01 | 2015-07-01 | 476 | 66.8% |
| double_faults | ensemble_v1_double_faults | 7 | 2015-07-01 | 2015-08-01 | 368 | 70.1% |
| double_faults | ensemble_v1_double_faults | 8 | 2015-08-01 | 2015-09-01 | 574 | 67.6% |
| double_faults | ensemble_v1_double_faults | 9 | 2015-09-01 | 2015-10-01 | 262 | 64.1% |
| double_faults | ensemble_v1_double_faults | 10 | 2015-10-01 | 2015-11-01 | 544 | 77.4% |
| double_faults | ensemble_v1_double_faults | 11 | 2015-11-01 | 2015-12-01 | 128 | 74.2% |
| double_faults | ensemble_v1_double_faults | 13 | 2016-01-01 | 2016-02-01 | 479 | 69.1% |
| double_faults | ensemble_v1_double_faults | 14 | 2016-02-01 | 2016-03-01 | 631 | 72.1% |
| double_faults | ensemble_v1_double_faults | 15 | 2016-03-01 | 2016-04-01 | 431 | 70.5% |
| double_faults | ensemble_v1_double_faults | 16 | 2016-04-01 | 2016-05-01 | 486 | 74.7% |
| double_faults | ensemble_v1_double_faults | 17 | 2016-05-01 | 2016-06-01 | 560 | 75.5% |
| double_faults | ensemble_v1_double_faults | 18 | 2016-06-01 | 2016-07-01 | 526 | 68.3% |
| double_faults | ensemble_v1_double_faults | 19 | 2016-07-01 | 2016-08-01 | 564 | 72.2% |
| double_faults | ensemble_v1_double_faults | 20 | 2016-08-01 | 2016-09-01 | 633 | 67.5% |
| double_faults | ensemble_v1_double_faults | 21 | 2016-09-01 | 2016-10-01 | 278 | 70.5% |
| double_faults | ensemble_v1_double_faults | 22 | 2016-10-01 | 2016-11-01 | 514 | 75.9% |
| double_faults | ensemble_v1_double_faults | 23 | 2016-11-01 | 2016-12-01 | 130 | 76.2% |
| double_faults | ensemble_v1_double_faults | 25 | 2017-01-01 | 2017-02-01 | 492 | 68.3% |
| double_faults | ensemble_v1_double_faults | 26 | 2017-02-01 | 2017-03-01 | 562 | 70.6% |
| double_faults | ensemble_v1_double_faults | 27 | 2017-03-01 | 2017-04-01 | 544 | 73.2% |
| double_faults | ensemble_v1_double_faults | 28 | 2017-04-01 | 2017-05-01 | 434 | 70.7% |
| double_faults | ensemble_v1_double_faults | 29 | 2017-05-01 | 2017-06-01 | 676 | 72.3% |
| double_faults | ensemble_v1_double_faults | 30 | 2017-06-01 | 2017-07-01 | 346 | 71.1% |
| double_faults | ensemble_v1_double_faults | 31 | 2017-07-01 | 2017-08-01 | 573 | 63.5% |
| double_faults | ensemble_v1_double_faults | 32 | 2017-08-01 | 2017-09-01 | 720 | 67.5% |
| double_faults | ensemble_v1_double_faults | 33 | 2017-09-01 | 2017-10-01 | 289 | 75.1% |
| double_faults | ensemble_v1_double_faults | 34 | 2017-10-01 | 2017-11-01 | 550 | 69.3% |
| double_faults | ensemble_v1_double_faults | 35 | 2017-11-01 | 2017-12-01 | 123 | 72.4% |
| double_faults | ensemble_v1_double_faults | 37 | 2018-01-01 | 2018-02-01 | 498 | 68.9% |
| double_faults | ensemble_v1_double_faults | 38 | 2018-02-01 | 2018-03-01 | 670 | 70.4% |
| double_faults | ensemble_v1_double_faults | 39 | 2018-03-01 | 2018-04-01 | 458 | 72.9% |
| double_faults | ensemble_v1_double_faults | 40 | 2018-04-01 | 2018-05-01 | 451 | 67.6% |
| double_faults | ensemble_v1_double_faults | 41 | 2018-05-01 | 2018-06-01 | 712 | 74.3% |
| double_faults | ensemble_v1_double_faults | 42 | 2018-06-01 | 2018-07-01 | 335 | 80.3% |
| double_faults | ensemble_v1_double_faults | 43 | 2018-07-01 | 2018-08-01 | 592 | 66.6% |
| double_faults | ensemble_v1_double_faults | 44 | 2018-08-01 | 2018-09-01 | 711 | 69.2% |
| double_faults | ensemble_v1_double_faults | 45 | 2018-09-01 | 2018-10-01 | 286 | 75.5% |
| double_faults | ensemble_v1_double_faults | 46 | 2018-10-01 | 2018-11-01 | 559 | 77.6% |
| double_faults | ensemble_v1_double_faults | 47 | 2018-11-01 | 2018-12-01 | 95 | 71.6% |
| double_faults | ensemble_v1_double_faults | 49 | 2019-01-01 | 2019-02-01 | 521 | 63.7% |
| double_faults | ensemble_v1_double_faults | 50 | 2019-02-01 | 2019-03-01 | 683 | 73.1% |
| double_faults | ensemble_v1_double_faults | 51 | 2019-03-01 | 2019-04-01 | 409 | 78.2% |
| double_faults | ensemble_v1_double_faults | 52 | 2019-04-01 | 2019-05-01 | 362 | 73.5% |
| double_faults | ensemble_v1_double_faults | 53 | 2019-05-01 | 2019-06-01 | 658 | 70.7% |
| double_faults | ensemble_v1_double_faults | 54 | 2019-06-01 | 2019-07-01 | 333 | 74.2% |
| double_faults | ensemble_v1_double_faults | 55 | 2019-07-01 | 2019-08-01 | 672 | 68.6% |
| double_faults | ensemble_v1_double_faults | 56 | 2019-08-01 | 2019-09-01 | 639 | 71.7% |
| double_faults | ensemble_v1_double_faults | 57 | 2019-09-01 | 2019-10-01 | 214 | 71.5% |
| double_faults | ensemble_v1_double_faults | 58 | 2019-10-01 | 2019-11-01 | 590 | 77.6% |
| double_faults | ensemble_v1_double_faults | 59 | 2019-11-01 | 2019-12-01 | 169 | 68.0% |
| double_faults | ensemble_v1_double_faults | 61 | 2020-01-01 | 2020-02-01 | 562 | 65.5% |
| double_faults | ensemble_v1_double_faults | 62 | 2020-02-01 | 2020-03-01 | 641 | 72.1% |
| double_faults | ensemble_v1_double_faults | 63 | 2020-03-01 | 2020-04-01 | 108 | 78.7% |
| double_faults | ensemble_v1_double_faults | 68 | 2020-08-01 | 2020-09-01 | 229 | 64.6% |
| double_faults | ensemble_v1_double_faults | 69 | 2020-09-01 | 2020-10-01 | 552 | 62.7% |
| double_faults | ensemble_v1_double_faults | 70 | 2020-10-01 | 2020-11-01 | 400 | 72.8% |
| double_faults | ensemble_v1_double_faults | 71 | 2020-11-01 | 2020-12-01 | 192 | 76.6% |
| double_faults | ensemble_v1_double_faults | 73 | 2021-01-01 | 2021-02-01 | 102 | 77.5% |
| double_faults | ensemble_v1_double_faults | 74 | 2021-02-01 | 2021-03-01 | 633 | 69.5% |
| double_faults | ensemble_v1_double_faults | 75 | 2021-03-01 | 2021-04-01 | 602 | 72.1% |
| double_faults | ensemble_v1_double_faults | 76 | 2021-04-01 | 2021-05-01 | 451 | 73.2% |
| double_faults | ensemble_v1_double_faults | 77 | 2021-05-01 | 2021-06-01 | 550 | 71.8% |
| double_faults | ensemble_v1_double_faults | 78 | 2021-06-01 | 2021-07-01 | 619 | 67.2% |
| double_faults | ensemble_v1_double_faults | 79 | 2021-07-01 | 2021-08-01 | 433 | 67.7% |
| double_faults | ensemble_v1_double_faults | 80 | 2021-08-01 | 2021-09-01 | 578 | 70.4% |
| double_faults | ensemble_v1_double_faults | 81 | 2021-09-01 | 2021-10-01 | 306 | 70.3% |
| double_faults | ensemble_v1_double_faults | 82 | 2021-10-01 | 2021-11-01 | 436 | 71.6% |
| double_faults | ensemble_v1_double_faults | 83 | 2021-11-01 | 2021-12-01 | 296 | 73.3% |
| double_faults | ensemble_v1_double_faults | 84 | 2021-12-01 | 2022-01-01 | 20 | 85.0% |
| double_faults | ensemble_v1_double_faults | 85 | 2022-01-01 | 2022-02-01 | 564 | 70.6% |
| double_faults | ensemble_v1_double_faults | 86 | 2022-02-01 | 2022-03-01 | 708 | 72.2% |
| double_faults | ensemble_v1_double_faults | 87 | 2022-03-01 | 2022-04-01 | 458 | 72.3% |
| double_faults | ensemble_v1_double_faults | 88 | 2022-04-01 | 2022-05-01 | 460 | 68.0% |
| double_faults | ensemble_v1_double_faults | 89 | 2022-05-01 | 2022-06-01 | 562 | 69.4% |
| double_faults | ensemble_v1_double_faults | 90 | 2022-06-01 | 2022-07-01 | 552 | 67.8% |
| double_faults | ensemble_v1_double_faults | 91 | 2022-07-01 | 2022-08-01 | 368 | 75.0% |
| double_faults | ensemble_v1_double_faults | 92 | 2022-08-01 | 2022-09-01 | 661 | 71.1% |
| double_faults | ensemble_v1_double_faults | 93 | 2022-09-01 | 2022-10-01 | 261 | 70.5% |
| double_faults | ensemble_v1_double_faults | 94 | 2022-10-01 | 2022-11-01 | 507 | 70.4% |
| double_faults | ensemble_v1_double_faults | 95 | 2022-11-01 | 2022-12-01 | 163 | 63.2% |
| double_faults | ensemble_v1_double_faults | 97 | 2023-01-01 | 2023-02-01 | 543 | 67.8% |
| double_faults | ensemble_v1_double_faults | 98 | 2023-02-01 | 2023-03-01 | 475 | 72.4% |
| double_faults | ensemble_v1_double_faults | 99 | 2023-03-01 | 2023-04-01 | 543 | 68.5% |
| double_faults | ensemble_v1_double_faults | 100 | 2023-04-01 | 2023-05-01 | 638 | 73.4% |
| double_faults | ensemble_v1_double_faults | 101 | 2023-05-01 | 2023-06-01 | 494 | 69.8% |
| double_faults | ensemble_v1_double_faults | 102 | 2023-06-01 | 2023-07-01 | 350 | 73.1% |
| double_faults | ensemble_v1_double_faults | 103 | 2023-07-01 | 2023-08-01 | 567 | 68.8% |
| double_faults | ensemble_v1_double_faults | 104 | 2023-08-01 | 2023-09-01 | 719 | 65.1% |
| double_faults | ensemble_v1_double_faults | 105 | 2023-09-01 | 2023-10-01 | 296 | 76.0% |
| double_faults | ensemble_v1_double_faults | 106 | 2023-10-01 | 2023-11-01 | 527 | 77.2% |
| double_faults | ensemble_v1_double_faults | 107 | 2023-11-01 | 2023-12-01 | 238 | 77.3% |
| double_faults | ensemble_v1_double_faults | 108 | 2023-12-01 | 2024-01-01 | 6 | 16.7% |
| double_faults | ensemble_v1_double_faults | 109 | 2024-01-01 | 2024-02-01 | 532 | 68.8% |
| double_faults | ensemble_v1_double_faults | 110 | 2024-02-01 | 2024-03-01 | 743 | 76.7% |
| double_faults | ensemble_v1_double_faults | 111 | 2024-03-01 | 2024-04-01 | 412 | 74.5% |
| double_faults | ensemble_v1_double_faults | 112 | 2024-04-01 | 2024-05-01 | 642 | 70.7% |
| double_faults | ensemble_v1_double_faults | 113 | 2024-05-01 | 2024-06-01 | 527 | 70.6% |
| double_faults | ensemble_v1_double_faults | 114 | 2024-06-01 | 2024-07-01 | 329 | 70.5% |
| double_faults | ensemble_v1_double_faults | 115 | 2024-07-01 | 2024-08-01 | 756 | 64.7% |
| double_faults | ensemble_v1_double_faults | 116 | 2024-08-01 | 2024-09-01 | 603 | 62.2% |
| double_faults | ensemble_v1_double_faults | 117 | 2024-09-01 | 2024-10-01 | 342 | 76.9% |
| double_faults | ensemble_v1_double_faults | 118 | 2024-10-01 | 2024-11-01 | 568 | 78.7% |
| double_faults | ensemble_v1_double_faults | 119 | 2024-11-01 | 2024-12-01 | 175 | 71.4% |
| double_faults | ensemble_v1_double_faults | 120 | 2024-12-01 | 2025-01-01 | 69 | 72.5% |
| double_faults | ensemble_v1_double_faults | 121 | 2025-01-01 | 2025-02-01 | 518 | 67.2% |
| double_faults | ensemble_v1_double_faults | 122 | 2025-02-01 | 2025-03-01 | 563 | 71.8% |
| double_faults | ensemble_v1_double_faults | 123 | 2025-03-01 | 2025-04-01 | 387 | 74.4% |
| double_faults | ensemble_v1_double_faults | 124 | 2025-04-01 | 2025-05-01 | 570 | 69.5% |
| double_faults | ensemble_v1_double_faults | 125 | 2025-05-01 | 2025-06-01 | 540 | 69.8% |
| double_faults | ensemble_v1_double_faults | 126 | 2025-06-01 | 2025-07-01 | 455 | 70.8% |
| double_faults | ensemble_v1_double_faults | 127 | 2025-07-01 | 2025-08-01 | 635 | 65.4% |
| double_faults | ensemble_v1_double_faults | 128 | 2025-08-01 | 2025-09-01 | 531 | 64.0% |
| double_faults | ensemble_v1_double_faults | 129 | 2025-09-01 | 2025-10-01 | 247 | 77.3% |
| double_faults | ensemble_v1_double_faults | 130 | 2025-10-01 | 2025-11-01 | 570 | 71.4% |
| double_faults | ensemble_v1_double_faults | 131 | 2025-11-01 | 2025-12-01 | 134 | 75.4% |
| double_faults | ensemble_v1_double_faults | 132 | 2025-12-01 | 2026-01-01 | 27 | 63.0% |
| double_faults | ensemble_v1_double_faults | 133 | 2026-01-01 | 2026-02-01 | 217 | 71.0% |
| double_faults | ensemble_v1_double_faults | 134 | 2026-02-01 | 2026-03-01 | 1009 | 70.9% |
| double_faults | ensemble_v1_double_faults | 135 | 2026-03-01 | 2026-04-01 | 1365 | 67.8% |
| double_faults | ensemble_v1_double_faults | 136 | 2026-04-01 | 2026-05-01 | 1857 | 70.9% |
| double_faults | ensemble_v1_double_faults | 137 | 2026-05-01 | 2026-06-01 | 1546 | 70.1% |
| double_faults | ensemble_v1_double_faults | 138 | 2026-06-01 | 2026-07-01 | 1542 | 70.0% |
| double_faults | ensemble_v1_double_faults | 139 | 2026-07-01 | 2026-08-01 | 1862 | 71.2% |
| double_faults | ensemble_v1_double_faults | 140 | 2026-08-01 | 2026-09-01 | 1606 | 70.1% |
| double_faults | ensemble_v1_double_faults | 141 | 2026-09-01 | 2026-10-01 | 1088 | 71.3% |
| double_faults | gbm_v1_double_faults | 2 | 2015-02-01 | 2015-03-01 | 426 | 80.0% |
| double_faults | gbm_v1_double_faults | 3 | 2015-03-01 | 2015-04-01 | 344 | 76.2% |
| double_faults | gbm_v1_double_faults | 4 | 2015-04-01 | 2015-05-01 | 413 | 72.6% |
| double_faults | gbm_v1_double_faults | 5 | 2015-05-01 | 2015-06-01 | 580 | 84.3% |
| double_faults | gbm_v1_double_faults | 6 | 2015-06-01 | 2015-07-01 | 476 | 66.8% |
| double_faults | gbm_v1_double_faults | 7 | 2015-07-01 | 2015-08-01 | 368 | 75.3% |
| double_faults | gbm_v1_double_faults | 8 | 2015-08-01 | 2015-09-01 | 574 | 71.6% |
| double_faults | gbm_v1_double_faults | 9 | 2015-09-01 | 2015-10-01 | 262 | 77.1% |
| double_faults | gbm_v1_double_faults | 10 | 2015-10-01 | 2015-11-01 | 544 | 81.1% |
| double_faults | gbm_v1_double_faults | 11 | 2015-11-01 | 2015-12-01 | 128 | 77.3% |
| double_faults | gbm_v1_double_faults | 13 | 2016-01-01 | 2016-02-01 | 479 | 80.4% |
| double_faults | gbm_v1_double_faults | 14 | 2016-02-01 | 2016-03-01 | 631 | 74.2% |
| double_faults | gbm_v1_double_faults | 15 | 2016-03-01 | 2016-04-01 | 431 | 75.4% |
| double_faults | gbm_v1_double_faults | 16 | 2016-04-01 | 2016-05-01 | 486 | 78.2% |
| double_faults | gbm_v1_double_faults | 17 | 2016-05-01 | 2016-06-01 | 560 | 84.1% |
| double_faults | gbm_v1_double_faults | 18 | 2016-06-01 | 2016-07-01 | 526 | 79.3% |
| double_faults | gbm_v1_double_faults | 19 | 2016-07-01 | 2016-08-01 | 564 | 76.4% |
| double_faults | gbm_v1_double_faults | 20 | 2016-08-01 | 2016-09-01 | 633 | 73.0% |
| double_faults | gbm_v1_double_faults | 21 | 2016-09-01 | 2016-10-01 | 278 | 78.4% |
| double_faults | gbm_v1_double_faults | 22 | 2016-10-01 | 2016-11-01 | 514 | 77.2% |
| double_faults | gbm_v1_double_faults | 23 | 2016-11-01 | 2016-12-01 | 130 | 76.9% |
| double_faults | gbm_v1_double_faults | 25 | 2017-01-01 | 2017-02-01 | 492 | 79.5% |
| double_faults | gbm_v1_double_faults | 26 | 2017-02-01 | 2017-03-01 | 562 | 74.6% |
| double_faults | gbm_v1_double_faults | 27 | 2017-03-01 | 2017-04-01 | 544 | 75.7% |
| double_faults | gbm_v1_double_faults | 28 | 2017-04-01 | 2017-05-01 | 434 | 76.0% |
| double_faults | gbm_v1_double_faults | 29 | 2017-05-01 | 2017-06-01 | 676 | 78.1% |
| double_faults | gbm_v1_double_faults | 30 | 2017-06-01 | 2017-07-01 | 346 | 77.2% |
| double_faults | gbm_v1_double_faults | 31 | 2017-07-01 | 2017-08-01 | 573 | 75.7% |
| double_faults | gbm_v1_double_faults | 32 | 2017-08-01 | 2017-09-01 | 720 | 77.8% |
| double_faults | gbm_v1_double_faults | 33 | 2017-09-01 | 2017-10-01 | 289 | 83.0% |
| double_faults | gbm_v1_double_faults | 34 | 2017-10-01 | 2017-11-01 | 550 | 76.7% |
| double_faults | gbm_v1_double_faults | 35 | 2017-11-01 | 2017-12-01 | 123 | 86.2% |
| double_faults | gbm_v1_double_faults | 37 | 2018-01-01 | 2018-02-01 | 498 | 80.9% |
| double_faults | gbm_v1_double_faults | 38 | 2018-02-01 | 2018-03-01 | 670 | 76.3% |
| double_faults | gbm_v1_double_faults | 39 | 2018-03-01 | 2018-04-01 | 458 | 79.0% |
| double_faults | gbm_v1_double_faults | 40 | 2018-04-01 | 2018-05-01 | 451 | 74.7% |
| double_faults | gbm_v1_double_faults | 41 | 2018-05-01 | 2018-06-01 | 712 | 81.2% |
| double_faults | gbm_v1_double_faults | 42 | 2018-06-01 | 2018-07-01 | 335 | 85.7% |
| double_faults | gbm_v1_double_faults | 43 | 2018-07-01 | 2018-08-01 | 592 | 78.4% |
| double_faults | gbm_v1_double_faults | 44 | 2018-08-01 | 2018-09-01 | 711 | 77.5% |
| double_faults | gbm_v1_double_faults | 45 | 2018-09-01 | 2018-10-01 | 286 | 82.5% |
| double_faults | gbm_v1_double_faults | 46 | 2018-10-01 | 2018-11-01 | 559 | 78.9% |
| double_faults | gbm_v1_double_faults | 47 | 2018-11-01 | 2018-12-01 | 95 | 75.8% |
| double_faults | gbm_v1_double_faults | 49 | 2019-01-01 | 2019-02-01 | 521 | 80.0% |
| double_faults | gbm_v1_double_faults | 50 | 2019-02-01 | 2019-03-01 | 683 | 80.4% |
| double_faults | gbm_v1_double_faults | 51 | 2019-03-01 | 2019-04-01 | 409 | 80.7% |
| double_faults | gbm_v1_double_faults | 52 | 2019-04-01 | 2019-05-01 | 362 | 82.3% |
| double_faults | gbm_v1_double_faults | 53 | 2019-05-01 | 2019-06-01 | 658 | 80.5% |
| double_faults | gbm_v1_double_faults | 54 | 2019-06-01 | 2019-07-01 | 333 | 82.6% |
| double_faults | gbm_v1_double_faults | 55 | 2019-07-01 | 2019-08-01 | 672 | 80.5% |
| double_faults | gbm_v1_double_faults | 56 | 2019-08-01 | 2019-09-01 | 639 | 79.7% |
| double_faults | gbm_v1_double_faults | 57 | 2019-09-01 | 2019-10-01 | 214 | 72.9% |
| double_faults | gbm_v1_double_faults | 58 | 2019-10-01 | 2019-11-01 | 590 | 81.0% |
| double_faults | gbm_v1_double_faults | 59 | 2019-11-01 | 2019-12-01 | 169 | 70.4% |
| double_faults | gbm_v1_double_faults | 61 | 2020-01-01 | 2020-02-01 | 562 | 78.1% |
| double_faults | gbm_v1_double_faults | 62 | 2020-02-01 | 2020-03-01 | 641 | 79.1% |
| double_faults | gbm_v1_double_faults | 63 | 2020-03-01 | 2020-04-01 | 108 | 80.6% |
| double_faults | gbm_v1_double_faults | 68 | 2020-08-01 | 2020-09-01 | 229 | 78.2% |
| double_faults | gbm_v1_double_faults | 69 | 2020-09-01 | 2020-10-01 | 552 | 76.8% |
| double_faults | gbm_v1_double_faults | 70 | 2020-10-01 | 2020-11-01 | 400 | 78.8% |
| double_faults | gbm_v1_double_faults | 71 | 2020-11-01 | 2020-12-01 | 192 | 80.7% |
| double_faults | gbm_v1_double_faults | 73 | 2021-01-01 | 2021-02-01 | 102 | 81.4% |
| double_faults | gbm_v1_double_faults | 74 | 2021-02-01 | 2021-03-01 | 633 | 83.1% |
| double_faults | gbm_v1_double_faults | 75 | 2021-03-01 | 2021-04-01 | 602 | 79.6% |
| double_faults | gbm_v1_double_faults | 76 | 2021-04-01 | 2021-05-01 | 451 | 83.8% |
| double_faults | gbm_v1_double_faults | 77 | 2021-05-01 | 2021-06-01 | 550 | 83.8% |
| double_faults | gbm_v1_double_faults | 78 | 2021-06-01 | 2021-07-01 | 619 | 83.0% |
| double_faults | gbm_v1_double_faults | 79 | 2021-07-01 | 2021-08-01 | 433 | 76.7% |
| double_faults | gbm_v1_double_faults | 80 | 2021-08-01 | 2021-09-01 | 578 | 80.3% |
| double_faults | gbm_v1_double_faults | 81 | 2021-09-01 | 2021-10-01 | 306 | 78.8% |
| double_faults | gbm_v1_double_faults | 82 | 2021-10-01 | 2021-11-01 | 436 | 77.3% |
| double_faults | gbm_v1_double_faults | 83 | 2021-11-01 | 2021-12-01 | 296 | 80.1% |
| double_faults | gbm_v1_double_faults | 84 | 2021-12-01 | 2022-01-01 | 20 | 85.0% |
| double_faults | gbm_v1_double_faults | 85 | 2022-01-01 | 2022-02-01 | 564 | 81.6% |
| double_faults | gbm_v1_double_faults | 86 | 2022-02-01 | 2022-03-01 | 708 | 77.8% |
| double_faults | gbm_v1_double_faults | 87 | 2022-03-01 | 2022-04-01 | 458 | 77.5% |
| double_faults | gbm_v1_double_faults | 88 | 2022-04-01 | 2022-05-01 | 460 | 75.7% |
| double_faults | gbm_v1_double_faults | 89 | 2022-05-01 | 2022-06-01 | 562 | 79.0% |
| double_faults | gbm_v1_double_faults | 90 | 2022-06-01 | 2022-07-01 | 552 | 76.3% |
| double_faults | gbm_v1_double_faults | 91 | 2022-07-01 | 2022-08-01 | 368 | 79.3% |
| double_faults | gbm_v1_double_faults | 92 | 2022-08-01 | 2022-09-01 | 661 | 77.8% |
| double_faults | gbm_v1_double_faults | 93 | 2022-09-01 | 2022-10-01 | 261 | 76.6% |
| double_faults | gbm_v1_double_faults | 94 | 2022-10-01 | 2022-11-01 | 507 | 72.4% |
| double_faults | gbm_v1_double_faults | 95 | 2022-11-01 | 2022-12-01 | 163 | 69.3% |
| double_faults | gbm_v1_double_faults | 97 | 2023-01-01 | 2023-02-01 | 543 | 80.7% |
| double_faults | gbm_v1_double_faults | 98 | 2023-02-01 | 2023-03-01 | 475 | 77.7% |
| double_faults | gbm_v1_double_faults | 99 | 2023-03-01 | 2023-04-01 | 543 | 77.2% |
| double_faults | gbm_v1_double_faults | 100 | 2023-04-01 | 2023-05-01 | 638 | 79.5% |
| double_faults | gbm_v1_double_faults | 101 | 2023-05-01 | 2023-06-01 | 494 | 78.1% |
| double_faults | gbm_v1_double_faults | 102 | 2023-06-01 | 2023-07-01 | 350 | 76.6% |
| double_faults | gbm_v1_double_faults | 103 | 2023-07-01 | 2023-08-01 | 567 | 78.5% |
| double_faults | gbm_v1_double_faults | 104 | 2023-08-01 | 2023-09-01 | 719 | 74.8% |
| double_faults | gbm_v1_double_faults | 105 | 2023-09-01 | 2023-10-01 | 296 | 80.7% |
| double_faults | gbm_v1_double_faults | 106 | 2023-10-01 | 2023-11-01 | 527 | 84.3% |
| double_faults | gbm_v1_double_faults | 107 | 2023-11-01 | 2023-12-01 | 238 | 83.2% |
| double_faults | gbm_v1_double_faults | 108 | 2023-12-01 | 2024-01-01 | 6 | 33.3% |
| double_faults | gbm_v1_double_faults | 109 | 2024-01-01 | 2024-02-01 | 532 | 79.1% |
| double_faults | gbm_v1_double_faults | 110 | 2024-02-01 | 2024-03-01 | 743 | 81.4% |
| double_faults | gbm_v1_double_faults | 111 | 2024-03-01 | 2024-04-01 | 412 | 82.5% |
| double_faults | gbm_v1_double_faults | 112 | 2024-04-01 | 2024-05-01 | 642 | 79.1% |
| double_faults | gbm_v1_double_faults | 113 | 2024-05-01 | 2024-06-01 | 527 | 83.9% |
| double_faults | gbm_v1_double_faults | 114 | 2024-06-01 | 2024-07-01 | 329 | 80.5% |
| double_faults | gbm_v1_double_faults | 115 | 2024-07-01 | 2024-08-01 | 756 | 75.3% |
| double_faults | gbm_v1_double_faults | 116 | 2024-08-01 | 2024-09-01 | 603 | 71.0% |
| double_faults | gbm_v1_double_faults | 117 | 2024-09-01 | 2024-10-01 | 342 | 79.8% |
| double_faults | gbm_v1_double_faults | 118 | 2024-10-01 | 2024-11-01 | 568 | 84.2% |
| double_faults | gbm_v1_double_faults | 119 | 2024-11-01 | 2024-12-01 | 175 | 77.7% |
| double_faults | gbm_v1_double_faults | 120 | 2024-12-01 | 2025-01-01 | 69 | 78.3% |
| double_faults | gbm_v1_double_faults | 121 | 2025-01-01 | 2025-02-01 | 518 | 77.4% |
| double_faults | gbm_v1_double_faults | 122 | 2025-02-01 | 2025-03-01 | 563 | 79.2% |
| double_faults | gbm_v1_double_faults | 123 | 2025-03-01 | 2025-04-01 | 387 | 80.6% |
| double_faults | gbm_v1_double_faults | 124 | 2025-04-01 | 2025-05-01 | 570 | 77.5% |
| double_faults | gbm_v1_double_faults | 125 | 2025-05-01 | 2025-06-01 | 540 | 78.9% |
| double_faults | gbm_v1_double_faults | 126 | 2025-06-01 | 2025-07-01 | 455 | 78.7% |
| double_faults | gbm_v1_double_faults | 127 | 2025-07-01 | 2025-08-01 | 635 | 74.8% |
| double_faults | gbm_v1_double_faults | 128 | 2025-08-01 | 2025-09-01 | 531 | 73.3% |
| double_faults | gbm_v1_double_faults | 129 | 2025-09-01 | 2025-10-01 | 247 | 81.8% |
| double_faults | gbm_v1_double_faults | 130 | 2025-10-01 | 2025-11-01 | 570 | 75.6% |
| double_faults | gbm_v1_double_faults | 131 | 2025-11-01 | 2025-12-01 | 134 | 81.3% |
| double_faults | gbm_v1_double_faults | 132 | 2025-12-01 | 2026-01-01 | 27 | 66.7% |
| double_faults | gbm_v1_double_faults | 133 | 2026-01-01 | 2026-02-01 | 217 | 81.6% |
| double_faults | gbm_v1_double_faults | 134 | 2026-02-01 | 2026-03-01 | 1009 | 78.9% |
| double_faults | gbm_v1_double_faults | 135 | 2026-03-01 | 2026-04-01 | 1365 | 75.4% |
| double_faults | gbm_v1_double_faults | 136 | 2026-04-01 | 2026-05-01 | 1857 | 78.4% |
| double_faults | gbm_v1_double_faults | 137 | 2026-05-01 | 2026-06-01 | 1546 | 79.6% |
| double_faults | gbm_v1_double_faults | 138 | 2026-06-01 | 2026-07-01 | 1542 | 79.4% |
| double_faults | gbm_v1_double_faults | 139 | 2026-07-01 | 2026-08-01 | 1862 | 80.4% |
| double_faults | gbm_v1_double_faults | 140 | 2026-08-01 | 2026-09-01 | 1606 | 78.6% |
| double_faults | gbm_v1_double_faults | 141 | 2026-09-01 | 2026-10-01 | 1088 | 80.8% |
| service_games | baseline_v1_service_games | 2 | 2015-02-01 | 2015-03-01 | 426 | 64.6% |
| service_games | baseline_v1_service_games | 3 | 2015-03-01 | 2015-04-01 | 344 | 72.1% |
| service_games | baseline_v1_service_games | 4 | 2015-04-01 | 2015-05-01 | 413 | 69.2% |
| service_games | baseline_v1_service_games | 5 | 2015-05-01 | 2015-06-01 | 580 | 43.1% |
| service_games | baseline_v1_service_games | 6 | 2015-06-01 | 2015-07-01 | 476 | 53.6% |
| service_games | baseline_v1_service_games | 7 | 2015-07-01 | 2015-08-01 | 368 | 68.2% |
| service_games | baseline_v1_service_games | 8 | 2015-08-01 | 2015-09-01 | 574 | 68.5% |
| service_games | baseline_v1_service_games | 9 | 2015-09-01 | 2015-10-01 | 262 | 52.7% |
| service_games | baseline_v1_service_games | 10 | 2015-10-01 | 2015-11-01 | 544 | 74.8% |
| service_games | baseline_v1_service_games | 11 | 2015-11-01 | 2015-12-01 | 128 | 67.2% |
| service_games | baseline_v1_service_games | 13 | 2016-01-01 | 2016-02-01 | 479 | 46.3% |
| service_games | baseline_v1_service_games | 14 | 2016-02-01 | 2016-03-01 | 631 | 76.1% |
| service_games | baseline_v1_service_games | 15 | 2016-03-01 | 2016-04-01 | 431 | 74.2% |
| service_games | baseline_v1_service_games | 16 | 2016-04-01 | 2016-05-01 | 486 | 73.7% |
| service_games | baseline_v1_service_games | 17 | 2016-05-01 | 2016-06-01 | 560 | 42.9% |
| service_games | baseline_v1_service_games | 18 | 2016-06-01 | 2016-07-01 | 526 | 45.1% |
| service_games | baseline_v1_service_games | 19 | 2016-07-01 | 2016-08-01 | 564 | 76.4% |
| service_games | baseline_v1_service_games | 20 | 2016-08-01 | 2016-09-01 | 633 | 56.7% |
| service_games | baseline_v1_service_games | 21 | 2016-09-01 | 2016-10-01 | 278 | 62.9% |
| service_games | baseline_v1_service_games | 22 | 2016-10-01 | 2016-11-01 | 514 | 72.4% |
| service_games | baseline_v1_service_games | 23 | 2016-11-01 | 2016-12-01 | 130 | 67.7% |
| service_games | baseline_v1_service_games | 25 | 2017-01-01 | 2017-02-01 | 492 | 44.3% |
| service_games | baseline_v1_service_games | 26 | 2017-02-01 | 2017-03-01 | 562 | 74.4% |
| service_games | baseline_v1_service_games | 27 | 2017-03-01 | 2017-04-01 | 544 | 73.0% |
| service_games | baseline_v1_service_games | 28 | 2017-04-01 | 2017-05-01 | 434 | 59.2% |
| service_games | baseline_v1_service_games | 29 | 2017-05-01 | 2017-06-01 | 676 | 48.5% |
| service_games | baseline_v1_service_games | 30 | 2017-06-01 | 2017-07-01 | 346 | 63.3% |
| service_games | baseline_v1_service_games | 31 | 2017-07-01 | 2017-08-01 | 573 | 45.0% |
| service_games | baseline_v1_service_games | 32 | 2017-08-01 | 2017-09-01 | 720 | 58.1% |
| service_games | baseline_v1_service_games | 33 | 2017-09-01 | 2017-10-01 | 289 | 68.5% |
| service_games | baseline_v1_service_games | 34 | 2017-10-01 | 2017-11-01 | 550 | 74.7% |
| service_games | baseline_v1_service_games | 35 | 2017-11-01 | 2017-12-01 | 123 | 53.7% |
| service_games | baseline_v1_service_games | 37 | 2018-01-01 | 2018-02-01 | 498 | 43.6% |
| service_games | baseline_v1_service_games | 38 | 2018-02-01 | 2018-03-01 | 670 | 71.0% |
| service_games | baseline_v1_service_games | 39 | 2018-03-01 | 2018-04-01 | 458 | 69.2% |
| service_games | baseline_v1_service_games | 40 | 2018-04-01 | 2018-05-01 | 451 | 63.2% |
| service_games | baseline_v1_service_games | 41 | 2018-05-01 | 2018-06-01 | 712 | 50.1% |
| service_games | baseline_v1_service_games | 42 | 2018-06-01 | 2018-07-01 | 335 | 77.3% |
| service_games | baseline_v1_service_games | 43 | 2018-07-01 | 2018-08-01 | 592 | 52.4% |
| service_games | baseline_v1_service_games | 44 | 2018-08-01 | 2018-09-01 | 711 | 63.6% |
| service_games | baseline_v1_service_games | 45 | 2018-09-01 | 2018-10-01 | 286 | 66.1% |
| service_games | baseline_v1_service_games | 46 | 2018-10-01 | 2018-11-01 | 559 | 77.5% |
| service_games | baseline_v1_service_games | 47 | 2018-11-01 | 2018-12-01 | 95 | 69.5% |
| service_games | baseline_v1_service_games | 49 | 2019-01-01 | 2019-02-01 | 521 | 47.0% |
| service_games | baseline_v1_service_games | 50 | 2019-02-01 | 2019-03-01 | 683 | 74.2% |
| service_games | baseline_v1_service_games | 51 | 2019-03-01 | 2019-04-01 | 409 | 73.3% |
| service_games | baseline_v1_service_games | 52 | 2019-04-01 | 2019-05-01 | 362 | 69.1% |
| service_games | baseline_v1_service_games | 53 | 2019-05-01 | 2019-06-01 | 658 | 44.8% |
| service_games | baseline_v1_service_games | 54 | 2019-06-01 | 2019-07-01 | 333 | 75.4% |
| service_games | baseline_v1_service_games | 55 | 2019-07-01 | 2019-08-01 | 672 | 53.4% |
| service_games | baseline_v1_service_games | 56 | 2019-08-01 | 2019-09-01 | 639 | 58.7% |
| service_games | baseline_v1_service_games | 57 | 2019-09-01 | 2019-10-01 | 214 | 80.4% |
| service_games | baseline_v1_service_games | 58 | 2019-10-01 | 2019-11-01 | 590 | 79.8% |
| service_games | baseline_v1_service_games | 59 | 2019-11-01 | 2019-12-01 | 169 | 62.7% |
| service_games | baseline_v1_service_games | 61 | 2020-01-01 | 2020-02-01 | 562 | 50.2% |
| service_games | baseline_v1_service_games | 62 | 2020-02-01 | 2020-03-01 | 641 | 73.8% |
| service_games | baseline_v1_service_games | 63 | 2020-03-01 | 2020-04-01 | 108 | 63.9% |
| service_games | baseline_v1_service_games | 68 | 2020-08-01 | 2020-09-01 | 229 | 42.8% |
| service_games | baseline_v1_service_games | 69 | 2020-09-01 | 2020-10-01 | 552 | 39.5% |
| service_games | baseline_v1_service_games | 70 | 2020-10-01 | 2020-11-01 | 400 | 78.0% |
| service_games | baseline_v1_service_games | 71 | 2020-11-01 | 2020-12-01 | 192 | 71.9% |
| service_games | baseline_v1_service_games | 73 | 2021-01-01 | 2021-02-01 | 102 | 84.3% |
| service_games | baseline_v1_service_games | 74 | 2021-02-01 | 2021-03-01 | 633 | 54.0% |
| service_games | baseline_v1_service_games | 75 | 2021-03-01 | 2021-04-01 | 602 | 74.8% |
| service_games | baseline_v1_service_games | 76 | 2021-04-01 | 2021-05-01 | 451 | 66.1% |
| service_games | baseline_v1_service_games | 77 | 2021-05-01 | 2021-06-01 | 550 | 56.5% |
| service_games | baseline_v1_service_games | 78 | 2021-06-01 | 2021-07-01 | 621 | 43.0% |
| service_games | baseline_v1_service_games | 79 | 2021-07-01 | 2021-08-01 | 433 | 73.2% |
| service_games | baseline_v1_service_games | 80 | 2021-08-01 | 2021-09-01 | 578 | 65.4% |
| service_games | baseline_v1_service_games | 81 | 2021-09-01 | 2021-10-01 | 306 | 66.3% |
| service_games | baseline_v1_service_games | 82 | 2021-10-01 | 2021-11-01 | 436 | 81.9% |
| service_games | baseline_v1_service_games | 83 | 2021-11-01 | 2021-12-01 | 296 | 67.2% |
| service_games | baseline_v1_service_games | 84 | 2021-12-01 | 2022-01-01 | 20 | 75.0% |
| service_games | baseline_v1_service_games | 85 | 2022-01-01 | 2022-02-01 | 564 | 53.0% |
| service_games | baseline_v1_service_games | 86 | 2022-02-01 | 2022-03-01 | 708 | 75.8% |
| service_games | baseline_v1_service_games | 87 | 2022-03-01 | 2022-04-01 | 458 | 72.7% |
| service_games | baseline_v1_service_games | 88 | 2022-04-01 | 2022-05-01 | 460 | 61.7% |
| service_games | baseline_v1_service_games | 89 | 2022-05-01 | 2022-06-01 | 562 | 44.5% |
| service_games | baseline_v1_service_games | 90 | 2022-06-01 | 2022-07-01 | 552 | 47.1% |
| service_games | baseline_v1_service_games | 91 | 2022-07-01 | 2022-08-01 | 368 | 75.0% |
| service_games | baseline_v1_service_games | 92 | 2022-08-01 | 2022-09-01 | 661 | 58.9% |
| service_games | baseline_v1_service_games | 93 | 2022-09-01 | 2022-10-01 | 261 | 75.1% |
| service_games | baseline_v1_service_games | 94 | 2022-10-01 | 2022-11-01 | 507 | 76.3% |
| service_games | baseline_v1_service_games | 95 | 2022-11-01 | 2022-12-01 | 163 | 60.7% |
| service_games | baseline_v1_service_games | 97 | 2023-01-01 | 2023-02-01 | 543 | 50.8% |
| service_games | baseline_v1_service_games | 98 | 2023-02-01 | 2023-03-01 | 475 | 77.5% |
| service_games | baseline_v1_service_games | 99 | 2023-03-01 | 2023-04-01 | 543 | 74.2% |
| service_games | baseline_v1_service_games | 100 | 2023-04-01 | 2023-05-01 | 638 | 61.0% |
| service_games | baseline_v1_service_games | 101 | 2023-05-01 | 2023-06-01 | 494 | 40.9% |
| service_games | baseline_v1_service_games | 102 | 2023-06-01 | 2023-07-01 | 350 | 71.1% |
| service_games | baseline_v1_service_games | 103 | 2023-07-01 | 2023-08-01 | 567 | 51.0% |
| service_games | baseline_v1_service_games | 104 | 2023-08-01 | 2023-09-01 | 719 | 59.4% |
| service_games | baseline_v1_service_games | 105 | 2023-09-01 | 2023-10-01 | 296 | 77.7% |
| service_games | baseline_v1_service_games | 106 | 2023-10-01 | 2023-11-01 | 527 | 72.5% |
| service_games | baseline_v1_service_games | 107 | 2023-11-01 | 2023-12-01 | 238 | 63.9% |
| service_games | baseline_v1_service_games | 108 | 2023-12-01 | 2024-01-01 | 6 | 50.0% |
| service_games | baseline_v1_service_games | 109 | 2024-01-01 | 2024-02-01 | 532 | 50.8% |
| service_games | baseline_v1_service_games | 110 | 2024-02-01 | 2024-03-01 | 743 | 77.7% |
| service_games | baseline_v1_service_games | 111 | 2024-03-01 | 2024-04-01 | 412 | 74.8% |
| service_games | baseline_v1_service_games | 112 | 2024-04-01 | 2024-05-01 | 642 | 61.4% |
| service_games | baseline_v1_service_games | 113 | 2024-05-01 | 2024-06-01 | 527 | 44.2% |
| service_games | baseline_v1_service_games | 114 | 2024-06-01 | 2024-07-01 | 329 | 77.5% |
| service_games | baseline_v1_service_games | 115 | 2024-07-01 | 2024-08-01 | 756 | 57.7% |
| service_games | baseline_v1_service_games | 116 | 2024-08-01 | 2024-09-01 | 601 | 54.2% |
| service_games | baseline_v1_service_games | 117 | 2024-09-01 | 2024-10-01 | 342 | 77.2% |
| service_games | baseline_v1_service_games | 118 | 2024-10-01 | 2024-11-01 | 568 | 74.8% |
| service_games | baseline_v1_service_games | 119 | 2024-11-01 | 2024-12-01 | 175 | 74.3% |
| service_games | baseline_v1_service_games | 120 | 2024-12-01 | 2025-01-01 | 69 | 59.4% |
| service_games | baseline_v1_service_games | 121 | 2025-01-01 | 2025-02-01 | 518 | 46.3% |
| service_games | baseline_v1_service_games | 122 | 2025-02-01 | 2025-03-01 | 563 | 75.7% |
| service_games | baseline_v1_service_games | 123 | 2025-03-01 | 2025-04-01 | 387 | 74.4% |
| service_games | baseline_v1_service_games | 124 | 2025-04-01 | 2025-05-01 | 570 | 65.4% |
| service_games | baseline_v1_service_games | 125 | 2025-05-01 | 2025-06-01 | 540 | 49.6% |
| service_games | baseline_v1_service_games | 126 | 2025-06-01 | 2025-07-01 | 455 | 57.8% |
| service_games | baseline_v1_service_games | 127 | 2025-07-01 | 2025-08-01 | 635 | 66.8% |
| service_games | baseline_v1_service_games | 128 | 2025-08-01 | 2025-09-01 | 531 | 53.3% |
| service_games | baseline_v1_service_games | 129 | 2025-09-01 | 2025-10-01 | 247 | 77.3% |
| service_games | baseline_v1_service_games | 130 | 2025-10-01 | 2025-11-01 | 570 | 73.9% |
| service_games | baseline_v1_service_games | 131 | 2025-11-01 | 2025-12-01 | 134 | 56.7% |
| service_games | baseline_v1_service_games | 132 | 2025-12-01 | 2026-01-01 | 27 | 14.8% |
| service_games | baseline_v1_service_games | 133 | 2026-01-01 | 2026-02-01 | 217 | 44.7% |
| service_games | baseline_v1_service_games | 134 | 2026-02-01 | 2026-03-01 | 1002 | 63.3% |
| service_games | baseline_v1_service_games | 135 | 2026-03-01 | 2026-04-01 | 1362 | 56.0% |
| service_games | baseline_v1_service_games | 136 | 2026-04-01 | 2026-05-01 | 1857 | 58.8% |
| service_games | baseline_v1_service_games | 137 | 2026-05-01 | 2026-06-01 | 1544 | 54.4% |
| service_games | baseline_v1_service_games | 138 | 2026-06-01 | 2026-07-01 | 1541 | 56.1% |
| service_games | baseline_v1_service_games | 139 | 2026-07-01 | 2026-08-01 | 1862 | 57.7% |
| service_games | baseline_v1_service_games | 140 | 2026-08-01 | 2026-09-01 | 1604 | 65.8% |
| service_games | baseline_v1_service_games | 141 | 2026-09-01 | 2026-10-01 | 1088 | 54.1% |
| service_games | ensemble_v1_service_games | 2 | 2015-02-01 | 2015-03-01 | 426 | 50.2% |
| service_games | ensemble_v1_service_games | 3 | 2015-03-01 | 2015-04-01 | 344 | 76.5% |
| service_games | ensemble_v1_service_games | 4 | 2015-04-01 | 2015-05-01 | 413 | 72.4% |
| service_games | ensemble_v1_service_games | 5 | 2015-05-01 | 2015-06-01 | 580 | 60.3% |
| service_games | ensemble_v1_service_games | 6 | 2015-06-01 | 2015-07-01 | 476 | 61.8% |
| service_games | ensemble_v1_service_games | 7 | 2015-07-01 | 2015-08-01 | 368 | 76.1% |
| service_games | ensemble_v1_service_games | 8 | 2015-08-01 | 2015-09-01 | 574 | 73.3% |
| service_games | ensemble_v1_service_games | 9 | 2015-09-01 | 2015-10-01 | 262 | 67.6% |
| service_games | ensemble_v1_service_games | 10 | 2015-10-01 | 2015-11-01 | 544 | 78.5% |
| service_games | ensemble_v1_service_games | 11 | 2015-11-01 | 2015-12-01 | 128 | 73.4% |
| service_games | ensemble_v1_service_games | 13 | 2016-01-01 | 2016-02-01 | 479 | 61.8% |
| service_games | ensemble_v1_service_games | 14 | 2016-02-01 | 2016-03-01 | 631 | 81.0% |
| service_games | ensemble_v1_service_games | 15 | 2016-03-01 | 2016-04-01 | 431 | 77.3% |
| service_games | ensemble_v1_service_games | 16 | 2016-04-01 | 2016-05-01 | 486 | 81.9% |
| service_games | ensemble_v1_service_games | 17 | 2016-05-01 | 2016-06-01 | 560 | 58.6% |
| service_games | ensemble_v1_service_games | 18 | 2016-06-01 | 2016-07-01 | 526 | 57.6% |
| service_games | ensemble_v1_service_games | 19 | 2016-07-01 | 2016-08-01 | 564 | 82.8% |
| service_games | ensemble_v1_service_games | 20 | 2016-08-01 | 2016-09-01 | 633 | 70.5% |
| service_games | ensemble_v1_service_games | 21 | 2016-09-01 | 2016-10-01 | 278 | 73.4% |
| service_games | ensemble_v1_service_games | 22 | 2016-10-01 | 2016-11-01 | 514 | 78.4% |
| service_games | ensemble_v1_service_games | 23 | 2016-11-01 | 2016-12-01 | 130 | 74.6% |
| service_games | ensemble_v1_service_games | 25 | 2017-01-01 | 2017-02-01 | 492 | 59.1% |
| service_games | ensemble_v1_service_games | 26 | 2017-02-01 | 2017-03-01 | 562 | 81.3% |
| service_games | ensemble_v1_service_games | 27 | 2017-03-01 | 2017-04-01 | 544 | 79.8% |
| service_games | ensemble_v1_service_games | 28 | 2017-04-01 | 2017-05-01 | 434 | 71.4% |
| service_games | ensemble_v1_service_games | 29 | 2017-05-01 | 2017-06-01 | 676 | 63.2% |
| service_games | ensemble_v1_service_games | 30 | 2017-06-01 | 2017-07-01 | 346 | 67.1% |
| service_games | ensemble_v1_service_games | 31 | 2017-07-01 | 2017-08-01 | 573 | 58.3% |
| service_games | ensemble_v1_service_games | 32 | 2017-08-01 | 2017-09-01 | 720 | 70.7% |
| service_games | ensemble_v1_service_games | 33 | 2017-09-01 | 2017-10-01 | 289 | 77.9% |
| service_games | ensemble_v1_service_games | 34 | 2017-10-01 | 2017-11-01 | 550 | 76.2% |
| service_games | ensemble_v1_service_games | 35 | 2017-11-01 | 2017-12-01 | 123 | 66.7% |
| service_games | ensemble_v1_service_games | 37 | 2018-01-01 | 2018-02-01 | 498 | 58.8% |
| service_games | ensemble_v1_service_games | 38 | 2018-02-01 | 2018-03-01 | 670 | 77.3% |
| service_games | ensemble_v1_service_games | 39 | 2018-03-01 | 2018-04-01 | 458 | 76.2% |
| service_games | ensemble_v1_service_games | 40 | 2018-04-01 | 2018-05-01 | 451 | 68.7% |
| service_games | ensemble_v1_service_games | 41 | 2018-05-01 | 2018-06-01 | 712 | 64.0% |
| service_games | ensemble_v1_service_games | 42 | 2018-06-01 | 2018-07-01 | 335 | 81.2% |
| service_games | ensemble_v1_service_games | 43 | 2018-07-01 | 2018-08-01 | 592 | 66.4% |
| service_games | ensemble_v1_service_games | 44 | 2018-08-01 | 2018-09-01 | 711 | 73.3% |
| service_games | ensemble_v1_service_games | 45 | 2018-09-01 | 2018-10-01 | 286 | 71.7% |
| service_games | ensemble_v1_service_games | 46 | 2018-10-01 | 2018-11-01 | 559 | 80.9% |
| service_games | ensemble_v1_service_games | 47 | 2018-11-01 | 2018-12-01 | 95 | 78.9% |
| service_games | ensemble_v1_service_games | 49 | 2019-01-01 | 2019-02-01 | 521 | 61.2% |
| service_games | ensemble_v1_service_games | 50 | 2019-02-01 | 2019-03-01 | 683 | 79.5% |
| service_games | ensemble_v1_service_games | 51 | 2019-03-01 | 2019-04-01 | 409 | 79.2% |
| service_games | ensemble_v1_service_games | 52 | 2019-04-01 | 2019-05-01 | 362 | 80.9% |
| service_games | ensemble_v1_service_games | 53 | 2019-05-01 | 2019-06-01 | 658 | 60.0% |
| service_games | ensemble_v1_service_games | 54 | 2019-06-01 | 2019-07-01 | 333 | 78.7% |
| service_games | ensemble_v1_service_games | 55 | 2019-07-01 | 2019-08-01 | 672 | 64.1% |
| service_games | ensemble_v1_service_games | 56 | 2019-08-01 | 2019-09-01 | 639 | 70.7% |
| service_games | ensemble_v1_service_games | 57 | 2019-09-01 | 2019-10-01 | 214 | 83.2% |
| service_games | ensemble_v1_service_games | 58 | 2019-10-01 | 2019-11-01 | 590 | 81.9% |
| service_games | ensemble_v1_service_games | 59 | 2019-11-01 | 2019-12-01 | 169 | 72.8% |
| service_games | ensemble_v1_service_games | 61 | 2020-01-01 | 2020-02-01 | 562 | 62.1% |
| service_games | ensemble_v1_service_games | 62 | 2020-02-01 | 2020-03-01 | 641 | 80.8% |
| service_games | ensemble_v1_service_games | 63 | 2020-03-01 | 2020-04-01 | 108 | 65.7% |
| service_games | ensemble_v1_service_games | 68 | 2020-08-01 | 2020-09-01 | 229 | 63.3% |
| service_games | ensemble_v1_service_games | 69 | 2020-09-01 | 2020-10-01 | 552 | 55.8% |
| service_games | ensemble_v1_service_games | 70 | 2020-10-01 | 2020-11-01 | 400 | 80.2% |
| service_games | ensemble_v1_service_games | 71 | 2020-11-01 | 2020-12-01 | 192 | 77.6% |
| service_games | ensemble_v1_service_games | 73 | 2021-01-01 | 2021-02-01 | 102 | 85.3% |
| service_games | ensemble_v1_service_games | 74 | 2021-02-01 | 2021-03-01 | 633 | 65.6% |
| service_games | ensemble_v1_service_games | 75 | 2021-03-01 | 2021-04-01 | 602 | 79.1% |
| service_games | ensemble_v1_service_games | 76 | 2021-04-01 | 2021-05-01 | 451 | 72.3% |
| service_games | ensemble_v1_service_games | 77 | 2021-05-01 | 2021-06-01 | 550 | 68.2% |
| service_games | ensemble_v1_service_games | 78 | 2021-06-01 | 2021-07-01 | 621 | 61.8% |
| service_games | ensemble_v1_service_games | 79 | 2021-07-01 | 2021-08-01 | 433 | 79.2% |
| service_games | ensemble_v1_service_games | 80 | 2021-08-01 | 2021-09-01 | 578 | 75.1% |
| service_games | ensemble_v1_service_games | 81 | 2021-09-01 | 2021-10-01 | 306 | 72.2% |
| service_games | ensemble_v1_service_games | 82 | 2021-10-01 | 2021-11-01 | 436 | 86.2% |
| service_games | ensemble_v1_service_games | 83 | 2021-11-01 | 2021-12-01 | 296 | 74.7% |
| service_games | ensemble_v1_service_games | 84 | 2021-12-01 | 2022-01-01 | 20 | 75.0% |
| service_games | ensemble_v1_service_games | 85 | 2022-01-01 | 2022-02-01 | 564 | 62.9% |
| service_games | ensemble_v1_service_games | 86 | 2022-02-01 | 2022-03-01 | 708 | 81.2% |
| service_games | ensemble_v1_service_games | 87 | 2022-03-01 | 2022-04-01 | 458 | 76.4% |
| service_games | ensemble_v1_service_games | 88 | 2022-04-01 | 2022-05-01 | 460 | 74.1% |
| service_games | ensemble_v1_service_games | 89 | 2022-05-01 | 2022-06-01 | 562 | 61.9% |
| service_games | ensemble_v1_service_games | 90 | 2022-06-01 | 2022-07-01 | 552 | 58.2% |
| service_games | ensemble_v1_service_games | 91 | 2022-07-01 | 2022-08-01 | 368 | 79.6% |
| service_games | ensemble_v1_service_games | 92 | 2022-08-01 | 2022-09-01 | 661 | 71.3% |
| service_games | ensemble_v1_service_games | 93 | 2022-09-01 | 2022-10-01 | 261 | 81.6% |
| service_games | ensemble_v1_service_games | 94 | 2022-10-01 | 2022-11-01 | 507 | 78.7% |
| service_games | ensemble_v1_service_games | 95 | 2022-11-01 | 2022-12-01 | 163 | 65.6% |
| service_games | ensemble_v1_service_games | 97 | 2023-01-01 | 2023-02-01 | 543 | 63.7% |
| service_games | ensemble_v1_service_games | 98 | 2023-02-01 | 2023-03-01 | 475 | 80.4% |
| service_games | ensemble_v1_service_games | 99 | 2023-03-01 | 2023-04-01 | 543 | 81.0% |
| service_games | ensemble_v1_service_games | 100 | 2023-04-01 | 2023-05-01 | 638 | 69.9% |
| service_games | ensemble_v1_service_games | 101 | 2023-05-01 | 2023-06-01 | 494 | 58.9% |
| service_games | ensemble_v1_service_games | 102 | 2023-06-01 | 2023-07-01 | 350 | 80.6% |
| service_games | ensemble_v1_service_games | 103 | 2023-07-01 | 2023-08-01 | 567 | 66.1% |
| service_games | ensemble_v1_service_games | 104 | 2023-08-01 | 2023-09-01 | 719 | 69.1% |
| service_games | ensemble_v1_service_games | 105 | 2023-09-01 | 2023-10-01 | 296 | 79.1% |
| service_games | ensemble_v1_service_games | 106 | 2023-10-01 | 2023-11-01 | 527 | 79.1% |
| service_games | ensemble_v1_service_games | 107 | 2023-11-01 | 2023-12-01 | 238 | 68.1% |
| service_games | ensemble_v1_service_games | 108 | 2023-12-01 | 2024-01-01 | 6 | 50.0% |
| service_games | ensemble_v1_service_games | 109 | 2024-01-01 | 2024-02-01 | 532 | 66.0% |
| service_games | ensemble_v1_service_games | 110 | 2024-02-01 | 2024-03-01 | 743 | 81.6% |
| service_games | ensemble_v1_service_games | 111 | 2024-03-01 | 2024-04-01 | 412 | 82.3% |
| service_games | ensemble_v1_service_games | 112 | 2024-04-01 | 2024-05-01 | 642 | 73.5% |
| service_games | ensemble_v1_service_games | 113 | 2024-05-01 | 2024-06-01 | 527 | 61.9% |
| service_games | ensemble_v1_service_games | 114 | 2024-06-01 | 2024-07-01 | 329 | 82.7% |
| service_games | ensemble_v1_service_games | 115 | 2024-07-01 | 2024-08-01 | 756 | 70.0% |
| service_games | ensemble_v1_service_games | 116 | 2024-08-01 | 2024-09-01 | 601 | 66.2% |
| service_games | ensemble_v1_service_games | 117 | 2024-09-01 | 2024-10-01 | 342 | 81.9% |
| service_games | ensemble_v1_service_games | 118 | 2024-10-01 | 2024-11-01 | 568 | 80.6% |
| service_games | ensemble_v1_service_games | 119 | 2024-11-01 | 2024-12-01 | 175 | 77.7% |
| service_games | ensemble_v1_service_games | 120 | 2024-12-01 | 2025-01-01 | 69 | 62.3% |
| service_games | ensemble_v1_service_games | 121 | 2025-01-01 | 2025-02-01 | 518 | 63.9% |
| service_games | ensemble_v1_service_games | 122 | 2025-02-01 | 2025-03-01 | 563 | 78.2% |
| service_games | ensemble_v1_service_games | 123 | 2025-03-01 | 2025-04-01 | 387 | 78.0% |
| service_games | ensemble_v1_service_games | 124 | 2025-04-01 | 2025-05-01 | 570 | 72.6% |
| service_games | ensemble_v1_service_games | 125 | 2025-05-01 | 2025-06-01 | 540 | 64.6% |
| service_games | ensemble_v1_service_games | 126 | 2025-06-01 | 2025-07-01 | 455 | 67.3% |
| service_games | ensemble_v1_service_games | 127 | 2025-07-01 | 2025-08-01 | 635 | 75.4% |
| service_games | ensemble_v1_service_games | 128 | 2025-08-01 | 2025-09-01 | 531 | 63.5% |
| service_games | ensemble_v1_service_games | 129 | 2025-09-01 | 2025-10-01 | 247 | 82.2% |
| service_games | ensemble_v1_service_games | 130 | 2025-10-01 | 2025-11-01 | 570 | 79.1% |
| service_games | ensemble_v1_service_games | 131 | 2025-11-01 | 2025-12-01 | 134 | 64.9% |
| service_games | ensemble_v1_service_games | 132 | 2025-12-01 | 2026-01-01 | 27 | 14.8% |
| service_games | ensemble_v1_service_games | 133 | 2026-01-01 | 2026-02-01 | 217 | 52.1% |
| service_games | ensemble_v1_service_games | 134 | 2026-02-01 | 2026-03-01 | 1002 | 73.5% |
| service_games | ensemble_v1_service_games | 135 | 2026-03-01 | 2026-04-01 | 1362 | 68.6% |
| service_games | ensemble_v1_service_games | 136 | 2026-04-01 | 2026-05-01 | 1857 | 72.2% |
| service_games | ensemble_v1_service_games | 137 | 2026-05-01 | 2026-06-01 | 1544 | 67.6% |
| service_games | ensemble_v1_service_games | 138 | 2026-06-01 | 2026-07-01 | 1541 | 69.2% |
| service_games | ensemble_v1_service_games | 139 | 2026-07-01 | 2026-08-01 | 1862 | 68.2% |
| service_games | ensemble_v1_service_games | 140 | 2026-08-01 | 2026-09-01 | 1604 | 75.9% |
| service_games | ensemble_v1_service_games | 141 | 2026-09-01 | 2026-10-01 | 1088 | 66.9% |
| service_games | gbm_v1_service_games | 2 | 2015-02-01 | 2015-03-01 | 426 | 37.8% |
| service_games | gbm_v1_service_games | 3 | 2015-03-01 | 2015-04-01 | 344 | 73.0% |
| service_games | gbm_v1_service_games | 4 | 2015-04-01 | 2015-05-01 | 413 | 69.5% |
| service_games | gbm_v1_service_games | 5 | 2015-05-01 | 2015-06-01 | 580 | 70.9% |
| service_games | gbm_v1_service_games | 6 | 2015-06-01 | 2015-07-01 | 476 | 67.9% |
| service_games | gbm_v1_service_games | 7 | 2015-07-01 | 2015-08-01 | 368 | 73.1% |
| service_games | gbm_v1_service_games | 8 | 2015-08-01 | 2015-09-01 | 574 | 73.3% |
| service_games | gbm_v1_service_games | 9 | 2015-09-01 | 2015-10-01 | 262 | 77.9% |
| service_games | gbm_v1_service_games | 10 | 2015-10-01 | 2015-11-01 | 544 | 75.9% |
| service_games | gbm_v1_service_games | 11 | 2015-11-01 | 2015-12-01 | 128 | 73.4% |
| service_games | gbm_v1_service_games | 13 | 2016-01-01 | 2016-02-01 | 479 | 74.9% |
| service_games | gbm_v1_service_games | 14 | 2016-02-01 | 2016-03-01 | 631 | 72.4% |
| service_games | gbm_v1_service_games | 15 | 2016-03-01 | 2016-04-01 | 431 | 70.8% |
| service_games | gbm_v1_service_games | 16 | 2016-04-01 | 2016-05-01 | 486 | 81.5% |
| service_games | gbm_v1_service_games | 17 | 2016-05-01 | 2016-06-01 | 560 | 76.4% |
| service_games | gbm_v1_service_games | 18 | 2016-06-01 | 2016-07-01 | 526 | 78.7% |
| service_games | gbm_v1_service_games | 19 | 2016-07-01 | 2016-08-01 | 564 | 77.1% |
| service_games | gbm_v1_service_games | 20 | 2016-08-01 | 2016-09-01 | 633 | 74.4% |
| service_games | gbm_v1_service_games | 21 | 2016-09-01 | 2016-10-01 | 278 | 79.1% |
| service_games | gbm_v1_service_games | 22 | 2016-10-01 | 2016-11-01 | 514 | 77.0% |
| service_games | gbm_v1_service_games | 23 | 2016-11-01 | 2016-12-01 | 130 | 74.6% |
| service_games | gbm_v1_service_games | 25 | 2017-01-01 | 2017-02-01 | 492 | 74.0% |
| service_games | gbm_v1_service_games | 26 | 2017-02-01 | 2017-03-01 | 562 | 80.2% |
| service_games | gbm_v1_service_games | 27 | 2017-03-01 | 2017-04-01 | 544 | 77.2% |
| service_games | gbm_v1_service_games | 28 | 2017-04-01 | 2017-05-01 | 434 | 76.0% |
| service_games | gbm_v1_service_games | 29 | 2017-05-01 | 2017-06-01 | 676 | 77.7% |
| service_games | gbm_v1_service_games | 30 | 2017-06-01 | 2017-07-01 | 346 | 70.5% |
| service_games | gbm_v1_service_games | 31 | 2017-07-01 | 2017-08-01 | 573 | 74.0% |
| service_games | gbm_v1_service_games | 32 | 2017-08-01 | 2017-09-01 | 720 | 78.8% |
| service_games | gbm_v1_service_games | 33 | 2017-09-01 | 2017-10-01 | 289 | 78.2% |
| service_games | gbm_v1_service_games | 34 | 2017-10-01 | 2017-11-01 | 550 | 72.9% |
| service_games | gbm_v1_service_games | 35 | 2017-11-01 | 2017-12-01 | 123 | 70.7% |
| service_games | gbm_v1_service_games | 37 | 2018-01-01 | 2018-02-01 | 498 | 76.5% |
| service_games | gbm_v1_service_games | 38 | 2018-02-01 | 2018-03-01 | 670 | 77.6% |
| service_games | gbm_v1_service_games | 39 | 2018-03-01 | 2018-04-01 | 458 | 78.2% |
| service_games | gbm_v1_service_games | 40 | 2018-04-01 | 2018-05-01 | 451 | 73.2% |
| service_games | gbm_v1_service_games | 41 | 2018-05-01 | 2018-06-01 | 712 | 74.6% |
| service_games | gbm_v1_service_games | 42 | 2018-06-01 | 2018-07-01 | 335 | 82.4% |
| service_games | gbm_v1_service_games | 43 | 2018-07-01 | 2018-08-01 | 592 | 78.2% |
| service_games | gbm_v1_service_games | 44 | 2018-08-01 | 2018-09-01 | 711 | 80.7% |
| service_games | gbm_v1_service_games | 45 | 2018-09-01 | 2018-10-01 | 286 | 75.2% |
| service_games | gbm_v1_service_games | 46 | 2018-10-01 | 2018-11-01 | 559 | 78.4% |
| service_games | gbm_v1_service_games | 47 | 2018-11-01 | 2018-12-01 | 95 | 75.8% |
| service_games | gbm_v1_service_games | 49 | 2019-01-01 | 2019-02-01 | 521 | 76.2% |
| service_games | gbm_v1_service_games | 50 | 2019-02-01 | 2019-03-01 | 683 | 80.7% |
| service_games | gbm_v1_service_games | 51 | 2019-03-01 | 2019-04-01 | 409 | 76.0% |
| service_games | gbm_v1_service_games | 52 | 2019-04-01 | 2019-05-01 | 362 | 82.0% |
| service_games | gbm_v1_service_games | 53 | 2019-05-01 | 2019-06-01 | 658 | 81.5% |
| service_games | gbm_v1_service_games | 54 | 2019-06-01 | 2019-07-01 | 333 | 78.1% |
| service_games | gbm_v1_service_games | 55 | 2019-07-01 | 2019-08-01 | 672 | 76.9% |
| service_games | gbm_v1_service_games | 56 | 2019-08-01 | 2019-09-01 | 639 | 77.5% |
| service_games | gbm_v1_service_games | 57 | 2019-09-01 | 2019-10-01 | 214 | 75.2% |
| service_games | gbm_v1_service_games | 58 | 2019-10-01 | 2019-11-01 | 590 | 76.4% |
| service_games | gbm_v1_service_games | 59 | 2019-11-01 | 2019-12-01 | 169 | 71.6% |
| service_games | gbm_v1_service_games | 61 | 2020-01-01 | 2020-02-01 | 562 | 75.6% |
| service_games | gbm_v1_service_games | 62 | 2020-02-01 | 2020-03-01 | 641 | 79.3% |
| service_games | gbm_v1_service_games | 63 | 2020-03-01 | 2020-04-01 | 108 | 68.5% |
| service_games | gbm_v1_service_games | 68 | 2020-08-01 | 2020-09-01 | 229 | 76.0% |
| service_games | gbm_v1_service_games | 69 | 2020-09-01 | 2020-10-01 | 552 | 74.8% |
| service_games | gbm_v1_service_games | 70 | 2020-10-01 | 2020-11-01 | 400 | 74.2% |
| service_games | gbm_v1_service_games | 71 | 2020-11-01 | 2020-12-01 | 192 | 77.6% |
| service_games | gbm_v1_service_games | 73 | 2021-01-01 | 2021-02-01 | 102 | 79.4% |
| service_games | gbm_v1_service_games | 74 | 2021-02-01 | 2021-03-01 | 633 | 78.7% |
| service_games | gbm_v1_service_games | 75 | 2021-03-01 | 2021-04-01 | 602 | 75.7% |
| service_games | gbm_v1_service_games | 76 | 2021-04-01 | 2021-05-01 | 451 | 71.8% |
| service_games | gbm_v1_service_games | 77 | 2021-05-01 | 2021-06-01 | 550 | 77.8% |
| service_games | gbm_v1_service_games | 78 | 2021-06-01 | 2021-07-01 | 621 | 83.3% |
| service_games | gbm_v1_service_games | 79 | 2021-07-01 | 2021-08-01 | 433 | 75.5% |
| service_games | gbm_v1_service_games | 80 | 2021-08-01 | 2021-09-01 | 578 | 80.6% |
| service_games | gbm_v1_service_games | 81 | 2021-09-01 | 2021-10-01 | 306 | 84.6% |
| service_games | gbm_v1_service_games | 82 | 2021-10-01 | 2021-11-01 | 436 | 80.5% |
| service_games | gbm_v1_service_games | 83 | 2021-11-01 | 2021-12-01 | 296 | 76.7% |
| service_games | gbm_v1_service_games | 84 | 2021-12-01 | 2022-01-01 | 20 | 80.0% |
| service_games | gbm_v1_service_games | 85 | 2022-01-01 | 2022-02-01 | 564 | 75.7% |
| service_games | gbm_v1_service_games | 86 | 2022-02-01 | 2022-03-01 | 708 | 76.0% |
| service_games | gbm_v1_service_games | 87 | 2022-03-01 | 2022-04-01 | 458 | 77.7% |
| service_games | gbm_v1_service_games | 88 | 2022-04-01 | 2022-05-01 | 460 | 80.2% |
| service_games | gbm_v1_service_games | 89 | 2022-05-01 | 2022-06-01 | 562 | 79.4% |
| service_games | gbm_v1_service_games | 90 | 2022-06-01 | 2022-07-01 | 552 | 77.4% |
| service_games | gbm_v1_service_games | 91 | 2022-07-01 | 2022-08-01 | 368 | 80.4% |
| service_games | gbm_v1_service_games | 92 | 2022-08-01 | 2022-09-01 | 661 | 77.8% |
| service_games | gbm_v1_service_games | 93 | 2022-09-01 | 2022-10-01 | 261 | 79.3% |
| service_games | gbm_v1_service_games | 94 | 2022-10-01 | 2022-11-01 | 507 | 76.5% |
| service_games | gbm_v1_service_games | 95 | 2022-11-01 | 2022-12-01 | 163 | 68.1% |
| service_games | gbm_v1_service_games | 97 | 2023-01-01 | 2023-02-01 | 543 | 77.2% |
| service_games | gbm_v1_service_games | 98 | 2023-02-01 | 2023-03-01 | 475 | 80.2% |
| service_games | gbm_v1_service_games | 99 | 2023-03-01 | 2023-04-01 | 543 | 78.1% |
| service_games | gbm_v1_service_games | 100 | 2023-04-01 | 2023-05-01 | 638 | 77.4% |
| service_games | gbm_v1_service_games | 101 | 2023-05-01 | 2023-06-01 | 494 | 77.1% |
| service_games | gbm_v1_service_games | 102 | 2023-06-01 | 2023-07-01 | 350 | 84.6% |
| service_games | gbm_v1_service_games | 103 | 2023-07-01 | 2023-08-01 | 567 | 81.7% |
| service_games | gbm_v1_service_games | 104 | 2023-08-01 | 2023-09-01 | 719 | 75.2% |
| service_games | gbm_v1_service_games | 105 | 2023-09-01 | 2023-10-01 | 296 | 81.4% |
| service_games | gbm_v1_service_games | 106 | 2023-10-01 | 2023-11-01 | 527 | 78.4% |
| service_games | gbm_v1_service_games | 107 | 2023-11-01 | 2023-12-01 | 238 | 69.7% |
| service_games | gbm_v1_service_games | 108 | 2023-12-01 | 2024-01-01 | 6 | 33.3% |
| service_games | gbm_v1_service_games | 109 | 2024-01-01 | 2024-02-01 | 532 | 75.2% |
| service_games | gbm_v1_service_games | 110 | 2024-02-01 | 2024-03-01 | 743 | 76.9% |
| service_games | gbm_v1_service_games | 111 | 2024-03-01 | 2024-04-01 | 412 | 77.7% |
| service_games | gbm_v1_service_games | 112 | 2024-04-01 | 2024-05-01 | 642 | 82.9% |
| service_games | gbm_v1_service_games | 113 | 2024-05-01 | 2024-06-01 | 527 | 78.2% |
| service_games | gbm_v1_service_games | 114 | 2024-06-01 | 2024-07-01 | 329 | 86.3% |
| service_games | gbm_v1_service_games | 115 | 2024-07-01 | 2024-08-01 | 756 | 78.6% |
| service_games | gbm_v1_service_games | 116 | 2024-08-01 | 2024-09-01 | 601 | 76.2% |
| service_games | gbm_v1_service_games | 117 | 2024-09-01 | 2024-10-01 | 342 | 83.6% |
| service_games | gbm_v1_service_games | 118 | 2024-10-01 | 2024-11-01 | 568 | 81.9% |
| service_games | gbm_v1_service_games | 119 | 2024-11-01 | 2024-12-01 | 175 | 78.3% |
| service_games | gbm_v1_service_games | 120 | 2024-12-01 | 2025-01-01 | 69 | 65.2% |
| service_games | gbm_v1_service_games | 121 | 2025-01-01 | 2025-02-01 | 518 | 75.5% |
| service_games | gbm_v1_service_games | 122 | 2025-02-01 | 2025-03-01 | 563 | 77.3% |
| service_games | gbm_v1_service_games | 123 | 2025-03-01 | 2025-04-01 | 387 | 75.5% |
| service_games | gbm_v1_service_games | 124 | 2025-04-01 | 2025-05-01 | 570 | 77.5% |
| service_games | gbm_v1_service_games | 125 | 2025-05-01 | 2025-06-01 | 540 | 82.4% |
| service_games | gbm_v1_service_games | 126 | 2025-06-01 | 2025-07-01 | 455 | 78.7% |
| service_games | gbm_v1_service_games | 127 | 2025-07-01 | 2025-08-01 | 635 | 81.4% |
| service_games | gbm_v1_service_games | 128 | 2025-08-01 | 2025-09-01 | 531 | 74.8% |
| service_games | gbm_v1_service_games | 129 | 2025-09-01 | 2025-10-01 | 247 | 84.2% |
| service_games | gbm_v1_service_games | 130 | 2025-10-01 | 2025-11-01 | 570 | 79.1% |
| service_games | gbm_v1_service_games | 131 | 2025-11-01 | 2025-12-01 | 134 | 77.6% |
| service_games | gbm_v1_service_games | 132 | 2025-12-01 | 2026-01-01 | 27 | 29.6% |
| service_games | gbm_v1_service_games | 133 | 2026-01-01 | 2026-02-01 | 217 | 57.1% |
| service_games | gbm_v1_service_games | 134 | 2026-02-01 | 2026-03-01 | 1002 | 73.3% |
| service_games | gbm_v1_service_games | 135 | 2026-03-01 | 2026-04-01 | 1362 | 75.9% |
| service_games | gbm_v1_service_games | 136 | 2026-04-01 | 2026-05-01 | 1857 | 80.4% |
| service_games | gbm_v1_service_games | 137 | 2026-05-01 | 2026-06-01 | 1544 | 78.6% |
| service_games | gbm_v1_service_games | 138 | 2026-06-01 | 2026-07-01 | 1541 | 77.9% |
| service_games | gbm_v1_service_games | 139 | 2026-07-01 | 2026-08-01 | 1862 | 76.3% |
| service_games | gbm_v1_service_games | 140 | 2026-08-01 | 2026-09-01 | 1604 | 82.0% |
| service_games | gbm_v1_service_games | 141 | 2026-09-01 | 2026-10-01 | 1088 | 76.1% |

## Pooled calibration by prediction bin

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

## OOF objective comparison

| Target | OOF objective | Pooled ensemble MAE |
|---|---|---:|
| aces | absolute error | unavailable |
| aces | squared error | unavailable |
| double_faults | absolute error | unavailable |
| double_faults | squared error | unavailable |
| service_games | absolute error | unavailable |
| service_games | squared error | unavailable |

Coverage near 80% means the nominal 0.1–0.9 interval contains outcomes about eight times in ten. Higher coverage usually means intervals are too wide; lower coverage means they are too narrow.

## Fold-level bias-sign review

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

## Market comparison

Market comparison sample: 0 paired prediction/line/result rows.

- Prediction/line pairs before requiring a known result: 0.
- Pairs with a completed match and known target result: 0.
- Providers in the paired sample: none.
- No hit rate or ROI is reported because this sample is not informative.

## Data coverage

- Feature pipeline: ATP men only (`players.tour = 'ATP'`).
- Captured odds archive: 100% WTA.
- Captured markets: Sets Won, Games Won, and Break Points Won.
- Active model targets: aces, double faults, and service games.
- The current model/market intersection is empty; this is a data-domain mismatch, not a capture-start-date explanation.

## Reproducibility and boundaries

- Each model was scored on the same test rows within each monthly fold.
- Training rows were restricted to event dates strictly before the fold cutoff.
- Ensemble weights were fit only from earlier scored folds.
- Fold-level metrics and calibration rows are in [model-card-tennis-v1-appendix.csv](model-card-tennis-v1-appendix.csv).
- Results are appended to `model_backtest_results`; prior runs are not overwritten.
