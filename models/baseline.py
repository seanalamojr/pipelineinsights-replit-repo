"""Config-driven baseline predictions from player_game_features only.

The baseline is intentionally simple: a prior rolling mean is multiplied by
training-period context ratios. It is a reference point for later models, not
an accuracy claim.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
import yaml

from config._schema import validate_sport_config
DEFAULT_CONFIG = Path("config/tennis.yaml")
BASELINE_MODEL_PREFIX = "baseline_v1"
MODEL_FEATURE_COLUMNS = (
    "target_value",
    "has_sufficient_history",
    "is_training_eligible",
)


@dataclass(frozen=True)
class BaselineSettings:
    target: str
    feature_version: str
    base_window: int
    context_columns: tuple[str, ...]
    minimum_group_size: int

    @property
    def base_column(self) -> str:
        return f"rolling_mean_{self.base_window}"

    @property
    def standard_deviation_column(self) -> str:
        return f"rolling_std_{self.base_window}"

    @property
    def modelversion(self) -> str:
        return f"{BASELINE_MODEL_PREFIX}_{self.target}"


@dataclass(frozen=True)
class BaselineResult:
    target: str
    modelversion: str
    rows_read: int
    training_rows: int
    training_rows_excluded: int
    prediction_rows_excluded: int
    missing_base_rows: int
    predictions: pd.DataFrame
    context_report: dict[str, dict[str, Any]]


def load_raw_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return raw


def baseline_settings_for_target(
    raw_config: Mapping[str, Any],
    target: str,
) -> BaselineSettings:
    """Return validated baseline settings or fail before reading any data."""

    validated = validate_sport_config(dict(raw_config))
    if target not in validated.stat_targets:
        raise ValueError(f"Baseline target is not active in config: {target}")
    baseline = validated.features.baseline
    if baseline is None:
        raise ValueError(
            f"No features.baseline configuration is defined for target {target}"
        )
    if baseline.base_window not in validated.features.rolling_windows:
        raise ValueError(
            f"Baseline base_window {baseline.base_window} is not one of the "
            f"configured rolling_windows"
        )
    return BaselineSettings(
        target=target,
        feature_version=validated.features.feature_version,
        base_window=baseline.base_window,
        context_columns=tuple(baseline.context_columns),
        minimum_group_size=baseline.minimum_group_size,
    )


def _expand_feature_values(frame: pd.DataFrame) -> pd.DataFrame:
    """Expose the stored JSON feature vector as model-local columns."""

    output = frame.copy()
    if "feature_values" not in output:
        return output
    parsed: list[dict[str, Any]] = []
    for value in output["feature_values"]:
        if isinstance(value, str):
            value = json.loads(value)
        parsed.append(value if isinstance(value, dict) else {})
    if parsed:
        feature_frame = pd.json_normalize(parsed, sep=".")
        for column in feature_frame.columns:
            if column not in output:
                output[column] = feature_frame[column].to_numpy()
    return output


def _require_model_columns(
    frame: pd.DataFrame,
    settings: BaselineSettings,
) -> None:
    required = {
        "player_id",
        "match_id",
        "sport",
        "stat_target",
        *MODEL_FEATURE_COLUMNS,
        settings.base_column,
        settings.standard_deviation_column,
        *settings.context_columns,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            "player_game_features is missing baseline inputs: "
            + ", ".join(missing)
        )


def compute_context_adjustments(
    frame: pd.DataFrame,
    settings: BaselineSettings,
) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    """Apply training-only context ratios and return their audit report."""

    frame = frame.copy()
    frame["target_value"] = pd.to_numeric(frame["target_value"], errors="coerce")
    _require_model_columns(frame, settings)
    training_mask = (
        frame["is_training_eligible"].fillna(False).astype(bool)
        & frame["target_value"].notna()
    )
    training = frame.loc[training_mask].copy()
    if training.empty:
        raise ValueError(f"No training-eligible rows available for {settings.target}")

    overall_mean = float(training["target_value"].mean())
    if overall_mean <= 0:
        raise ValueError(
            f"Training target mean must be positive for {settings.target}"
        )

    output = frame.copy()
    output["baseline_context_adjustment"] = 1.0
    report: dict[str, dict[str, Any]] = {}
    for column in settings.context_columns:
        grouped = (
            training.loc[training[column].notna()]
            .groupby(column, dropna=False)["target_value"]
            .agg(["mean", "count"])
        )
        eligible = grouped[grouped["count"] >= settings.minimum_group_size]
        multipliers: dict[object, float] = {
            key: float(values["mean"] / overall_mean)
            for key, values in eligible.iterrows()
        }
        adjustment_column = f"baseline_adjustment_{column}"
        output[adjustment_column] = (
            output[column].map(multipliers).fillna(1.0).astype(float)
        )
        output["baseline_context_adjustment"] *= output[adjustment_column]
        report[column] = {
            "overall_mean": overall_mean,
            "minimum_group_size": settings.minimum_group_size,
            "groups": {
                str(key): {
                    "count": int(values["count"]),
                    "multiplier": float(values["mean"] / overall_mean),
                }
                for key, values in eligible.iterrows()
            },
        }
    return output, report


def prepare_predictions(
    frame: pd.DataFrame,
    settings: BaselineSettings,
    *,
    predictiontimestamp: datetime | None = None,
) -> BaselineResult:
    """Build baseline predictions without writing to the database."""

    frame = _expand_feature_values(frame)
    _require_model_columns(frame, settings)
    if frame.empty:
        raise ValueError(f"No feature rows available for {settings.target}")
    if not (frame["stat_target"] == settings.target).all():
        raise ValueError("Baseline frame contains more than its configured target")

    adjusted, context_report = compute_context_adjustments(frame, settings)
    training_mask = adjusted["is_training_eligible"].fillna(False).astype(bool)
    history_mask = adjusted["has_sufficient_history"].fillna(False).astype(bool)
    candidate_mask = history_mask & adjusted[settings.base_column].notna()
    missing_base_rows = int((history_mask & ~candidate_mask).sum())

    candidates = adjusted.loc[candidate_mask].copy()
    prediction_values = (
        pd.to_numeric(candidates[settings.base_column], errors="coerce")
        * candidates["baseline_context_adjustment"]
    )
    standard_deviations = pd.to_numeric(
        candidates[settings.standard_deviation_column],
        errors="coerce",
    )
    lower = (prediction_values - standard_deviations).clip(lower=0)
    upper = prediction_values + standard_deviations
    timestamp = predictiontimestamp or datetime.now(timezone.utc)
    predictions = pd.DataFrame(
        {
            "player_id": candidates["player_id"].to_numpy(),
            "match_id": candidates["match_id"].to_numpy(),
            "sport": candidates["sport"].to_numpy(),
            "prop_type": settings.target,
            "prediction": prediction_values.to_numpy(),
            "lowerci": lower.where(standard_deviations.notna()).to_numpy(),
            "upperci": upper.where(standard_deviations.notna()).to_numpy(),
            "modelversion": settings.modelversion,
            "predictiontimestamp": timestamp,
        }
    )
    return BaselineResult(
        target=settings.target,
        modelversion=settings.modelversion,
        rows_read=len(adjusted),
        training_rows=int(training_mask.sum()),
        training_rows_excluded=int((~training_mask).sum()),
        prediction_rows_excluded=int((~history_mask).sum()),
        missing_base_rows=missing_base_rows,
        predictions=predictions,
        context_report=context_report,
    )


def load_feature_rows(
    connection: object,
    *,
    sport: str,
    feature_version: str,
    target: str,
) -> pd.DataFrame:
    """Read the complete model input from player_game_features only."""

    from sqlalchemy import text

    result = connection.execute(
        text(
            """
            SELECT
                player_id,
                match_id,
                event_date,
                sport,
                feature_version,
                stat_target,
                target_value,
                has_sufficient_history,
                is_training_eligible,
                feature_values
            FROM player_game_features
            WHERE sport = :sport
              AND feature_version = :feature_version
              AND stat_target = :target
              AND player_id NOT LIKE 'demo_%%'
            ORDER BY event_date, match_id, player_id
            """
        ),
        {
            "sport": sport,
            "feature_version": feature_version,
            "target": target,
        },
    )
    return pd.DataFrame(result.mappings().all())


def _prediction_rows(predictions: pd.DataFrame) -> list[dict[str, Any]]:
    if predictions.empty:
        return []
    rows: list[dict[str, Any]] = []
    for raw_row in predictions.to_dict(orient="records"):
        row: dict[str, Any] = {}
        for key, value in raw_row.items():
            if pd.isna(value):
                row[key] = None
            elif isinstance(value, pd.Timestamp):
                row[key] = value.to_pydatetime()
            else:
                row[key] = value.item() if hasattr(value, "item") else value
        row.setdefault("fold_number", None)
        row.setdefault("fold_cutoff_date", None)
        row.setdefault("fold_test_end_date", None)
        rows.append(row)
    return rows


PREDICTION_INSERT_SQL = """
    INSERT INTO player_prop_predictions (
        player_id,
        match_id,
        sport,
        prop_type,
        prediction,
        lowerci,
        upperci,
        modelversion,
        predictiontimestamp,
        fold_number,
        fold_cutoff_date,
        fold_test_end_date
    )
    VALUES (
        :player_id,
        :match_id,
        :sport,
        :prop_type,
        :prediction,
        :lowerci,
        :upperci,
        :modelversion,
        :predictiontimestamp,
        :fold_number,
        :fold_cutoff_date,
        :fold_test_end_date
    )
