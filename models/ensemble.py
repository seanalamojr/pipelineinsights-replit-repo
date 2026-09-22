"""Weighted, versioned ensembles built from existing model predictions.

Production ensemble generation reads only player_prop_predictions. Walk-forward
evaluation supplies earlier-fold predictions and outcomes separately so fitted
weights cannot see the fold they are scoring.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from config._schema import validate_sport_config
from models.baseline import upsert_predictions


DEFAULT_CONFIG = Path("config/tennis.yaml")
ENSEMBLE_MODEL_PREFIX = "ensemble_v1"
KEY_COLUMNS = ("player_id", "match_id")
PREDICTION_COLUMNS = ("prediction", "lowerci", "upperci")


@dataclass(frozen=True)
class EnsembleMember:
    modelversion: str
    weight: float


@dataclass(frozen=True)
class EnsembleSettings:
    target: str
    sport: str
    members: tuple[EnsembleMember, ...]
    missing_member_policy: str
    oof_objective: str = "absolute"

    @property
    def modelversion(self) -> str:
        return f"{ENSEMBLE_MODEL_PREFIX}_{self.target}"

    @property
    def configured_weights(self) -> dict[str, float]:
        return {member.modelversion: member.weight for member in self.members}


@dataclass(frozen=True)
class EnsembleResult:
    predictions: pd.DataFrame
    rows_read: int
    complete_rows: int
    renormalized_rows: int
    skipped_rows: int
    weights: dict[str, float]
    weight_source: str


def load_raw_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return raw


def ensemble_settings_for_target(
    raw_config: Mapping[str, Any],
    target: str,
) -> EnsembleSettings:
    validated = validate_sport_config(dict(raw_config))
    if target not in validated.stat_targets:
        raise ValueError(f"Ensemble target is not active in config: {target}")
    if validated.ensemble is None:
        raise ValueError("No ensemble configuration is defined")
    configured = validated.ensemble.targets.get(target)
    if configured is None:
        raise ValueError(f"No ensemble configuration is defined for {target}")
    return EnsembleSettings(
        target=target,
        sport=validated.sport,
        members=tuple(
            EnsembleMember(
                modelversion=member.modelversion,
                weight=member.weight,
            )
            for member in configured.members
        ),
        missing_member_policy=validated.ensemble.missing_member_policy,
        oof_objective=validated.ensemble.oof_objective,
    )


def _indexed_member_frame(
    frame: pd.DataFrame,
    modelversion: str,
) -> pd.DataFrame:
    required = set(KEY_COLUMNS) | set(PREDICTION_COLUMNS)
    if frame.empty and not required <= set(frame.columns):
        empty_index = pd.MultiIndex.from_tuples([], names=KEY_COLUMNS)
        return pd.DataFrame(columns=list(PREDICTION_COLUMNS), index=empty_index)
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            f"Predictions for {modelversion} are missing columns: "
            + ", ".join(missing)
        )
    indexed = frame[list(KEY_COLUMNS) + list(PREDICTION_COLUMNS)].copy()
    if indexed.duplicated(list(KEY_COLUMNS)).any():
        raise ValueError(f"Predictions for {modelversion} contain duplicate keys")
    indexed = indexed.set_index(list(KEY_COLUMNS))
    for column in PREDICTION_COLUMNS:
        indexed[column] = pd.to_numeric(indexed[column], errors="coerce")
    return indexed


def _project_simplex(values: np.ndarray) -> np.ndarray:
    """Project a vector onto the non-negative unit simplex."""

    sorted_values = np.sort(values)[::-1]
    cumulative = np.cumsum(sorted_values)
    valid = sorted_values - (cumulative - 1) / (np.arange(len(values)) + 1) > 0
    if not valid.any():
        return np.full(len(values), 1.0 / len(values))
    rho = int(np.flatnonzero(valid)[-1])
    threshold = (cumulative[rho] - 1) / (rho + 1)
    return np.maximum(values - threshold, 0.0)


def fit_oof_weights(
    member_predictions: Mapping[str, pd.DataFrame],
    actual_rows: pd.DataFrame,
    settings: EnsembleSettings,
    *,
    objective: str | None = None,
) -> dict[str, float]:
    """Fit weights only from complete rows supplied by earlier folds."""

    effective_objective = objective or settings.oof_objective
    if effective_objective not in {"absolute", "squared"}:
        raise ValueError(
            "OOF objective must be 'absolute' or 'squared', "
            f"not {effective_objective!r}"
        )
    if not member_predictions:
        return settings.configured_weights
    if not set(KEY_COLUMNS + ("target_value",)) <= set(actual_rows.columns):
        raise ValueError("OOF actual rows must contain keys and target_value")

    actual = actual_rows[list(KEY_COLUMNS) + ["target_value"]].copy()
    actual["target_value"] = pd.to_numeric(actual["target_value"], errors="coerce")
    actual = actual.dropna(subset=["target_value"]).set_index(list(KEY_COLUMNS))
    complete = actual.rename(columns={"target_value": "_target"})
    matrices: list[pd.Series] = []
    for member in settings.members:
        frame = member_predictions.get(member.modelversion)
        if frame is None:
            return settings.configured_weights
        indexed = _indexed_member_frame(frame, member.modelversion)
        complete = complete.join(
            indexed[["prediction"]].rename(
                columns={"prediction": member.modelversion}
            ),
            how="inner",
        )
    complete = complete.dropna()
    if complete.empty:
        return settings.configured_weights

    matrix = complete[[member.modelversion for member in settings.members]].to_numpy(
        dtype=float
    )
    target_values = complete["_target"].to_numpy(dtype=float)
    weights = np.array(
        [member.weight for member in settings.members],
        dtype=float,
    )
    spectral_norm = float(np.linalg.norm(matrix, ord=2))
    if spectral_norm == 0:
        return settings.configured_weights
    if effective_objective == "squared":
        step = 1.0 / (2.0 * spectral_norm**2)

    for iteration in range(1, 4001):
        residuals = matrix.dot(weights) - target_values
        if effective_objective == "absolute":
            gradient = matrix.T.dot(np.sign(residuals)) / len(target_values)
            step = 0.5 / (spectral_norm * np.sqrt(iteration))
        else:
            gradient = 2.0 * matrix.T.dot(residuals) / len(target_values)
        updated = _project_simplex(weights - step * gradient)
        if np.max(np.abs(updated - weights)) < 1e-10:
            weights = updated
            break
        weights = updated
    return {
        member.modelversion: float(weight)
        for member, weight in zip(settings.members, weights, strict=True)
    }


def combine_predictions(
    member_predictions: Mapping[str, pd.DataFrame],
    settings: EnsembleSettings,
    *,
    weights: Mapping[str, float] | None = None,
    predictiontimestamp: datetime | None = None,
    weight_source: str = "configured static weights",
) -> EnsembleResult:
    """Combine member rows without treating missing predictions as zero."""

    effective_weights = dict(weights or settings.configured_weights)
    if set(effective_weights) != {member.modelversion for member in settings.members}:
        raise ValueError("Ensemble weights do not match configured members")
    total_weight = sum(effective_weights.values())
    if total_weight <= 0:
        raise ValueError("Ensemble weights must have a positive total")
    effective_weights = {
        modelversion: weight / total_weight
        for modelversion, weight in effective_weights.items()
    }

    indexed_members = {
        member.modelversion: _indexed_member_frame(
            member_predictions.get(member.modelversion, pd.DataFrame()),
            member.modelversion,
        )
        for member in settings.members
    }
    all_keys: set[tuple[object, object]] = set()
    for indexed in indexed_members.values():
        all_keys.update(indexed.index.tolist())

    rows: list[dict[str, Any]] = []
    complete_rows = 0
    renormalized_rows = 0
    skipped_rows = 0
    timestamp = predictiontimestamp or datetime.now(timezone.utc)
    for key in sorted(all_keys, key=lambda value: (str(value[0]), str(value[1]))):
        present = [
            member.modelversion
            for member in settings.members
            if key in indexed_members[member.modelversion].index
            and pd.notna(
                indexed_members[member.modelversion].loc[key, "prediction"]
            )
        ]
        if not present:
            skipped_rows += 1
            continue
        if len(present) == len(settings.members):
            complete_rows += 1
        elif settings.missing_member_policy == "emit_none":
            skipped_rows += 1
            continue
        else:
            renormalized_rows += 1

        prediction_weights = {
            modelversion: effective_weights[modelversion] for modelversion in present
        }
        prediction_weight_total = sum(prediction_weights.values())
        prediction_weights = {
            modelversion: weight / prediction_weight_total
            for modelversion, weight in prediction_weights.items()
        }
        prediction = sum(
            prediction_weights[modelversion]
            * float(indexed_members[modelversion].loc[key, "prediction"])
            for modelversion in present
        )

        def weighted_bound(column: str) -> float | None:
            available = [
                modelversion
                for modelversion in present
                if pd.notna(indexed_members[modelversion].loc[key, column])
            ]
            if not available:
                return None
            bound_weights = {
                modelversion: effective_weights[modelversion]
                for modelversion in available
            }
            bound_total = sum(bound_weights.values())
            return sum(
                bound_weights[modelversion]
                / bound_total
                * float(indexed_members[modelversion].loc[key, column])
                for modelversion in available
            )

        lower = weighted_bound("lowerci")
        upper = weighted_bound("upperci")
        if lower is not None:
            lower = max(0.0, min(lower, prediction))
        if upper is not None:
            upper = max(upper, prediction)
        rows.append(
            {
                "player_id": key[0],
                "match_id": key[1],
                "sport": settings.sport,
                "prop_type": settings.target,
                "prediction": prediction,
                "lowerci": lower,
                "upperci": upper,
                "modelversion": settings.modelversion,
                "predictiontimestamp": timestamp,
            }
        )

    predictions = pd.DataFrame(rows)
    return EnsembleResult(
        predictions=predictions,
        rows_read=len(all_keys),
        complete_rows=complete_rows,
        renormalized_rows=renormalized_rows,
        skipped_rows=skipped_rows,
        weights=effective_weights,
        weight_source=weight_source,
    )


def load_member_predictions(
    connection: object,
    *,
    sport: str,
    target: str,
    modelversions: Sequence[str],
) -> dict[str, pd.DataFrame]:
    from sqlalchemy import text

    result = connection.execute(
        text(
            """
            SELECT player_id, match_id, sport, prop_type, prediction,
                   lowerci, upperci, modelversion, predictiontimestamp
            FROM player_prop_predictions
            WHERE sport = :sport
              AND prop_type = :target
              AND modelversion = ANY(:modelversions)
            ORDER BY match_id, player_id, modelversion
            """
        ),
        {
            "sport": sport,
            "target": target,
            "modelversions": list(modelversions),
        },
    )
    rows = pd.DataFrame(result.mappings().all())
    return {
        modelversion: rows[rows["modelversion"] == modelversion].copy()
        if not rows.empty
        else pd.DataFrame(columns=list(KEY_COLUMNS) + list(PREDICTION_COLUMNS))
        for modelversion in modelversions
    }


def _print_report(
    result: EnsembleResult,
    settings: EnsembleSettings,
    *,
    dry_run: bool,
    written: int,
) -> None:
    print(f"\nEnsemble report: {settings.target}")
    print(f"modelversion: {settings.modelversion}")
    print(
        "production weights are configured static weights; fitted walk-forward "
        "weights are evaluation-only"
    )
    print(
        "weights: "
        + ", ".join(
            f"{modelversion}={weight:.4f}"
            for modelversion, weight in result.weights.items()
        )
    )
    print(f"weight source: {result.weight_source}")
    print(f"member rows read: {result.rows_read}")
    print(f"complete-member rows: {result.complete_rows}")
    print(f"renormalized missing-member rows: {result.renormalized_rows}")
    print(f"skipped missing-member rows: {result.skipped_rows}")
    print(
        f"predictions {'computed' if dry_run else 'written'}: "
        f"{len(result.predictions) if dry_run else written}"
    )
    print(
        "interval note: weighted member bounds are a heuristic, not a "
        "statistically calibrated interval; Checkpoint 12 should measure "
        "whether coverage is near 80%."
    )
    print(
        "A stacked meta-model is not built here. A safe version would need "
        "stored out-of-fold member predictions, a time-aware training split, "
        "regularization, and a separately evaluated calibration policy."
    )


def run_ensemble(
    config_path: Path = DEFAULT_CONFIG,
    *,
    targets: Sequence[str] | None = None,
    dry_run: bool = False,
) -> list[EnsembleResult]:
    """Write ensemble predictions using only existing member predictions."""

    raw_config = load_raw_config(config_path)
    validated = validate_sport_config(raw_config)
    if validated.ensemble is None:
        raise ValueError("No ensemble configuration is defined")
    requested_targets = list(targets or validated.stat_targets)
    unknown = sorted(set(requested_targets) - set(validated.stat_targets))
    if unknown:
        raise ValueError(f"Unknown ensemble target(s): {', '.join(unknown)}")

    from db.connection import create_db_engine

    engine = create_db_engine()
    results: list[EnsembleResult] = []
    run_timestamp = datetime.now(timezone.utc)
    try:
        with engine.begin() as connection:
            for target in requested_targets:
                settings = ensemble_settings_for_target(raw_config, target)
                member_predictions = load_member_predictions(
                    connection,
                    sport=settings.sport,
                    target=target,
                    modelversions=[
                        member.modelversion for member in settings.members
                    ],
                )
                result = combine_predictions(
                    member_predictions,
                    settings,
                    predictiontimestamp=run_timestamp,
                )
                written = (
                    upsert_predictions(connection, result.predictions)
                    if not dry_run
                    else 0
                )
                _print_report(
                    result,
                    settings,
                    dry_run=dry_run,
                    written=written,
                )
                results.append(result)
    finally:
        engine.dispose()
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--target", action="append", dest="targets")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_ensemble(args.config, targets=args.targets, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())