"""Strict walk-forward evaluation for versioned player-prop models."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from config._schema import validate_sport_config
from models.baseline import (
    BaselineSettings,
    _expand_feature_values,
    baseline_settings_for_target,
    compute_context_adjustments,
    insert_backtest_predictions,
    load_feature_rows,
)


DEFAULT_CONFIG = Path("config/tennis.yaml")
KEY_COLUMNS = ("player_id", "match_id")
METRICS = ("mae", "rmse", "mean_bias", "interval_coverage")
INTERVAL_DIAGNOSTICS = ("interval_crossing_count", "interval_repair_count")
IMPROVEMENT_METRIC = "mae_improvement_over_baseline"
CALIBRATION_BIN_COUNT = 10
OOF_OBJECTIVES = ("absolute", "squared")
FoldFitter = Callable[
    [pd.DataFrame, pd.DataFrame, BaselineSettings],
    pd.DataFrame,
]
OOFFitObserver = Callable[
    ["Fold", Mapping[str, pd.DataFrame], pd.DataFrame],
    None,
]


@dataclass(frozen=True)
class BacktestSettings:
    start_date: date
    end_date: date
    step_months: int


@dataclass(frozen=True)
class Fold:
    fold_number: int
    cutoff_date: date
    test_end_date: date
    training: pd.DataFrame
    test: pd.DataFrame


@dataclass(frozen=True)
class FoldScore:
    metrics: dict[str, float | None]
    row_counts: dict[str, int]
    scored: pd.DataFrame
    calibration_bins: tuple[dict[str, Any], ...] = ()


def load_raw_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return raw


def backtest_settings_for_config(
    raw_config: Mapping[str, Any],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    step_months: int | None = None,
) -> BacktestSettings:
    validated = validate_sport_config(dict(raw_config))
    configured = validated.backtest
    if configured is None:
        raise ValueError("No backtest configuration is defined")
    settings = BacktestSettings(
        start_date=start_date or configured.start_date,
        end_date=end_date or configured.end_date,
        step_months=step_months or configured.step_months,
    )
    if settings.end_date <= settings.start_date:
        raise ValueError("Backtest end_date must be after start_date")
    if settings.step_months < 1:
        raise ValueError("Backtest step_months must be positive")
    return settings


def _next_month(value: date, step_months: int) -> date:
    timestamp = pd.Timestamp(value) + pd.DateOffset(months=step_months)
    return timestamp.date()


def assert_future_cutoff(training: pd.DataFrame, cutoff_date: date) -> None:
    dates = pd.to_datetime(training["event_date"], errors="coerce")
    if dates.notna().any() and not (dates < pd.Timestamp(cutoff_date)).all():
        raise AssertionError(
            f"Training data contains an event on or after cutoff {cutoff_date}"
        )


def build_walk_forward_folds(
    frame: pd.DataFrame,
    settings: BacktestSettings,
) -> list[Fold]:
    """Create non-overlapping monthly test windows with strict prior training."""

    if "event_date" not in frame:
        raise ValueError("Backtest frame is missing event_date")
    working = frame.copy()
    working["event_date"] = pd.to_datetime(working["event_date"]).dt.date
    folds: list[Fold] = []
    cutoff = settings.start_date
    fold_number = 1
    while cutoff < settings.end_date:
        test_end = min(
            _next_month(cutoff, settings.step_months),
            settings.end_date,
        )
        training = working[
            (working["event_date"] < cutoff)
            & working["is_training_eligible"].fillna(False).astype(bool)
        ].copy()
        test = working[
            (working["event_date"] >= cutoff)
            & (working["event_date"] < test_end)
            & working["has_sufficient_history"].fillna(False).astype(bool)
            & working["target_value"].notna()
        ].copy()
        assert_future_cutoff(training, cutoff)
        folds.append(
            Fold(
                fold_number=fold_number,
                cutoff_date=cutoff,
                test_end_date=test_end,
                training=training,
                test=test,
            )
        )
        cutoff = test_end
        fold_number += 1
    return folds


def _prediction_frame(
    adjusted: pd.DataFrame,
    selection: pd.Series,
    settings: BaselineSettings,
) -> pd.DataFrame:
    candidates = adjusted.loc[selection].copy()
    base = pd.to_numeric(candidates[settings.base_column], errors="coerce")
    prediction = base * candidates["baseline_context_adjustment"]
    standard_deviation = pd.to_numeric(
        candidates[settings.standard_deviation_column],
        errors="coerce",
    )
    lower = (prediction - standard_deviation).clip(lower=0)
    upper = prediction + standard_deviation
    return pd.DataFrame(
        {
            "player_id": candidates["player_id"].to_numpy(),
            "match_id": candidates["match_id"].to_numpy(),
            "prediction": prediction.to_numpy(),
            "lowerci": lower.where(standard_deviation.notna()).to_numpy(),
            "upperci": upper.where(standard_deviation.notna()).to_numpy(),
            "modelversion": settings.modelversion,
        }
    )


def fit_baseline_fold(
    training: pd.DataFrame,
    test: pd.DataFrame,
    settings: BaselineSettings,
) -> pd.DataFrame:
    """Fit context ratios on training and predict only the following window."""

    if training.empty:
        raise ValueError(
            f"Fold ending {test['event_date'].min() if not test.empty else 'unknown'} "
            f"has no training rows for {settings.target}"
        )
    combined = pd.concat(
        [
            training.assign(_backtest_test_row=False),
            test.assign(_backtest_test_row=True),
        ],
        ignore_index=True,
    )
    combined.loc[combined["_backtest_test_row"], "is_training_eligible"] = False
    adjusted, _ = compute_context_adjustments(combined, settings)
    selection = (
        adjusted["_backtest_test_row"].fillna(False).astype(bool)
        & adjusted["has_sufficient_history"].fillna(False).astype(bool)
        & adjusted[settings.base_column].notna()
    )
    return _prediction_frame(adjusted, selection, settings)


def _key_set(frame: pd.DataFrame) -> set[tuple[object, object]]:
    return set(frame[list(KEY_COLUMNS)].itertuples(index=False, name=None))


def score_predictions(
    predictions: pd.DataFrame,
    baseline_predictions: pd.DataFrame,
    test_rows: pd.DataFrame,
) -> FoldScore:
    """Score a model and enforce identical test rows to the baseline."""

    expected = _key_set(test_rows)
    if _key_set(predictions) != expected:
        raise AssertionError("Model predictions do not cover the complete test row set")
    if _key_set(baseline_predictions) != expected:
        raise AssertionError("Baseline predictions do not cover the complete test row set")
    actual = test_rows[list(KEY_COLUMNS) + ["target_value"]]
    scored = predictions.merge(
        actual,
        on=list(KEY_COLUMNS),
        how="inner",
        validate="one_to_one",
    )
    baseline_scored = baseline_predictions.merge(
        actual,
        on=list(KEY_COLUMNS),
        how="inner",
        validate="one_to_one",
    )
    if len(scored) != len(test_rows) or len(baseline_scored) != len(test_rows):
        raise AssertionError("Prediction and actual row sets do not match exactly")

    interval_crossing_count = 0
    interval_repair_count = 0
    for frame_index, scored_frame in enumerate((scored, baseline_scored)):
        for column in (
            "prediction",
            "lowerci",
            "upperci",
            "target_value",
        ):
            scored_frame[column] = pd.to_numeric(
                scored_frame[column], errors="coerce"
            )
        interval_mask = scored_frame["lowerci"].notna() & scored_frame["upperci"].notna()
        crossing = interval_mask & (
            scored_frame["lowerci"] > scored_frame["upperci"]
        )
        repair = interval_mask & (
            crossing
            | (scored_frame["prediction"] < 0)
            | (scored_frame["lowerci"] < 0)
            | (scored_frame["lowerci"] > scored_frame["prediction"])
            | (scored_frame["upperci"] < scored_frame["prediction"])
        )
        if repair.any():
            scored_frame.loc[repair, "prediction"] = scored_frame.loc[
                repair, "prediction"
            ].clip(lower=0)
            repaired_values = scored_frame.loc[
                repair, ["lowerci", "prediction", "upperci"]
            ]
            scored_frame.loc[repair, "lowerci"] = repaired_values.min(axis=1).clip(
                lower=0
            )
            scored_frame.loc[repair, "upperci"] = repaired_values.max(axis=1).clip(
                lower=0
            )
        if frame_index == 0:
            interval_crossing_count = int(crossing.sum())
            interval_repair_count = int(repair.sum())
    errors = scored["prediction"] - scored["target_value"]
    mae = float(errors.abs().mean())
    rmse = float(np.sqrt((errors**2).mean()))
    mean_bias = float(errors.mean())
    interval_rows = scored[
        scored["lowerci"].notna() & scored["upperci"].notna()
    ]
    interval_coverage = None
    if not interval_rows.empty:
        interval_coverage = float(
            (
                (interval_rows["target_value"] >= interval_rows["lowerci"])
                & (interval_rows["target_value"] <= interval_rows["upperci"])
            ).mean()
        )
    baseline_errors = baseline_scored["prediction"] - baseline_scored["target_value"]
    baseline_mae = float(baseline_errors.abs().mean())
    if baseline_mae == 0:
        improvement = 0.0 if mae == 0 else None
    else:
        improvement = float((baseline_mae - mae) / baseline_mae * 100)
    calibration_bins = calibration_by_prediction_bin(scored)
    return FoldScore(
        metrics={
            "mae": mae,
            "rmse": rmse,
            "mean_bias": mean_bias,
            "interval_coverage": interval_coverage,
            "interval_crossing_count": float(interval_crossing_count),
            "interval_repair_count": float(interval_repair_count),
            IMPROVEMENT_METRIC: improvement,
        },
        row_counts={
            "mae": len(scored),
            "rmse": len(scored),
            "mean_bias": len(scored),
            "interval_coverage": len(interval_rows),
            "interval_crossing_count": len(interval_rows),
            "interval_repair_count": len(interval_rows),
            IMPROVEMENT_METRIC: len(scored),
        },
        scored=scored,
        calibration_bins=tuple(calibration_bins),
    )


def backtest_model_version(
    model_prefix: str,
    target: str,
    run_timestamp: datetime,
) -> str:
    """Return a run-specific version that cannot collide with a live version."""

    stamp = run_timestamp.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{model_prefix}_{target}_backtest_{stamp}"


def prepare_backtest_predictions(
    score: FoldScore,
    fold: Fold,
    *,
    sport: str,
    target: str,
    model_prefix: str,
    run_timestamp: datetime,
) -> pd.DataFrame:
    """Adapt one scored OOF fold for persistence with auditable provenance.

    The event-date join is deliberately performed against ``fold.test`` rather
    than the training frame. This makes it impossible for a caller to persist
    training rows as historical predictions without failing the exact test-set
    checks below.
    """

    if score.scored.empty:
        return pd.DataFrame(
            columns=[
                "player_id",
                "match_id",
                "sport",
                "prop_type",
                "prediction",
                "lowerci",
                "upperci",
                "modelversion",
                "predictiontimestamp",
                "fold_number",
                "fold_cutoff_date",
                "fold_test_end_date",
            ]
        )
    expected = _key_set(fold.test)
    actual = _key_set(score.scored)
    if actual != expected:
        raise AssertionError(
            "Cannot persist historical predictions outside the scored fold test set"
        )
    test_dates = fold.test[list(KEY_COLUMNS) + ["event_date"]].copy()
    enriched = score.scored.merge(
        test_dates,
        on=list(KEY_COLUMNS),
        how="inner",
        validate="one_to_one",
    )
    event_dates = pd.to_datetime(enriched["event_date"], errors="coerce").dt.date
    training_cutoff_date = fold.cutoff_date - timedelta(days=1)
    if event_dates.isna().any() or not (
        (event_dates > training_cutoff_date)
        & (event_dates < fold.test_end_date)
    ).all():
        raise AssertionError("Historical predictions contain rows outside fold test window")
    modelversion = backtest_model_version(model_prefix, target, run_timestamp)
    return pd.DataFrame(
        {
            "player_id": enriched["player_id"].to_numpy(),
            "match_id": enriched["match_id"].to_numpy(),
            "sport": sport,
            "prop_type": target,
            "prediction": enriched["prediction"].to_numpy(),
            "lowerci": enriched["lowerci"].to_numpy(),
            "upperci": enriched["upperci"].to_numpy(),
            "modelversion": modelversion,
            "predictiontimestamp": run_timestamp,
            "fold_number": fold.fold_number,
            "fold_cutoff_date": training_cutoff_date,
            "fold_test_end_date": fold.test_end_date,
        }
    )


def persist_backtest_predictions(
    connection: object,
    score: FoldScore,
    fold: Fold,
    *,
    sport: str,
    target: str,
    model_prefix: str,
    run_timestamp: datetime,
) -> int:
    """Persist only one scored OOF fold through the canonical prediction writer."""

    predictions = prepare_backtest_predictions(
        score,
        fold,
        sport=sport,
        target=target,
        model_prefix=model_prefix,
        run_timestamp=run_timestamp,
    )
    return insert_backtest_predictions(connection, predictions)


def calibration_by_prediction_bin(
    scored: pd.DataFrame,
    *,
    bin_count: int = CALIBRATION_BIN_COUNT,
) -> list[dict[str, Any]]:
    """Measure interval coverage in prediction-ranked decile bins.

    Ranking before binning keeps the bins populated even when a model emits many
    tied predictions. Bounds and actual outcomes are still evaluated on the
    original rows; the rank only determines which prediction bin a row belongs
    to.
    """

    interval_rows = scored[
        scored["lowerci"].notna()
        & scored["upperci"].notna()
        & scored["prediction"].notna()
        & scored["target_value"].notna()
    ].copy()
    if interval_rows.empty:
        return []
    count = min(bin_count, len(interval_rows))
    ranks = interval_rows["prediction"].rank(method="first")
    interval_rows["_prediction_bin"] = np.ceil(ranks * count / len(interval_rows)).astype(
        int
    )
    output: list[dict[str, Any]] = []
    for bin_number, group in interval_rows.groupby("_prediction_bin", sort=True):
        covered = (
            (group["target_value"] >= group["lowerci"])
            & (group["target_value"] <= group["upperci"])
        )
        output.append(
            {
                "bin_number": int(bin_number),
                "row_count": int(len(group)),
                "prediction_min": float(group["prediction"].min()),
                "prediction_max": float(group["prediction"].max()),
                "coverage": float(covered.mean()),
            }
        )
    return output


def _calibration_metric_rows(
    score: FoldScore,
    *,
    modelversion: str,
    sport: str,
    stat_target: str,
    fold_number: int,
    cutoff_date: date,
    test_end_date: date,
    run_timestamp: datetime,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in score.calibration_bins:
        rows.append(
            {
                "modelversion": modelversion,
                "sport": sport,
                "stat_target": stat_target,
                "fold_number": fold_number,
                "metric": f"prediction_bin_{item['bin_number']:02d}_coverage",
                "metric_value": item["coverage"],
                "cutoff_date": cutoff_date,
                "test_end_date": test_end_date,
                "row_count": item["row_count"],
                "run_timestamp": run_timestamp,
            }
        )
    return rows


def _all_metric_rows(
    score: FoldScore,
    *,
    modelversion: str,
    sport: str,
    stat_target: str,
    fold_number: int,
    cutoff_date: date,
    test_end_date: date,
    run_timestamp: datetime,
) -> list[dict[str, Any]]:
    return _metric_rows(
        score,
        modelversion=modelversion,
        sport=sport,
        stat_target=stat_target,
        fold_number=fold_number,
        cutoff_date=cutoff_date,
        test_end_date=test_end_date,
        run_timestamp=run_timestamp,
    ) + _calibration_metric_rows(
        score,
        modelversion=modelversion,
        sport=sport,
        stat_target=stat_target,
        fold_number=fold_number,
        cutoff_date=cutoff_date,
        test_end_date=test_end_date,
        run_timestamp=run_timestamp,
    )


def _bias_sign_summary(
    fold_scores: Sequence[tuple[Fold, FoldScore]],
) -> tuple[str, int, int, float]:
    positive = sum(
        score.metrics["mean_bias"] is not None
        and score.metrics["mean_bias"] > 0
        for _fold, score in fold_scores
    )
    negative = sum(
        score.metrics["mean_bias"] is not None
        and score.metrics["mean_bias"] < 0
        for _fold, score in fold_scores
    )
    total = positive + negative
    if not total:
        return "unavailable", 0, 0, 0.0
    if positive >= negative:
        return "positive", positive, negative, positive / total
    return "negative", positive, negative, negative / total


def accumulate_ensemble_fold_history(
    prior_predictions: Mapping[str, Sequence[pd.DataFrame]],
    prior_tests: Sequence[pd.DataFrame],
    *,
    fold_predictions: Mapping[str, pd.DataFrame],
    fold_test: pd.DataFrame,
) -> tuple[dict[str, list[pd.DataFrame]], list[pd.DataFrame]]:
    """Append one scored fold after its predictions have been evaluated.

    Returning new containers makes the boundary explicit: callers construct the
    OOF inputs for a fold from the prior result, score the fold, and only then
    call this helper with that fold's predictions and outcomes.
    """

    if set(prior_predictions) != set(fold_predictions):
        raise ValueError("Fold history members do not match ensemble members")
    accumulated_predictions = {
        modelversion: [*frames, fold_predictions[modelversion]]
        for modelversion, frames in prior_predictions.items()
    }
    accumulated_tests = [*prior_tests, fold_test]
    return accumulated_predictions, accumulated_tests


def build_ensemble_oof_inputs(
    prior_predictions: Mapping[str, Sequence[pd.DataFrame]],
    prior_tests: Sequence[pd.DataFrame],
    *,
    current_predictions: Mapping[str, pd.DataFrame],
    current_test: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Build OOF fitting inputs without including the fold being scored."""

    del current_predictions, current_test
    if not prior_tests:
        return (
            {
                modelversion: pd.DataFrame()
                for modelversion in prior_predictions
            },
            pd.DataFrame(),
        )
    return (
        {
            modelversion: pd.concat(frames, ignore_index=True)
            for modelversion, frames in prior_predictions.items()
        },
        pd.concat(prior_tests, ignore_index=True),
    )


