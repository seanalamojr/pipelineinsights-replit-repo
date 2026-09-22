from datetime import date, timedelta

import pandas as pd
import pytest

from models.gbm import (
    GbmSettings,
    fit_quantile_models,
    gbm_settings_for_target,
    predict_quantile_models,
    prepare_matrix,
    select_shuffle_diagnostic_fold,
    shuffled_target_sabotage,
)


def _settings() -> GbmSettings:
    return GbmSettings(
        target="aces",
        sport="tennis",
        feature_version="test_v1",
        quantiles=(0.1, 0.5, 0.9),
        feature_columns=("signal", "nullable"),
        categorical_features=(),
        validation_fraction=0.25,
        early_stopping_rounds=5,
        params={
            "n_estimators": 40,
            "learning_rate": 0.1,
            "num_leaves": 5,
            "max_depth": 3,
            "min_child_samples": 2,
            "verbosity": -1,
        },
        descriptions={"signal": "Known pre-match signal", "nullable": "Unknown input"},
    )


def _frame() -> pd.DataFrame:
    rows = []
    for index in range(32):
        signal = float(index % 8)
        rows.append(
            {
                "player_id": f"p{index}",
                "match_id": f"m{index}",
                "event_date": date(2024, 1, 1) + timedelta(days=index),
                "target_value": signal * 2.0 + 1.0,
                "signal": signal,
                "nullable": None if index % 5 == 0 else float(index),
            }
        )
    return pd.DataFrame(rows)


def test_gbm_uses_the_configured_feature_list_and_preserves_nulls() -> None:
    matrix = prepare_matrix(
        _frame(),
        _settings(),
        {},
    )

    assert list(matrix.columns) == ["signal", "nullable"]
    assert matrix["nullable"].isna().sum() > 0


def test_gbm_fits_one_model_per_configured_quantile() -> None:
    frame = _frame()
    fitted = fit_quantile_models(frame.iloc[:24], _settings())
    predictions = predict_quantile_models(fitted, frame.iloc[24:], _settings())

    assert set(fitted.models) == {0.1, 0.5, 0.9}
    assert list(predictions.columns) == [
        "player_id",
        "match_id",
        "sport",
        "prop_type",
        "prediction",
        "lowerci",
        "upperci",
        "modelversion",
    ]
    assert len(predictions) == 8
    assert (predictions[["lowerci", "prediction", "upperci"]] >= 0).all().all()
    assert (predictions["lowerci"] <= predictions["prediction"]).all()
    assert (predictions["prediction"] <= predictions["upperci"]).all()


def test_gbm_shuffled_target_sabotage_degrades_a_signal_model() -> None:
    frame = _frame()
    ordinary_mae, shuffled_mae = shuffled_target_sabotage(
        frame.iloc[:24],
        frame.iloc[24:],
        _settings(),
        random_state=4,
    )

    assert shuffled_mae > ordinary_mae


def test_gbm_shuffle_diagnostic_skips_small_startup_folds() -> None:
    class Fold:
        def __init__(self, training_rows: int, test_rows: int) -> None:
            self.training = pd.DataFrame({"row": range(training_rows)})
            self.test = pd.DataFrame({"row": range(test_rows)})

    startup = Fold(training_rows=100, test_rows=10)
    mature = Fold(training_rows=5_000, test_rows=10)

    assert (
        select_shuffle_diagnostic_fold([startup, mature])
        is mature
    )


def test_gbm_requires_every_configured_feature() -> None:
    with pytest.raises(ValueError, match="missing configured GBM features"):
        prepare_matrix(
            _frame().drop(columns=["signal"]),
            _settings(),
            {},
        )


def test_tennis_gbm_settings_have_descriptions_for_selected_features() -> None:
    settings = gbm_settings_for_target(
        {
            "sport": "tennis",
            "source": {"matches": "source", "odds": "odds"},
            "stat_targets": ["aces"],
            "features": {
                "rolling_windows": [10],
                "include": ["rolling_stat"],
                "feature_version": "test_v1",
                "targets": {"aces": {}},
                "descriptions": {"signal": "Signal"},
                "baseline": {
                    "base_window": 10,
                    "context_columns": ["surface"],
                    "minimum_group_size": 1,
                },
            },
            "gbm": {
                "quantiles": [0.1, 0.5, 0.9],
                "features": {"aces": ["signal"]},
                "validation_fraction": 0.25,
                "early_stopping_rounds": 5,
                "params": {"n_estimators": 10},
            },
        },
        "aces",
    )

    assert settings.descriptions["signal"] == "Signal"