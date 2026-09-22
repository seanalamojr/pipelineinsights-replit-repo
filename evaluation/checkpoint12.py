"""Run Checkpoint 12 and write an auditable evaluation report and model card."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from config._schema import validate_sport_config
from evaluation.backtest import run_ensemble_backtest


DEFAULT_CONFIG = Path("config/tennis.yaml")
DEFAULT_MODEL_CARD = Path("docs/model-card-tennis-v1.md")
DEFAULT_REPORT = Path("backtest/reports/checkpoint12-latest.md")
POOLED_FOLD = 0
MODEL_PREFIXES = ("baseline_v1", "gbm_v1", "ensemble_v1")
METRICS = ("mae", "rmse", "mean_bias", "interval_coverage")


@dataclass(frozen=True)
class MarketComparison:
    prediction_line_pairs: int
    known_result_pairs: int
    paired_rows: int
    providers: tuple[str, ...]


def _format_metric(
    value: object,
    *,
    percent: bool = False,
    percentage_points: bool = False,
) -> str:
    if value is None:
        return "unavailable"
    number = float(value)
    if percentage_points:
        return f"{number:.2f}%"
    return f"{number:.1%}" if percent else f"{number:.4f}"


def _metric_lookup(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, int, str], Mapping[str, Any]]:
    return {
        (
            str(row["stat_target"]),
            str(row["modelversion"]),
            int(row["fold_number"]),
            str(row["metric"]),
        ): row
        for row in rows
    }


def load_market_comparison(connection: object) -> MarketComparison:
    """Count only non-demo, pre-match lines joined to known completed outcomes."""

    from sqlalchemy import text

    result = connection.execute(
        text(
            """
            WITH paired AS (
                SELECT DISTINCT
                    prediction.prediction_id,
                    market.provider,
                    market.book,
                    market.captured_at
                FROM player_prop_predictions AS prediction
                JOIN matches AS match_row
                  ON match_row.match_id = prediction.match_id
                 AND match_row.player_id = prediction.player_id
                JOIN odds AS market
                  ON market.match_id = prediction.match_id
                 AND market.player_id = prediction.player_id
                 AND market.prop_type = prediction.prop_type
                WHERE prediction.player_id NOT LIKE 'demo_%%'
                  AND market.provider <> 'demo'
                  AND market.line IS NOT NULL
                  AND market.captured_at::date <= match_row.event_date
            ),
            known AS (
                SELECT DISTINCT
                    prediction.prediction_id,
                    market.provider,
                    market.book,
                    market.captured_at
                FROM player_prop_predictions AS prediction
                JOIN matches AS match_row
                  ON match_row.match_id = prediction.match_id
                 AND match_row.player_id = prediction.player_id
                JOIN odds AS market
                  ON market.match_id = prediction.match_id
                 AND market.player_id = prediction.player_id
                 AND market.prop_type = prediction.prop_type
                WHERE prediction.player_id NOT LIKE 'demo_%%'
                  AND market.provider <> 'demo'
                  AND market.line IS NOT NULL
                  AND market.captured_at::date <= match_row.event_date
                  AND match_row.match_completed
                  AND CASE prediction.prop_type
                      WHEN 'aces' THEN match_row.aces IS NOT NULL
                      WHEN 'double_faults' THEN match_row.double_faults IS NOT NULL
                      WHEN 'service_games' THEN match_row.service_games IS NOT NULL
                      ELSE FALSE
                  END
            )
            SELECT
                (SELECT COUNT(*) FROM paired) AS prediction_line_pairs,
                (SELECT COUNT(*) FROM known) AS known_result_pairs,
                (SELECT COUNT(*) FROM known) AS paired_rows,
                COALESCE(
                    (SELECT ARRAY_AGG(DISTINCT provider ORDER BY provider) FROM known),
                    ARRAY[]::text[]
                ) AS providers
            """
        )
    ).mappings().one()
    return MarketComparison(
        prediction_line_pairs=int(result["prediction_line_pairs"]),
        known_result_pairs=int(result["known_result_pairs"]),
        paired_rows=int(result["paired_rows"]),
        providers=tuple(result["providers"] or ()),
    )


def _summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if int(row["fold_number"]) == POOLED_FOLD
        and str(row["metric"]) in (*METRICS, "mae_improvement_over_baseline")
    ]


def _summary_table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lookup = _metric_lookup(rows)
    lines = [
        "| Target | Model | MAE | RMSE | Signed bias | Coverage | Rows | Interval crossings | Interval repairs | MAE improvement vs baseline |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for target in sorted({str(row["stat_target"]) for row in rows}):
        for prefix in MODEL_PREFIXES:
            modelversion = f"{prefix}_{target}"
            get = lambda metric: lookup.get(
                (target, modelversion, POOLED_FOLD, metric)
            )
            mae = get("mae")
            lines.append(
                "| {target} | {model} | {mae} | {rmse} | {bias} | {coverage} | {count} | {crossings} | {repairs} | {improvement} |".format(
                    target=target,
                    model=modelversion,
                    mae=_format_metric(mae and mae["metric_value"]),
                    rmse=_format_metric(get("rmse") and get("rmse")["metric_value"]),
                    bias=_format_metric(get("mean_bias") and get("mean_bias")["metric_value"]),
                    coverage=_format_metric(
                        get("interval_coverage")
                        and get("interval_coverage")["metric_value"],
                        percent=True,
                    ),
                    count=mae["row_count"] if mae else "unavailable",
                    crossings=_format_metric(
                        get("interval_crossing_count")
                        and get("interval_crossing_count")["metric_value"],
                    ),
                    repairs=_format_metric(
                        get("interval_repair_count")
                        and get("interval_repair_count")["metric_value"],
                    ),
                    improvement=_format_metric(
                        get("mae_improvement_over_baseline")
                        and get("mae_improvement_over_baseline")["metric_value"],
                        percentage_points=True,
                    ),
                )
            )
    return lines


def _objective_table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lookup = _metric_lookup(rows)
    lines = [
        "| Target | OOF objective | Pooled ensemble MAE |",
        "|---|---|---:|",
    ]
    for target in sorted({str(row["stat_target"]) for row in rows}):
        for objective in ("absolute", "squared"):
            row = lookup.get(
                (
                    target,
                    f"ensemble_v1_{target}",
                    POOLED_FOLD,
                    f"mae_{objective}_objective",
                )
            )
            lines.append(
                f"| {target} | {objective} error | "
                f"{_format_metric(row['metric_value'] if row else None)} |"
            )
    return lines


def _weight_summary_table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    grouped: dict[tuple[str, str, str], list[float]] = {}
    for row in rows:
        metric = str(row["metric"])
        if not metric.startswith("weight_") or int(row["fold_number"]) <= POOLED_FOLD:
            continue
        parts = metric.split("_", 2)
        if len(parts) != 3:
            continue
        objective, member = parts[1:]
        key = (str(row["stat_target"]), objective, member)
        grouped.setdefault(key, []).append(float(row["metric_value"]))
    lines = [
        "| Target | OOF objective | Member | Folds | Mean weight | Range |",
        "|---|---|---|---:|---:|---:|",
    ]
    for (target, objective, member), values in sorted(grouped.items()):
        lines.append(
            f"| {target} | {objective} error | {member} | {len(values)} | "
            f"{sum(values) / len(values):.4f} | "
            f"{min(values):.4f}–{max(values):.4f} |"
        )
    if len(lines) == 2:
        lines.append("| unavailable | unavailable | unavailable | 0 | unavailable | unavailable |")
    return lines


def _write_fold_appendix(
    rows: Sequence[Mapping[str, Any]],
    *,
    path: Path,
) -> None:
    appendix_rows = [
        {
            str(key): value
            for key, value in row.items()
        }
        for row in rows
        if int(row["fold_number"]) > POOLED_FOLD
    ]
    fieldnames = sorted(
        {key for row in appendix_rows for key in row},
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not fieldnames:
            handle.write("")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in appendix_rows:
            writer.writerow(
                {
                    key: "" if row.get(key) is None else str(row.get(key))
                    for key in fieldnames
                }
            )


def _fold_coverage_table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| Target | Model | Fold | Cutoff | Test end | Rows | Coverage |",
        "|---|---|---:|---|---|---:|---:|",
    ]
    for row in sorted(
        (
            row
            for row in rows
            if str(row["metric"]) == "interval_coverage"
            and int(row["fold_number"]) > POOLED_FOLD
        ),
        key=lambda item: (
            str(item["stat_target"]),
            str(item["modelversion"]),
            int(item["fold_number"]),
        ),
    ):
        lines.append(
            "| {target} | {model} | {fold} | {cutoff} | {end} | {count} | {coverage} |".format(
                target=row["stat_target"],
                model=row["modelversion"],
                fold=row["fold_number"],
                cutoff=row["cutoff_date"],
                end=row["test_end_date"],
                count=row["row_count"],
                coverage=_format_metric(row["metric_value"], percent=True),
            )
        )
    return lines


def _bin_table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| Target | Model | Prediction bin | Rows | Coverage |",
        "|---|---|---:|---:|---:|",
    ]
    for row in sorted(
        (
            row
            for row in rows
            if int(row["fold_number"]) == POOLED_FOLD
            and str(row["metric"]).startswith("prediction_bin_")
        ),
        key=lambda item: (
            str(item["stat_target"]),
            str(item["modelversion"]),
            str(item["metric"]),
        ),
    ):
        lines.append(
            "| {target} | {model} | {bin} | {count} | {coverage} |".format(
                target=row["stat_target"],
                model=row["modelversion"],
                bin=str(row["metric"]).removeprefix("prediction_bin_").removesuffix(
                    "_coverage"
                ),
                count=row["row_count"],
                coverage=_format_metric(row["metric_value"], percent=True),
            )
        )
    return lines


def _bias_review(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| Target | Model | Positive folds | Negative folds | Dominant sign share | Review |",
        "|---|---|---:|---:|---:|---|",
    ]
    targets = sorted({str(row["stat_target"]) for row in rows})
    for target in targets:
        for prefix in MODEL_PREFIXES:
            modelversion = f"{prefix}_{target}"
            biases = [
                float(row["metric_value"])
                for row in rows
                if str(row["modelversion"]) == modelversion
                and str(row["metric"]) == "mean_bias"
                and int(row["fold_number"]) > POOLED_FOLD
                and row["metric_value"] is not None
            ]
            positive = sum(value > 0 for value in biases)
            negative = sum(value < 0 for value in biases)
            total = positive + negative
            if not total:
                lines.append(
                    f"| {target} | {modelversion} | 0 | 0 | unavailable | unavailable |"
                )
                continue
            dominant = max(positive, negative) / total
            sign = "positive" if positive >= negative else "negative"
            review = (
                f"FLAG: {sign} in most folds"
                if dominant >= 0.6
                else "mixed"
            )
            lines.append(
                f"| {target} | {modelversion} | {positive} | {negative} | "
                f"{dominant:.1%} | {review} |"
            )
    return lines


def _expectation_lines(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lookup = _metric_lookup(rows)
    lines: list[str] = []
    aces_mae = lookup.get(("aces", "baseline_v1_aces", 0, "mae"))
    baseline_aces = float(aces_mae["metric_value"]) if aces_mae else None
    baseline_pass = baseline_aces is not None and 3.4 <= baseline_aces <= 4.1
    lines.append(
        f"- Baseline aces MAE 3.4–4.1: **{'PASS' if baseline_pass else 'FAIL'}** "
        f"({_format_metric(baseline_aces)})."
    )
    for target in sorted({str(row["stat_target"]) for row in rows}):
        base = lookup.get((target, f"baseline_v1_{target}", 0, "mae"))
        gbm = lookup.get((target, f"gbm_v1_{target}", 0, "mae_improvement_over_baseline"))
        ens = lookup.get((target, f"ensemble_v1_{target}", 0, "mae"))
        gbm_improvement = float(gbm["metric_value"]) if gbm else None
        gbm_pass = gbm_improvement is not None and 3 <= gbm_improvement <= 8
        lines.append(
            f"- GBM {target} improvement 3–8%: **{'PASS' if gbm_pass else 'FAIL'}** "
        f"({_format_metric(gbm_improvement, percentage_points=True)})."
        )
        ensemble_vs_gbm = None
        if ens and base:
            gbm_mae_row = lookup.get((target, f"gbm_v1_{target}", 0, "mae"))
            if gbm_mae_row and float(gbm_mae_row["metric_value"]) != 0:
                ensemble_vs_gbm = (
                    float(gbm_mae_row["metric_value"])
                    - float(ens["metric_value"])
                ) / float(gbm_mae_row["metric_value"]) * 100
        ensemble_pass = ensemble_vs_gbm is not None and 1 <= ensemble_vs_gbm <= 3
        lines.append(
            f"- Ensemble {target} improvement over GBM 1–3%: "
            f"**{'PASS' if ensemble_pass else 'FAIL'}** "
            f"({_format_metric(ensemble_vs_gbm, percentage_points=True)})."
        )
        for model in MODEL_PREFIXES:
            coverage = lookup.get(
                (target, f"{model}_{target}", 0, "interval_coverage")
            )
            value = float(coverage["metric_value"]) if coverage else None
            passed = value is not None and 0.75 <= value <= 0.85
            lines.append(
                f"- {model} {target} interval coverage 0.75–0.85: "
                f"**{'PASS' if passed else 'FAIL'}** "
                f"({_format_metric(value, percent=True)})."
            )
    lines.append(
        "- Any FAIL is not treated as success. It requires a leakage and data-boundary "
        "review before the model is trusted, including when the result is better than "
        "expected."
    )
    return lines


def _feature_section(raw_config: Mapping[str, Any]) -> list[str]:
    feature_config = raw_config["features"]
    baseline = feature_config["baseline"]
    lines = [
        "### Baseline",
        "",
        f"- Base feature: `rolling_mean_{baseline['base_window']}`.",
        f"- Training-only context ratios: {', '.join(baseline['context_columns'])}.",
        "- Bounds: approximately one prior rolling standard deviation around the point prediction; not calibrated by construction.",
        "",
        "### GBM",
        "",
        "The GBM uses the configured feature list independently for each target:",
    ]
    for target, features in raw_config["gbm"]["features"].items():
        lines.append(f"- `{target}`: {', '.join(f'`{feature}`' for feature in features)}")
    lines.extend(
        [
            "",
            "### Ensemble",
            "",
            "The ensemble combines the versioned baseline and GBM predictions. "
            "Production weights remain configured static weights; evaluation-only "
            "weights use strictly earlier folds.",
        ]
    )
    return lines


def write_reports(
    rows: Sequence[Mapping[str, Any]],
    *,
    raw_config: Mapping[str, Any],
    market: MarketComparison,
    model_card_path: Path = DEFAULT_MODEL_CARD,
    report_path: Path = DEFAULT_REPORT,
) -> None:
    validated = validate_sport_config(dict(raw_config))
    settings = validated.backtest
    if settings is None:
        raise ValueError("No backtest settings are configured")
    summary = _summary_table(rows)
    folds = _fold_coverage_table(rows)
    bins = _bin_table(rows)
    bias = _bias_review(rows)
    expectations = _expectation_lines(rows)
    objective_table = _objective_table(rows)
    weight_summary = _weight_summary_table(rows)
    objective_rows_available = any(
        str(row["metric"]).startswith(("mae_absolute_objective", "weight_absolute_"))
        for row in rows
    )
    appendix_path = model_card_path.with_name(
        f"{model_card_path.stem}-appendix.csv"
    )
    _write_fold_appendix(rows, path=appendix_path)
    scored_fold_counts = {
        target: len(
            {
                int(row["fold_number"])
                for row in rows
                if str(row["stat_target"]) == target
                and str(row["metric"]) == "interval_coverage"
                and int(row["fold_number"]) > POOLED_FOLD
            }
        )
        for target in sorted({str(row["stat_target"]) for row in rows})
    }
    market_sentence = (
        f"Market comparison sample: {market.paired_rows} paired "
        "prediction/line/result rows."
    )
    report_lines = [
        "# Checkpoint 12 — Historical backtest and calibration",
        "",
        f"Evaluation window: `{settings.start_date}` through `{settings.end_date}` "
        "(monthly folds; test end is exclusive).",
        "Scored monthly folds: "
        + ", ".join(f"{target}={count}" for target, count in scored_fold_counts.items())
        + ". Calendar windows without a test row or without strictly earlier "
        "training rows are not scored.",
        "",
        "## Pooled metrics",
        "",
        *summary,
        "",
        "## Fold-level interval coverage",
        "",
        *folds,
        "",
        "## Pooled calibration by prediction bin",
        "",
        *bins,
        "",
        "## OOF objective comparison",
        "",
        *objective_table,
        "",
        "Coverage near 80% means the nominal 0.1–0.9 interval contains outcomes "
        "about eight times in ten. Higher coverage usually means intervals are too "
        "wide; lower coverage means they are too narrow.",
        "Interval crossing and repair counts are persisted with each corrected run. "
        "Older append-only runs report these fields as unavailable rather than "
        "reconstructing them.",
        "",
        "## Fold-level bias-sign review",
        "",
        *bias,
        "",
        "## Expectation reconciliation",
        "",
        *expectations,
        "",
        "## Market comparison",
        "",
        market_sentence,
        "",
        f"- Prediction/line pairs before requiring a known result: {market.prediction_line_pairs}.",
        f"- Pairs with a completed match and known target result: {market.known_result_pairs}.",
        f"- Providers in the paired sample: {', '.join(market.providers) or 'none'}.",
        "- No hit rate or ROI is reported because this sample is not informative.",
        "",
        "## Data coverage",
        "",
        "- Feature pipeline: ATP men only (`players.tour = 'ATP'`).",
        "- Captured odds archive: 100% WTA.",
        "- Captured markets: Sets Won, Games Won, and Break Points Won.",
        "- Active model targets: aces, double faults, and service games.",
        "- The current model/market intersection is empty; this is a data-domain "
        "mismatch, not a capture-start-date explanation.",
        "",
        "## Reproducibility and boundaries",
        "",
        "- Each model was scored on the same test rows within each monthly fold.",
        "- Training rows were restricted to event dates strictly before the fold cutoff.",
        "- Ensemble weights were fit only from earlier scored folds.",
        "- Fold-level metrics and calibration rows "
        f"are in [{appendix_path.name}]({appendix_path.name}).",
        "- Results are appended to `model_backtest_results`; prior runs are not overwritten.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    model_card_lines = [
        "# Tennis player-prop model card v1",
        "",
        "This document describes what was evaluated, how it was evaluated, and when "
        "the predictions should not be trusted. It is written for a reader who did "
        "not build the pipeline.",
        "",
        "## Evaluation window and training rule",
        "",
        f"- Sport: `{validated.sport}`.",
        f"- Training/test window: `{settings.start_date}` through `{settings.end_date}`.",
        f"- Fold cadence: every {settings.step_months} month(s).",
        "- Scored monthly folds: "
        + ", ".join(f"{target}={count}" for target, count in scored_fold_counts.items())
        + ". Calendar windows without a test row or without strictly earlier "
        "training rows are not scored.",
        "- For each fold, training uses only eligible rows before the cutoff; the "
        "following monthly window is the test set.",
        "- The three targets are aces, double faults, and service games.",
        "",
        "## Model versions",
        "",
        "- `baseline_v1_<target>` is a transparent rolling-mean reference with "
        "training-period context adjustments.",
        "- `gbm_v1_<target>` is a LightGBM quantile model with 0.1, 0.5, and 0.9 "
        "quantiles. The median is the point prediction and the outer quantiles "
        "form the interval.",
        "- `ensemble_v1_<target>` combines the versioned baseline and GBM outputs. "
        "Evaluation-only weights may be fitted from earlier folds; production uses "
        "the configured static weights.",
        "",
        "## Production versus evaluation weights (read before using ensemble metrics)",
        "",
        "The ensemble scores in this document are not the exact artifact that "
        "production currently runs. Walk-forward evaluation fits weights from "
        "strictly earlier scored folds so it can measure a time-safe adaptive "
        "ensemble. Production prediction generation uses the configured static "
        "weights from `config/tennis.yaml`; those fitted evaluation weights are "
        "not persisted as a production model artifact.",
        "",
        "### Fitted weight summary",
        "",
        *weight_summary,
        *(
            [
                "",
                "The persisted append-only run used to rebuild this card predates "
                "objective-specific weight instrumentation; the corrected evaluator "
                "will populate this table on its next full run.",
            ]
            if not objective_rows_available
            else []
        ),
        "",
        "### OOF objective comparison",
        "",
        *objective_table,
        "",
        "## Features",
        "",
        *_feature_section(raw_config),
        "",
        "## Pooled metrics",
        "",
        *summary,
        "",
        "## Calibration",
        "",
        "The headline metric is interval coverage: the fraction of realized outcomes "
        "inside `[lowerci, upperci]`. With 0.1 and 0.9 quantiles, a useful target "
        "is near 80%. Coverage that is too high usually means intervals are too wide "
        "or conservative. Coverage that is too low means intervals are too narrow.",
        "Pooled metric rows also report interval crossings and repaired rows. "
        "Unavailable means the append-only run predates that instrumentation.",
        "",
        "### Prediction-ranked bins",
        "",
        *bins,
        "",
        "### Fold-level bias-sign review",
        "",
        *bias,
        "",
        "## Expectation reconciliation",
        "",
        *expectations,
        "",
        "## Known limitations",
        "",
        "- `games_won` and `sets_won` are conceptually empty in the current match "
        "store: the source transform leaves both fields NULL, so they are disabled "
        "targets rather than usable features.",
        "- Event dates are estimated from tournament start dates using "
        "`ROUND_OFFSETS` in the Sackmann ETL. The round ordering is useful for "
        "chronology, but the absolute dates are approximate.",
        f"- {market_sentence} The current market comparison is empty because the "
        "feature and odds data domains do not intersect; it is not explained by "
        "the odds capture start date.",
        "- The baseline interval is a rolling-standard-deviation heuristic, not a "
        "calibrated probability interval.",
        "",
        "## Conditions for not trusting a prediction",
        "",
        "- The player lacks the configured minimum history or key features are NULL.",
        "- Fold-level coverage is unstable or materially outside 0.75–0.85.",
        "- Mean bias has the same sign across most folds without a documented reason.",
        "- The result is outside the pre-registered expectation ranges until leakage "
        "and data-boundary causes have been investigated.",
        "- A market comparison or betting conclusion is based on the current tiny "
        "odds sample.",
        "",
        "## Market comparison",
        "",
        market_sentence,
        "",
        f"Prediction/line pairs before a known result: {market.prediction_line_pairs}. "
        f"Known-result pairs: {market.known_result_pairs}. Providers: "
        f"{', '.join(market.providers) or 'none'}.",
        "No hit rate or ROI is reported because the sample is not yet informative.",
        "",
        "## Data coverage",
        "",
        "- The feature pipeline is ATP men only: it selects `players.tour = 'ATP'`.",
        "- The captured odds archive to date is 100% WTA.",
        "- Captured markets are Sets Won, Games Won, and Break Points Won.",
        "- Active model targets are aces, double faults, and service games.",
        "- Therefore the current model/market intersection is empty. Collecting "
        "more rows under the current configuration will not create a paired row; "
        "the domain mismatch is documented here rather than changed in this cleanup.",
    ]
    model_card_path.parent.mkdir(parents=True, exist_ok=True)
    model_card_path.write_text(
        "\n".join(model_card_lines) + "\n",
        encoding="utf-8",
    )


def run_checkpoint12(
    config_path: Path = DEFAULT_CONFIG,
    *,
    dry_run: bool = False,
    fold_detail: bool = False,
) -> list[dict[str, Any]]:
    raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    rows = run_ensemble_backtest(
        config_path,
        dry_run=dry_run,
        fold_detail=fold_detail,
    )
    from db.connection import create_db_engine

    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            market = load_market_comparison(connection)
    finally:
        engine.dispose()
    write_reports(rows, raw_config=raw_config, market=market)
    print(
        f"\nCheckpoint 12 report written to {DEFAULT_REPORT}; "
        f"model card written to {DEFAULT_MODEL_CARD}."
    )
    print(
        f"Market comparison sample: {market.paired_rows} paired "
        "prediction/line/result rows; no hit rate or ROI reported."
    )
    return rows


def rebuild_reports_from_latest_run() -> None:
    """Recreate documents from the latest append-only database run."""

    from sqlalchemy import text
    from db.connection import create_db_engine

    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT modelversion, sport, stat_target, fold_number, metric,
                           metric_value, cutoff_date, test_end_date, row_count,
                           run_timestamp
                    FROM model_backtest_results
                    WHERE run_timestamp = (
                        SELECT MAX(run_timestamp) FROM model_backtest_results
                    )
                    ORDER BY stat_target, modelversion, fold_number, metric
                    """
                )
            ).mappings().all()
            market = load_market_comparison(connection)
    finally:
        engine.dispose()
    if not rows:
        raise ValueError("No model_backtest_results rows are available")
    raw_config = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    write_reports(rows, raw_config=raw_config, market=market)
    print(
        f"Rebuilt {DEFAULT_REPORT} and {DEFAULT_MODEL_CARD} from "
        f"{len(rows)} rows in the latest append-only run."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fold-detail", action="store_true")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Rebuild reports from the latest persisted backtest run without fitting models.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.report_only:
        rebuild_reports_from_latest_run()
        return 0
    run_checkpoint12(
        args.config,
        dry_run=args.dry_run,
        fold_detail=args.fold_detail,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())