def _print_calibration_explanation() -> None:
    print(
        "Calibration interpretation: coverage near 80% means the nominal "
        "[lowerci, upperci] intervals contain outcomes about eight times in ten. "
        "Coverage far above 80% usually means intervals are too wide or too "
        "conservative; coverage far below 80% means they are too narrow and "
        "understate uncertainty."
    )


def shuffled_target_sabotage(
    training: pd.DataFrame,
    test: pd.DataFrame,
    settings: BaselineSettings,
    *,
    random_state: int = 20250917,
) -> tuple[float, float]:
    """Return ordinary and shuffled-target MAE for the baseline fit."""

    ordinary = fit_baseline_fold(training, test, settings)
    shuffled_training = training.copy()
    values = shuffled_training["target_value"].to_numpy(copy=True)
    np.random.default_rng(random_state).shuffle(values)
    shuffled_training["target_value"] = values
    shuffled = fit_baseline_fold(shuffled_training, test, settings)
    ordinary_score = score_predictions(ordinary, ordinary, test)
    shuffled_score = score_predictions(shuffled, ordinary, test)
    return (
        float(ordinary_score.metrics["mae"]),
        float(shuffled_score.metrics["mae"]),
    )


def _metric_rows(
    score: FoldScore,
    *,
    modelversion: str,
    sport: str,
    stat_target: str,
    fold_number: int,
    cutoff_date: date,
    test_end_date: date,
    run_timestamp: datetime,
) -> list[dict[str, Any]]:
    return [
        {
            "modelversion": modelversion,
            "sport": sport,
            "stat_target": stat_target,
            "fold_number": fold_number,
            "metric": metric,
            "metric_value": score.metrics[metric],
            "cutoff_date": cutoff_date,
            "test_end_date": test_end_date,
            "row_count": score.row_counts[metric],
            "run_timestamp": run_timestamp,
        }
        for metric in (*METRICS, *INTERVAL_DIAGNOSTICS, IMPROVEMENT_METRIC)
    ]