"""


def upsert_predictions(connection: object, predictions: pd.DataFrame) -> int:
    """Replace only same-version live rows; preserve every other model version."""

    rows = _prediction_rows(predictions)
    if not rows:
        return 0
    from sqlalchemy import text

    statement = text(
        PREDICTION_INSERT_SQL
        + """
        ON CONFLICT (player_id, match_id, prop_type, modelversion)
        DO UPDATE SET
            prediction = EXCLUDED.prediction,
            lowerci = EXCLUDED.lowerci,
            upperci = EXCLUDED.upperci,
            predictiontimestamp = EXCLUDED.predictiontimestamp,
            fold_number = EXCLUDED.fold_number,
            fold_cutoff_date = EXCLUDED.fold_cutoff_date,
            fold_test_end_date = EXCLUDED.fold_test_end_date
        """
    )
    connection.execute(statement, rows)
    return len(rows)


def insert_backtest_predictions(
    connection: object,
    predictions: pd.DataFrame,
) -> int:
    """Insert historical OOF rows once; conflicts fail instead of rewriting history."""

    rows = _prediction_rows(predictions)
    if not rows:
        return 0
    if any("_backtest_" not in str(row["modelversion"]) for row in rows):
        raise ValueError("Historical predictions require a run-specific backtest version")
    if any(
        row["fold_number"] is None
        or row["fold_cutoff_date"] is None
        or row["fold_test_end_date"] is None
        for row in rows
    ):
        raise ValueError("Historical predictions require complete fold provenance")

    from sqlalchemy import text

    connection.execute(text(PREDICTION_INSERT_SQL), rows)
    return len(rows)


def _print_report(
    result: BaselineResult,
    *,
    dry_run: bool,
    written: int,
) -> None:
    print(f"\nBaseline report: {result.target}")
    print(f"modelversion: {result.modelversion}")
    print(f"rows read from player_game_features: {result.rows_read}")
    print(f"training rows used: {result.training_rows}")
    print(
        "training rows excluded because is_training_eligible=false: "
        f"{result.training_rows_excluded}"
    )
    print(
        "prediction rows excluded because has_sufficient_history=false: "
        f"{result.prediction_rows_excluded}"
    )
    print(f"prediction rows excluded because base feature is NULL: {result.missing_base_rows}")
    print(f"predictions {'computed' if dry_run else 'written'}: {len(result.predictions) if dry_run else written}")
    print("context multipliers (training-period group target mean / overall mean):")
    for column, details in result.context_report.items():
        print(f"  {column}: overall mean {details['overall_mean']:.4f}")
        for group, values in details["groups"].items():
            print(
                f"    {group}: n={values['count']} "
                f"multiplier={values['multiplier']:.6f}"
            )
    print(
        "confidence bounds: lowerci and upperci are approximately one prior "
        "rolling standard deviation around the prediction; they are not "
        "calibrated probability intervals. Rows without that standard deviation "
        "keep NULL bounds."
    )


def run_baseline(
    config_path: Path = DEFAULT_CONFIG,
    *,
    targets: Sequence[str] | None = None,
    dry_run: bool = False,
) -> list[BaselineResult]:
    raw_config = load_raw_config(config_path)
    validated = validate_sport_config(raw_config)
    requested_targets = list(targets or validated.stat_targets)
    unknown = sorted(set(requested_targets) - set(validated.stat_targets))
    if unknown:
        raise ValueError(f"Unknown baseline target(s): {', '.join(unknown)}")

    from db.connection import create_db_engine

    engine = create_db_engine()
    results: list[BaselineResult] = []
    try:
        with engine.begin() as connection:
            for target in requested_targets:
                settings = baseline_settings_for_target(raw_config, target)
                frame = load_feature_rows(
                    connection,
                    sport=validated.sport,
                    feature_version=settings.feature_version,
                    target=target,
                )
                result = prepare_predictions(frame, settings)
                written = (
                    upsert_predictions(connection, result.predictions)
                    if not dry_run
                    else 0
                )
                _print_report(result, dry_run=dry_run, written=written)
                results.append(result)
    finally:
        engine.dispose()
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        help="Active stat target to build; repeat for multiple targets. Defaults to all.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and print baseline summaries without writing predictions.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_baseline(args.config, targets=args.targets, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())