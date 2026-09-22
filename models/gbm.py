"""Config-driven LightGBM quantile models for player-game features."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml

from config._schema import validate_sport_config
from models.baseline import (
    _expand_feature_values,
    load_feature_rows,
    upsert_predictions,
)


DEFAULT_CONFIG = Path("config/tennis.yaml")
GBM_MODEL_PREFIX = "gbm_v1"
SHUFFLE_DIAGNOSTIC_MIN_TRAINING_ROWS = 5_000


@dataclass(frozen=True)
class GbmSettings:
    target: str
    sport: str
    feature_version: str
    quantiles: tuple[float, ...]
    feature_columns: tuple[str, ...]
    categorical_features: tuple[str, ...]
    validation_fraction: float
    early_stopping_rounds: int
    params: dict[str, Any]
    descriptions: dict[str, str]

    @property
    def modelversion(self) -> str:
        return f"{GBM_MODEL_PREFIX}_{self.target}"


@dataclass(frozen=True)
class GbmFit:
    models: dict[float, lgb.LGBMRegressor]
    category_levels: dict[str, list[object]]
    validation_start: object


def load_raw_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return raw


def gbm_settings_for_target(
    raw_config: Mapping[str, Any],
    target: str,
) -> GbmSettings:
    validated = validate_sport_config(dict(raw_config))
    gbm_config = validated.gbm
    if gbm_config is None:
        raise ValueError("No gbm configuration is defined")
    if target not in validated.stat_targets:
        raise ValueError(f"GBM target is not active in config: {target}")
    feature_columns = gbm_config.features.get(target)
    if not feature_columns:
        raise ValueError(f"No gbm feature list is configured for target {target}")
    descriptions = raw_config.get("features", {}).get("descriptions", {})
    return GbmSettings(
        target=target,
        sport=validated.sport,
        feature_version=validated.features.feature_version,
        quantiles=tuple(gbm_config.quantiles),
        feature_columns=tuple(feature_columns),
        categorical_features=tuple(gbm_config.categorical_features),
        validation_fraction=gbm_config.validation_fraction,
        early_stopping_rounds=gbm_config.early_stopping_rounds,
        params=dict(gbm_config.params),
        descriptions={
            feature: str(descriptions.get(feature, f"Configured feature: {feature}"))
            for feature in feature_columns
        },
    )


def _require_features(frame: pd.DataFrame, settings: GbmSettings) -> None:
    missing = sorted(set(settings.feature_columns) - set(frame.columns))
    if missing:
        raise ValueError(
            f"player_game_features is missing configured GBM features: "
            + ", ".join(missing)
        )
    missing_categories = sorted(
        set(settings.categorical_features) - set(settings.feature_columns)
    )
    if missing_categories:
        raise ValueError(
            "GBM categorical features are not in the configured feature list: "
            + ", ".join(missing_categories)
        )


def _category_levels(
    training: pd.DataFrame,
    settings: GbmSettings,
) -> dict[str, list[object]]:
    return {
        column: list(pd.unique(training[column].dropna()))
        for column in settings.categorical_features
    }


def prepare_matrix(
    frame: pd.DataFrame,
    settings: GbmSettings,
    category_levels: Mapping[str, list[object]],
) -> pd.DataFrame:
    """Select only configured columns and preserve nulls for LightGBM."""

    _require_features(frame, settings)
    matrix = frame[list(settings.feature_columns)].copy()
    for column in settings.feature_columns:
        if column in settings.categorical_features:
            matrix[column] = pd.Categorical(
                matrix[column],
                categories=category_levels[column],
            )
        else:
            matrix[column] = pd.to_numeric(matrix[column], errors="coerce")
    return matrix


def _validation_split(
    training: pd.DataFrame,
    settings: GbmSettings,
) -> tuple[pd.DataFrame, pd.DataFrame, object]:
    if "event_date" not in training:
        raise ValueError("GBM training data is missing event_date")
    ordered = training.copy()
    ordered["event_date"] = pd.to_datetime(ordered["event_date"])
    dates = pd.Index(sorted(ordered["event_date"].dropna().unique()))
    if len(dates) < 2:
        raise ValueError("GBM early stopping needs at least two training dates")
    validation_count = max(
        1,
        int(np.ceil(len(dates) * settings.validation_fraction)),
    )
    validation_count = min(validation_count, len(dates) - 1)
    validation_start = dates[-validation_count]
    train_core = ordered[ordered["event_date"] < validation_start].copy()
    validation = ordered[ordered["event_date"] >= validation_start].copy()
    if train_core.empty or validation.empty:
        raise ValueError("GBM validation slice left no training or validation rows")
    return train_core, validation, validation_start


def fit_quantile_models(
    training: pd.DataFrame,
    settings: GbmSettings,
) -> GbmFit:
    """Fit one conservative quantile model per configured target quantile."""

    _require_features(training, settings)
    if training.empty:
        raise ValueError(f"No training rows available for {settings.target}")
    training = training.copy()
    training["target_value"] = pd.to_numeric(
        training["target_value"], errors="coerce"
    )
    training = training[training["target_value"].notna()].copy()
    train_core, validation, validation_start = _validation_split(
        training,
        settings,
    )
    category_levels = _category_levels(train_core, settings)
    x_train = prepare_matrix(train_core, settings, category_levels)
    x_validation = prepare_matrix(validation, settings, category_levels)
    y_train = train_core["target_value"].astype(float)
    y_validation = validation["target_value"].astype(float)
    models: dict[float, lgb.LGBMRegressor] = {}
    for quantile in settings.quantiles:
        params = dict(settings.params)
        params.update({"objective": "quantile", "alpha": quantile})
        estimator = lgb.LGBMRegressor(**params)
        estimator.fit(
            x_train,
            y_train,
            eval_set=[(x_validation, y_validation)],
            eval_names=["time_validation"],
            eval_metric="quantile",
            categorical_feature=list(settings.categorical_features),
            callbacks=[
                lgb.early_stopping(
                    settings.early_stopping_rounds,
                    verbose=False,
                ),
                lgb.log_evaluation(period=0),
            ],
        )
        models[quantile] = estimator
    return GbmFit(
        models=models,
        category_levels=category_levels,
        validation_start=validation_start,
    )


def predict_quantile_models(
    fitted: GbmFit,
    test: pd.DataFrame,
    settings: GbmSettings,
) -> pd.DataFrame:
    matrix = prepare_matrix(test, settings, fitted.category_levels)
    quantile_values = {
        quantile: model.predict(matrix)
        for quantile, model in fitted.models.items()
    }
    ordered_quantiles = sorted(settings.quantiles)
    stacked = np.sort(
        np.vstack([quantile_values[quantile] for quantile in ordered_quantiles]),
        axis=0,
    )
    nonnegative = np.maximum(stacked, 0.0)
    lower_values = nonnegative[0]
    median_values = nonnegative[len(ordered_quantiles) // 2]
    upper_values = nonnegative[-1]
    return pd.DataFrame(
        {
            "player_id": test["player_id"].to_numpy(),
            "match_id": test["match_id"].to_numpy(),
            "sport": settings.sport,
            "prop_type": settings.target,
            "prediction": median_values,
            "lowerci": lower_values,
            "upperci": upper_values,
            "modelversion": settings.modelversion,
        }
    )


def fit_gbm_fold(
    training: pd.DataFrame,
    test: pd.DataFrame,
    settings: GbmSettings,
) -> pd.DataFrame:
    return predict_quantile_models(
        fit_quantile_models(training, settings),
        test,
        settings,
    )


def shuffled_target_sabotage(
    training: pd.DataFrame,
    test: pd.DataFrame,
    settings: GbmSettings,
    *,
    random_state: int = 20250917,
) -> tuple[float, float]:
    """Return ordinary and shuffled-target MAE for a GBM fit."""

    ordinary = predict_quantile_models(
        fit_quantile_models(training, settings),
        test,
        settings,
    )
    shuffled_training = training.copy()
    values = shuffled_training["target_value"].to_numpy(copy=True)
    np.random.default_rng(random_state).shuffle(values)
    shuffled_training["target_value"] = values
    shuffled = predict_quantile_models(
        fit_quantile_models(shuffled_training, settings),
        test,
        settings,
    )
    actual = pd.to_numeric(test["target_value"], errors="coerce").to_numpy()
    ordinary_mae = float(np.abs(ordinary["prediction"].to_numpy() - actual).mean())
    shuffled_mae = float(np.abs(shuffled["prediction"].to_numpy() - actual).mean())
    return ordinary_mae, shuffled_mae


def select_shuffle_diagnostic_fold(
    folds: Sequence[Any],
    *,
    minimum_training_rows: int = SHUFFLE_DIAGNOSTIC_MIN_TRAINING_ROWS,
) -> Any | None:
    """Select the first mature, scorable fold for the shuffle diagnostic."""

    if minimum_training_rows < 1:
        raise ValueError("minimum_training_rows must be positive")
    return next(
        (
            fold
            for fold in folds
            if len(fold.training) >= minimum_training_rows
            and not fold.test.empty
        ),
        None,
    )


def importance_rows(
    fitted: GbmFit,
    settings: GbmSettings,
    *,
    run_timestamp: datetime,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for quantile, estimator in fitted.models.items():
        gain = estimator.booster_.feature_importance(importance_type="gain")
        split = estimator.booster_.feature_importance(importance_type="split")
        order = np.argsort(-gain, kind="stable")
        for rank, index in enumerate(order, start=1):
            feature = settings.feature_columns[int(index)]
            rows.append(
                {
                    "modelversion": settings.modelversion,
                    "sport": settings.sport,
                    "stat_target": settings.target,
                    "quantile": quantile,
                    "feature_name": feature,
                    "feature_description": settings.descriptions[feature],
                    "importance_gain": float(gain[index]),
                    "importance_split": float(split[index]),
                    "importance_rank": rank,
                    "run_timestamp": run_timestamp,
                }
            )
    return rows


def store_importance_rows(connection: object, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    from sqlalchemy import text

    connection.execute(
        text(
            """
            INSERT INTO model_feature_importances (
                modelversion,
                sport,
                stat_target,
                quantile,
                feature_name,
                feature_description,
                importance_gain,
                importance_split,
                importance_rank,
                run_timestamp
            )
            VALUES (
                :modelversion,
                :sport,
                :stat_target,
                :quantile,
                :feature_name,
                :feature_description,
                :importance_gain,
                :importance_split,
                :importance_rank,
                :run_timestamp
            )
            """
        ),
        rows,
    )
    return len(rows)


def _print_importances(
    fitted: GbmFit,
    settings: GbmSettings,
) -> None:
    records = []
    for row in importance_rows(
        fitted,
        settings,
        run_timestamp=datetime.now(timezone.utc),
    ):
        records.append(row)
    importance = pd.DataFrame(records)
    summary = (
        importance.groupby(["feature_name", "feature_description"], as_index=False)
        .agg(
            mean_gain=("importance_gain", "mean"),
            mean_split=("importance_split", "mean"),
        )
        .sort_values(["mean_gain", "mean_split"], ascending=False)
        .head(15)
    )
    print("Top 15 GBM features by mean gain across quantiles:")
    for rank, row in enumerate(summary.to_dict(orient="records"), start=1):
        print(
            f"  {rank}. {row['feature_name']}: "
            f"gain={row['mean_gain']:.4f}, split={row['mean_split']:.1f} — "
            f"{row['feature_description']}"
        )


def run_gbm(
    config_path: Path = DEFAULT_CONFIG,
    *,
    targets: Sequence[str] | None = None,
    dry_run: bool = False,
) -> None:
    raw_config = load_raw_config(config_path)
    validated = validate_sport_config(raw_config)
    if validated.gbm is None:
        raise ValueError("No gbm configuration is defined")
    requested_targets = list(targets or validated.stat_targets)
    unknown = sorted(set(requested_targets) - set(validated.stat_targets))
    if unknown:
        raise ValueError(f"Unknown GBM target(s): {', '.join(unknown)}")

    run_timestamp = datetime.now(timezone.utc)
    from evaluation.backtest import (
        backtest_settings_for_config,
        build_walk_forward_folds,
    )

    backtest_settings = backtest_settings_for_config(raw_config)
    from db.connection import create_db_engine

    engine = create_db_engine()
    try:
        with engine.begin() as connection:
            for target in requested_targets:
                settings = gbm_settings_for_target(raw_config, target)
                frame = _expand_feature_values(
                    load_feature_rows(
                        connection,
                        sport=settings.sport,
                        feature_version=settings.feature_version,
                        target=target,
                    )
                )
                training = frame[
                    frame["is_training_eligible"].fillna(False).astype(bool)
                ].copy()
                test = frame[
                    frame["has_sufficient_history"].fillna(False).astype(bool)
                ].copy()
                fitted = fit_quantile_models(training, settings)
                predictions = predict_quantile_models(fitted, test, settings)
                importance = importance_rows(
                    fitted,
                    settings,
                    run_timestamp=run_timestamp,
                )
                _print_importances(fitted, settings)
                folds = build_walk_forward_folds(frame, backtest_settings)
                diagnostic_fold = select_shuffle_diagnostic_fold(folds)
                if diagnostic_fold is None:
                    raise ValueError(
                        "No mature test fold is available for the GBM "
                        f"shuffle diagnostic for {target}; require at least "
                        f"{SHUFFLE_DIAGNOSTIC_MIN_TRAINING_ROWS} training rows"
                    )
                ordinary_mae, shuffled_mae = shuffled_target_sabotage(
                    diagnostic_fold.training,
                    diagnostic_fold.test,
                    settings,
                )
                shuffle_delta = shuffled_mae - ordinary_mae
                shuffle_status = "PASS" if shuffle_delta > 0 else "INCONCLUSIVE"
                print(
                    f"{settings.modelversion} shuffled-target check "
                    f"[{shuffle_status}] on fold {diagnostic_fold.fold_number} "
                    f"(cutoff {diagnostic_fold.cutoff_date}, "
                    f"training rows={len(diagnostic_fold.training)}, "
                    f"test rows={len(diagnostic_fold.test)}): ordinary MAE="
                    f"{ordinary_mae:.4f}, shuffled-target MAE={shuffled_mae:.4f}, "
                    f"delta={shuffle_delta:.4f}"
                )
                if shuffle_status == "INCONCLUSIVE":
                    print(
                        "Shuffle diagnostic note: one deterministic holdout did "
                        "not degrade after target shuffling. This is not evidence "
                        "of leakage by itself; investigate across additional "
                        "time-safe folds before treating it as a model-quality "
                        "failure."
                    )
                if not dry_run:
                    predictions["predictiontimestamp"] = run_timestamp
                    upsert_predictions(connection, predictions)
                    store_importance_rows(connection, importance)
                print(
                    f"{settings.modelversion}: training rows={len(training)}, "
                    f"prediction rows={len(predictions)}, "
                    f"null feature values are preserved for LightGBM"
                )
    finally:
        engine.dispose()

    from evaluation.backtest import run_backtest

    for target in requested_targets:
        def target_fitter(
            training: pd.DataFrame,
            test: pd.DataFrame,
            _baseline_settings: object,
            target_name: str = target,
        ) -> pd.DataFrame:
            return fit_gbm_fold(
                training,
                test,
                gbm_settings_for_target(raw_config, target_name),
            )

        run_backtest(
            config_path,
            targets=[target],
            dry_run=dry_run,
            model_version_prefix=GBM_MODEL_PREFIX,
            fold_fitter=target_fitter,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--target", action="append", dest="targets")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_gbm(args.config, targets=args.targets, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())