def _ensemble_objective_rows(
    *,
    score: FoldScore,
    weights: Mapping[str, float],
    objective: str,
    modelversion: str,
    sport: str,
    stat_target: str,
    fold_number: int,
    cutoff_date: date,
    test_end_date: date,
    run_timestamp: datetime,
    include_weights: bool = True,
) -> list[dict[str, Any]]:
    rows = [
        {
            "modelversion": modelversion,
            "sport": sport,
            "stat_target": stat_target,
            "fold_number": fold_number,
            "metric": f"mae_{objective}_objective",
            "metric_value": score.metrics["mae"],
            "cutoff_date": cutoff_date,
            "test_end_date": test_end_date,
            "row_count": score.row_counts["mae"],
            "run_timestamp": run_timestamp,
        }
    ]
    if include_weights:
        rows.extend(
            {
                "modelversion": modelversion,
                "sport": sport,
                "stat_target": stat_target,
                "fold_number": fold_number,
                "metric": f"weight_{objective}_{member}",
                "metric_value": float(weight),
                "cutoff_date": cutoff_date,
                "test_end_date": test_end_date,
                "row_count": score.row_counts["mae"],
                "run_timestamp": run_timestamp,
            }
            for member, weight in weights.items()
        )
    return rows


def store_backtest_results(connection: object, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    from sqlalchemy import text

    connection.execute(
        text(
            """
            INSERT INTO model_backtest_results (
                modelversion,
                sport,
                stat_target,
                fold_number,
                metric,
                metric_value,
                cutoff_date,
                test_end_date,
                row_count,
                run_timestamp
            )
            VALUES (
                :modelversion,
                :sport,
                :stat_target,
                :fold_number,
                :metric,
                :metric_value,
                :cutoff_date,
                :test_end_date,
                :row_count,
                :run_timestamp
            )
            """
        ),
        rows,
    )
    return len(rows)


def _print_target_report(
    *,
    target: str,
    modelversion: str,
    settings: BacktestSettings,
    fold_scores: list[tuple[Fold, FoldScore]],
    pooled: FoldScore | None,
    dry_run: bool,
    written: int,
    fold_detail: bool,
) -> None:
    print(f"\nBacktest report: {target}")
    print(
        f"{modelversion} evaluated from {settings.start_date} through "
        f"{settings.end_date} across {len(fold_scores)} folds."
    )
    if fold_detail:
        for fold, score in fold_scores:
            coverage = score.metrics["interval_coverage"]
            coverage_text = "unavailable" if coverage is None else f"{coverage:.1%}"
            print(
                f"  fold {fold.fold_number} ({fold.cutoff_date} to "
                f"{fold.test_end_date}): rows={score.row_counts['mae']} "
                f"MAE={score.metrics['mae']:.4f} "
                f"RMSE={score.metrics['rmse']:.4f} "
                f"bias={score.metrics['mean_bias']:.4f} "
                f"coverage={coverage_text} "
                f"interval crossings={int(score.metrics['interval_crossing_count'] or 0)} "
                f"repairs={int(score.metrics['interval_repair_count'] or 0)}"
            )
            if score.calibration_bins:
                print(
                    "    prediction-bin coverage: "
                    + ", ".join(
                        f"{item['bin_number']}={item['coverage']:.1%}"
                        for item in score.calibration_bins
                    )
                )
    if pooled is None:
        print("No rows were available to score.")
        return
    coverage = pooled.metrics["interval_coverage"]
    coverage_text = "unavailable" if coverage is None else f"{coverage:.1%}"
    improvement = pooled.metrics[IMPROVEMENT_METRIC]
    improvement_text = (
        "unavailable" if improvement is None else f"{improvement:.2f}%"
    )
    print(
        f"In plain language: {modelversion} averaged "
        f"{pooled.metrics['mae']:.4f} absolute error across "
        f"{pooled.row_counts['mae']} scored rows; its RMSE was "
        f"{pooled.metrics['rmse']:.4f}, signed bias was "
        f"{pooled.metrics['mean_bias']:.4f}, interval coverage was "
        f"{coverage_text}, and MAE improvement over baseline_v1 was "
        f"{improvement_text}. Interval diagnostics recorded "
        f"{int(pooled.metrics['interval_crossing_count'] or 0)} crossings and "
        f"{int(pooled.metrics['interval_repair_count'] or 0)} repaired rows."
    )
    sign, positive, negative, share = _bias_sign_summary(fold_scores)
    if sign == "unavailable":
        print("Bias sign by fold: unavailable.")
    elif share >= 0.6:
        print(
            f"BIAS FLAG: {sign} mean bias in {max(positive, negative)}/"
            f"{positive + negative} scored folds ({share:.1%}); "
            "this indicates a systematic directional error."
        )
    else:
        print(
            f"Bias sign by fold: mixed ({positive} positive, {negative} negative)."
        )
    _print_calibration_explanation()
    print(
        f"Backtest rows {'computed' if dry_run else 'written'}: "
        f"{written}"
    )


def run_backtest(
    config_path: Path = DEFAULT_CONFIG,
    *,
    targets: Sequence[str] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    step_months: int | None = None,
    dry_run: bool = False,
    model_version_prefix: str = "baseline_v1",
    fold_fitter: FoldFitter | None = None,
    fold_detail: bool = False,
    persist_predictions: bool = False,
) -> list[dict[str, Any]]:
    raw_config = load_raw_config(config_path)
    validated = validate_sport_config(raw_config)
    settings = backtest_settings_for_config(
        raw_config,
        start_date=start_date,
        end_date=end_date,
        step_months=step_months,
    )
    requested_targets = list(targets or validated.stat_targets)
    unknown = sorted(set(requested_targets) - set(validated.stat_targets))
    if unknown:
        raise ValueError(f"Unknown backtest target(s): {', '.join(unknown)}")
    fitter = fold_fitter or fit_baseline_fold

    run_timestamp = datetime.now(timezone.utc)
    all_rows: list[dict[str, Any]] = []
    from db.connection import create_db_engine

    engine = create_db_engine()
    try:
        with engine.begin() as connection:
            for target in requested_targets:
                baseline_settings = baseline_settings_for_target(
                    raw_config, target
                )
                frame = _expand_feature_values(
                    load_feature_rows(
                        connection,
                        sport=validated.sport,
                        feature_version=baseline_settings.feature_version,
                        target=target,
                    )
                )
                folds = build_walk_forward_folds(frame, settings)
                fold_scores: list[tuple[Fold, FoldScore]] = []
                target_rows: list[dict[str, Any]] = []
                pooled_predictions: list[pd.DataFrame] = []
                pooled_baselines: list[pd.DataFrame] = []
                pooled_tests: list[pd.DataFrame] = []
                for fold in folds:
                    if fold.test.empty:
                        continue
                    if fold.training.empty:
                        if fold_detail:
                            print(
                                f"  fold {fold.fold_number} ({fold.cutoff_date} to "
                                f"{fold.test_end_date}) skipped: no strictly earlier "
                                "training rows."
                            )
                        continue
                    predictions = fitter(
                        fold.training,
                        fold.test,
                        baseline_settings,
                    )
                    baseline_predictions = fit_baseline_fold(
                        fold.training,
                        fold.test,
                        baseline_settings,
                    )
                    score = score_predictions(
                        predictions,
                        baseline_predictions,
                        fold.test,
                    )
                    fold_scores.append((fold, score))
                    if persist_predictions and not dry_run:
                        persist_backtest_predictions(
                            connection,
                            score,
                            fold,
                            sport=validated.sport,
                            target=target,
                            model_prefix=model_version_prefix,
                            run_timestamp=run_timestamp,
                        )
                    target_rows.extend(
                        _all_metric_rows(
                            score,
                            modelversion=f"{model_version_prefix}_{target}",
                            sport=validated.sport,
                            stat_target=target,
                            fold_number=fold.fold_number,
                            cutoff_date=fold.cutoff_date,
                            test_end_date=fold.test_end_date,
                            run_timestamp=run_timestamp,
                        )
                    )
                    pooled_predictions.append(predictions)
                    pooled_baselines.append(baseline_predictions)
                    pooled_tests.append(fold.test)
                pooled = None
                if pooled_tests:
                    pooled_predictions_frame = pd.concat(
                        pooled_predictions, ignore_index=True
                    )
                    pooled_baselines_frame = pd.concat(
                        pooled_baselines, ignore_index=True
                    )
                    pooled_test_frame = pd.concat(pooled_tests, ignore_index=True)
                    pooled = score_predictions(
                        pooled_predictions_frame,
                        pooled_baselines_frame,
                        pooled_test_frame,
                    )
                    target_rows.extend(
                        _all_metric_rows(
                            pooled,
                            modelversion=f"{model_version_prefix}_{target}",
                            sport=validated.sport,
                            stat_target=target,
                            fold_number=0,
                            cutoff_date=settings.end_date,
                            test_end_date=settings.end_date,
                            run_timestamp=run_timestamp,
                        )
                    )
                written = (
                    store_backtest_results(connection, target_rows)
                    if not dry_run
                    else 0
                )
                all_rows.extend(target_rows)
                _print_target_report(
                    target=target,
                    modelversion=f"{model_version_prefix}_{target}",
                    settings=settings,
                    fold_scores=fold_scores,
                    pooled=pooled,
                    dry_run=dry_run,
                    written=len(target_rows) if dry_run else written,
                    fold_detail=fold_detail,
                )
    finally:
        engine.dispose()
    return all_rows


def run_ensemble_backtest(
    config_path: Path = DEFAULT_CONFIG,
    *,
    targets: Sequence[str] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    step_months: int | None = None,
    dry_run: bool = False,
    fold_detail: bool = False,
    persist_predictions: bool = False,
    oof_fit_observer: OOFFitObserver | None = None,
) -> list[dict[str, Any]]:
    """Score baseline, GBM, and ensemble on identical walk-forward rows."""

    raw_config = load_raw_config(config_path)
    validated = validate_sport_config(raw_config)
    if validated.gbm is None:
        raise ValueError("Ensemble backtest requires gbm configuration")
    if validated.ensemble is None:
        raise ValueError("Ensemble backtest requires ensemble configuration")
    settings = backtest_settings_for_config(
        raw_config,
        start_date=start_date,
        end_date=end_date,
        step_months=step_months,
    )
    requested_targets = list(targets or validated.stat_targets)
    unknown = sorted(set(requested_targets) - set(validated.stat_targets))
    if unknown:
        raise ValueError(f"Unknown backtest target(s): {', '.join(unknown)}")

    from db.connection import create_db_engine
    from models.ensemble import (
        combine_predictions,
        ensemble_settings_for_target,
        fit_oof_weights,
    )
    from models.gbm import fit_gbm_fold, gbm_settings_for_target

    run_timestamp = datetime.now(timezone.utc)
    all_rows: list[dict[str, Any]] = []
    engine = create_db_engine()
    try:
        with engine.begin() as connection:
            for target in requested_targets:
                baseline_settings = baseline_settings_for_target(
                    raw_config, target
                )
                ensemble_settings = ensemble_settings_for_target(raw_config, target)
                gbm_settings = gbm_settings_for_target(raw_config, target)
                frame = _expand_feature_values(
                    load_feature_rows(
                        connection,
                        sport=validated.sport,
                        feature_version=baseline_settings.feature_version,
                        target=target,
                    )
                )
                folds = build_walk_forward_folds(frame, settings)
                member_versions = [
                    member.modelversion for member in ensemble_settings.members
                ]
                prior_predictions: dict[str, list[pd.DataFrame]] = {
                    modelversion: [] for modelversion in member_versions
                }
                prior_tests: list[pd.DataFrame] = []
                target_rows: list[dict[str, Any]] = []
                fold_reports: list[
                    tuple[
                        Fold,
                        FoldScore,
                        FoldScore,
                        FoldScore,
                        dict[str, float],
                        str,
                        int,
                        int,
                        int,
                    ]
                ] = []
                fold_objective_reports: dict[
                    int, dict[str, tuple[dict[str, float], FoldScore, str]]
                ] = {}
                pooled_baselines: list[pd.DataFrame] = []
                pooled_gbm: list[pd.DataFrame] = []
                pooled_ensemble: list[pd.DataFrame] = []
                pooled_objective_predictions: dict[str, list[pd.DataFrame]] = {
                    objective: [] for objective in OOF_OBJECTIVES
                }
                pooled_tests: list[pd.DataFrame] = []

                for fold in folds:
                    if fold.test.empty:
                        continue
                    if fold.training.empty:
                        if fold_detail:
                            print(
                                f"  fold {fold.fold_number} ({fold.cutoff_date} to "
                                f"{fold.test_end_date}) skipped: no strictly earlier "
                                "training rows."
                            )
                        continue
                    baseline_predictions = fit_baseline_fold(
                        fold.training,
                        fold.test,
                        baseline_settings,
                    )
                    gbm_predictions = fit_gbm_fold(
                        fold.training,
                        fold.test,
                        gbm_settings,
                    )
                    available_member_predictions = {
                        f"baseline_v1_{target}": baseline_predictions,
                        f"gbm_v1_{target}": gbm_predictions,
                    }
                    member_predictions = {
                        member.modelversion: available_member_predictions[
                            member.modelversion
                        ]
                        for member in ensemble_settings.members
                    }
                    if prior_tests:
                        earlier_predictions, earlier_actuals = (
                            build_ensemble_oof_inputs(
                                prior_predictions,
                                prior_tests,
                                current_predictions=member_predictions,
                                current_test=fold.test,
                            )
                        )
                        weight_source = (
                            f"OOF rows from {len(prior_tests)} earlier scored folds; "
                            f"none from fold {fold.fold_number}"
                        )
                    else:
                        earlier_predictions = {}
                        earlier_actuals = pd.DataFrame()
                        weight_source = (
                            "configured static weights because fold "
                            f"{fold.fold_number} has no earlier scored folds"
                        )
                    if oof_fit_observer is not None:
                        oof_fit_observer(
                            fold,
                            earlier_predictions,
                            earlier_actuals,
                        )
                    objective_reports: dict[
                        str, tuple[dict[str, float], FoldScore, str]
                    ] = {}
                    objective_prediction_frames: dict[str, pd.DataFrame] = {}
                    for objective in OOF_OBJECTIVES:
                        if prior_tests:
                            objective_weights = fit_oof_weights(
                                earlier_predictions,
                                earlier_actuals,
                                ensemble_settings,
                                objective=objective,
                            )
                        else:
                            objective_weights = ensemble_settings.configured_weights
                        objective_source = (
                            f"{weight_source}; objective={objective}"
                        )
                        objective_result = combine_predictions(
                            member_predictions,
                            ensemble_settings,
                            weights=objective_weights,
                            weight_source=objective_source,
                            predictiontimestamp=run_timestamp,
                        )
                        objective_score = score_predictions(
                            objective_result.predictions,
                            baseline_predictions,
                            fold.test,
                        )
                        objective_reports[objective] = (
                            objective_weights,
                            objective_score,
                            objective_source,
                        )
                        objective_prediction_frames[objective] = (
                            objective_result.predictions
                        )
                    fold_objective_reports[fold.fold_number] = objective_reports
                    weights, _configured_score, _configured_source = (
                        objective_reports[ensemble_settings.oof_objective]
                    )
                    ensemble_result = combine_predictions(
                        member_predictions,
                        ensemble_settings,
                        weights=weights,
                        weight_source=_configured_source,
                        predictiontimestamp=run_timestamp,
                    )
                    baseline_score = score_predictions(
                        baseline_predictions,
                        baseline_predictions,
                        fold.test,
                    )
                    gbm_score = score_predictions(
                        gbm_predictions,
                        baseline_predictions,
                        fold.test,
                    )
                    ensemble_score = score_predictions(
                        ensemble_result.predictions,
                        baseline_predictions,
                        fold.test,
                    )
                    scores = (
                        ("baseline_v1", baseline_score),
                        ("gbm_v1", gbm_score),
                        ("ensemble_v1", ensemble_score),
                    )
                    if persist_predictions and not dry_run:
                        for model_prefix, score in scores:
                            persist_backtest_predictions(
                                connection,
                                score,
                                fold,
                                sport=validated.sport,
                                target=target,
                                model_prefix=model_prefix,
                                run_timestamp=run_timestamp,
                            )
                    for model_prefix, score in scores:
                        target_rows.extend(
                            _all_metric_rows(
                                score,
                                modelversion=f"{model_prefix}_{target}",
                                sport=validated.sport,
                                stat_target=target,
                                fold_number=fold.fold_number,
                                cutoff_date=fold.cutoff_date,
                                test_end_date=fold.test_end_date,
                                run_timestamp=run_timestamp,
                            )
                        )
                    for objective, (
                        objective_weights,
                        objective_score,
                        _objective_source,
                    ) in objective_reports.items():
                        target_rows.extend(
                            _ensemble_objective_rows(
                                score=objective_score,
                                weights=objective_weights,
                                objective=objective,
                                modelversion=f"ensemble_v1_{target}",
                                sport=validated.sport,
                                stat_target=target,
                                fold_number=fold.fold_number,
                                cutoff_date=fold.cutoff_date,
                                test_end_date=fold.test_end_date,
                                run_timestamp=run_timestamp,
                            )
                        )
                    fold_reports.append(
                        (
                            fold,
                            baseline_score,
                            gbm_score,
                            ensemble_score,
                            weights,
                            weight_source,
                            ensemble_result.complete_rows,
                            ensemble_result.renormalized_rows,
                            ensemble_result.skipped_rows,
                        )
                    )
                    pooled_baselines.append(baseline_predictions)
                    pooled_gbm.append(gbm_predictions)
                    pooled_ensemble.append(ensemble_result.predictions)
                    for objective, predictions in objective_prediction_frames.items():
                        pooled_objective_predictions[objective].append(predictions)
                    pooled_tests.append(fold.test)
                    prior_predictions, prior_tests = accumulate_ensemble_fold_history(
                        prior_predictions,
                        prior_tests,
                        fold_predictions=member_predictions,
                        fold_test=fold.test,
                    )

                pooled_scores: tuple[FoldScore, FoldScore, FoldScore] | None = None
                if pooled_tests:
                    pooled_test = pd.concat(pooled_tests, ignore_index=True)
                    pooled_baseline = pd.concat(pooled_baselines, ignore_index=True)
                    pooled_gbm_frame = pd.concat(pooled_gbm, ignore_index=True)
                    pooled_ensemble_frame = pd.concat(
                        pooled_ensemble,
                        ignore_index=True,
                    )
                    pooled_scores = (
                        score_predictions(pooled_baseline, pooled_baseline, pooled_test),
                        score_predictions(pooled_gbm_frame, pooled_baseline, pooled_test),
                        score_predictions(
                            pooled_ensemble_frame,
                            pooled_baseline,
                            pooled_test,
                        ),
                    )
                    for model_prefix, score in zip(
                        ("baseline_v1", "gbm_v1", "ensemble_v1"),
                        pooled_scores,
                        strict=True,
                    ):
                        target_rows.extend(
                            _all_metric_rows(
                                score,
                                modelversion=f"{model_prefix}_{target}",
                                sport=validated.sport,
                                stat_target=target,
                                fold_number=0,
                                cutoff_date=settings.end_date,
                                test_end_date=settings.end_date,
                                run_timestamp=run_timestamp,
                            )
                        )
                    for objective in OOF_OBJECTIVES:
                        objective_frame = pd.concat(
                            pooled_objective_predictions[objective],
                            ignore_index=True,
                        )
                        objective_score = score_predictions(
                            objective_frame,
                            pooled_baseline,
                            pooled_test,
                        )
                        target_rows.extend(
                            _ensemble_objective_rows(
                                score=objective_score,
                                weights={},
                                objective=objective,
                                modelversion=f"ensemble_v1_{target}",
                                sport=validated.sport,
                                stat_target=target,
                                fold_number=0,
                                cutoff_date=settings.end_date,
                                test_end_date=settings.end_date,
                                run_timestamp=run_timestamp,
                                include_weights=False,
                            )
                        )

                written = (
                    store_backtest_results(connection, target_rows)
                    if not dry_run
                    else 0
                )
                all_rows.extend(target_rows)
                print(f"\nEnsemble backtest report: {target}")
                print(
                    "Each fold uses the baseline, GBM, and ensemble on the "
                    "identical test rows."
                )
                if fold_detail:
                    for (
                        fold,
                        baseline_score,
                        gbm_score,
                        ensemble_score,
                        weights,
                        weight_source,
                        complete_rows,
                        renormalized_rows,
                        skipped_rows,
                    ) in fold_reports:
                        baseline_mae = baseline_score.metrics["mae"]
                        gbm_mae = gbm_score.metrics["mae"]
                        ensemble_mae = ensemble_score.metrics["mae"]
                        print(
                            f"  fold {fold.fold_number} ({fold.cutoff_date} to "
                            f"{fold.test_end_date}): rows={baseline_score.row_counts['mae']} "
                            f"baseline MAE={baseline_mae:.4f}, "
                            f"GBM MAE={gbm_mae:.4f}, "
                            f"ensemble MAE={ensemble_mae:.4f}, "
                            f"ensemble improvement vs baseline="
                            f"{ensemble_score.metrics[IMPROVEMENT_METRIC]:.2f}%, "
                            f"vs GBM={((gbm_mae - ensemble_mae) / gbm_mae * 100) if gbm_mae else 0.0:.2f}%"
                        )
                        print(
                            "    fold coverage: "
                            + ", ".join(
                                f"{model}={score.metrics['interval_coverage']:.1%}"
                                if score.metrics["interval_coverage"] is not None
                                else f"{model}=unavailable"
                                for model, score in (
                                    ("baseline", baseline_score),
                                    ("GBM", gbm_score),
                                    ("ensemble", ensemble_score),
                                )
                            )
                        )
                        print(
                            "    weights: "
                            + ", ".join(
                                f"{modelversion}={weight:.4f}"
                                for modelversion, weight in weights.items()
                            )
                        )
                        for objective, (
                            objective_weights,
                            objective_score,
                            objective_source,
                        ) in fold_objective_reports[fold.fold_number].items():
                            print(
                                f"    objective={objective}: "
                                f"ensemble MAE={objective_score.metrics['mae']:.4f}; "
                                + ", ".join(
                                    f"{modelversion}={weight:.4f}"
                                    for modelversion, weight in objective_weights.items()
                                )
                            )
                            print(f"      weight rows: {objective_source}")
                        print(f"    weight rows: {weight_source}")
                        print(
                            "    member coverage: "
                            f"complete={complete_rows}, "
                            f"renormalized={renormalized_rows}, "
                            f"skipped={skipped_rows}"
                        )
                if pooled_scores is not None:
                    baseline_score, gbm_score, ensemble_score = pooled_scores
                    baseline_mae = baseline_score.metrics["mae"]
                    gbm_mae = gbm_score.metrics["mae"]
                    ensemble_mae = ensemble_score.metrics["mae"]
                    print(
                        f"Pooled MAE: baseline={baseline_mae:.4f}, "
                        f"GBM={gbm_mae:.4f}, ensemble={ensemble_mae:.4f}; "
                        f"ensemble improvement vs baseline="
                        f"{ensemble_score.metrics[IMPROVEMENT_METRIC]:.2f}%, "
                        f"vs GBM={((gbm_mae - ensemble_mae) / gbm_mae * 100) if gbm_mae else 0.0:.2f}%"
                    )
                    for model, score in (
                        ("baseline", baseline_score),
                        ("GBM", gbm_score),
                        ("ensemble", ensemble_score),
                    ):
                        coverage = score.metrics["interval_coverage"]
                        print(
                            f"  pooled {model} interval coverage: "
                            + (
                                "unavailable"
                                if coverage is None
                                else f"{coverage:.1%}"
                            )
                        )
                        if score.calibration_bins:
                            print(
                                f"  pooled {model} prediction-bin coverage: "
                                + ", ".join(
                                    f"{item['bin_number']}={item['coverage']:.1%}"
                                    for item in score.calibration_bins
                                )
                            )
                    for model, scores in (
                        (
                            "baseline",
                            [(fold, score) for fold, score, _gbm, _ens, *_ in fold_reports],
                        ),
                        (
                            "GBM",
                            [(fold, score) for fold, _base, score, _ens, *_ in fold_reports],
                        ),
                        (
                            "ensemble",
                            [(fold, score) for fold, _base, _gbm, score, *_ in fold_reports],
                        ),
                    ):
                        sign, positive, negative, share = _bias_sign_summary(scores)
                        if sign != "unavailable" and share >= 0.6:
                            print(
                                f"  BIAS FLAG {model}: {sign} in "
                                f"{max(positive, negative)}/{positive + negative} folds "
                                f"({share:.1%})."
                            )
                    _print_calibration_explanation()
                print(
                    f"Backtest rows {'computed' if dry_run else 'written'}: "
                    f"{len(target_rows) if dry_run else written}"
                )
    finally:
        engine.dispose()
    return all_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--target", action="append", dest="targets")
    parser.add_argument(
        "--model",
        choices=("baseline", "gbm", "ensemble", "all"),
        default="baseline",
        help="Run one model or the ensemble report; all scores baseline, GBM, and ensemble together.",
    )
    parser.add_argument("--start-date", type=date.fromisoformat)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument("--step-months", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--persist-predictions",
        action="store_true",
        help="Persist run-specific scored OOF predictions with fold provenance.",
    )
    parser.add_argument(
        "--fold-detail",
        action="store_true",
        help="Print per-fold metrics, coverage, bins, and bias diagnostics.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = {
        "targets": args.targets,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "step_months": args.step_months,
        "dry_run": args.dry_run,
        "fold_detail": args.fold_detail,
        "persist_predictions": args.persist_predictions,
    }
    if args.model in {"ensemble", "all"}:
        run_ensemble_backtest(args.config, **options)
    elif args.model == "gbm":
        from models.gbm import fit_gbm_fold, gbm_settings_for_target

        raw_config = load_raw_config(args.config)

        requested = args.targets or validate_sport_config(raw_config).stat_targets
        for target in requested:
            run_backtest(
                args.config,
                targets=[target],
                start_date=args.start_date,
                end_date=args.end_date,
                step_months=args.step_months,
                dry_run=args.dry_run,
                model_version_prefix="gbm_v1",
                fold_fitter=lambda training, test, baseline_settings, target_name=target: fit_gbm_fold(
                    training,
                    test,
                    gbm_settings_for_target(raw_config, target_name),
                ),
            )
    else:
        run_backtest(args.config, **options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())