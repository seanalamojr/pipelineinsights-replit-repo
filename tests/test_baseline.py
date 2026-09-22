from datetime import datetime, timezone

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from models.baseline import (
    BaselineSettings,
    baseline_settings_for_target,
    compute_context_adjustments,
    prepare_predictions,
    upsert_predictions,
)


def _config(*, baseline: dict | None = None) -> dict:
    features = {
        "rolling_windows": [3, 5, 10],
        "include": ["rolling_stat"],
        "feature_version": "tennis_v1",
        "minimum_history": 5,
        "targets": {"aces": {}},
    }
    if baseline is not None:
        features["baseline"] = baseline
    return {
        "sport": "tennis",
        "source": {"matches": "sackmann", "odds": "provider"},
        "stat_targets": ["aces"],
        "features": features,
    }


def _settings() -> BaselineSettings:
    return baseline_settings_for_target(
        _config(
            baseline={
                "base_window": 10,
                "context_columns": ["surface", "best_of", "tourney_level"],
                "minimum_group_size": 3,
            }
        ),
        "aces",
    )


def _frame() -> pd.DataFrame:
    rows = []
    for index, surface in enumerate(["Grass", "Grass", "Grass", "Clay", "Clay"]):
        rows.append(
            {
                "player_id": f"p{index}",
                "match_id": f"m{index}",
                "sport": "tennis",
                "stat_target": "aces",
                "target_value": 10 if surface == "Grass" else 4,
                "has_sufficient_history": True,
                "is_training_eligible": True,
                "rolling_mean_10": 8.0,
                "rolling_std_10": 2.0,
                "surface": surface,
                "best_of": 3,
                "tourney_level": "A",
            }
        )
    return pd.DataFrame(rows)


def test_baseline_requires_a_baseline_config() -> None:
    with pytest.raises(ValueError, match="No features.baseline"):
        baseline_settings_for_target(_config(), "aces")


def test_insufficient_history_produces_no_prediction_for_that_row() -> None:
    frame = _frame()
    frame.loc[4, "has_sufficient_history"] = False
    frame.loc[4, "is_training_eligible"] = False

    result = prepare_predictions(frame, _settings())

    assert set(result.predictions["match_id"]) == {"m0", "m1", "m2", "m3"}
    assert "m4" not in set(result.predictions["match_id"])
    assert result.prediction_rows_excluded == 1


def test_small_context_group_falls_back_to_exactly_one() -> None:
    adjusted, report = compute_context_adjustments(_frame(), _settings())

    assert adjusted.loc[adjusted["surface"] == "Clay", "baseline_adjustment_surface"].eq(
        1.0
    ).all()
    assert report["surface"]["groups"]["Grass"]["multiplier"] > 1.0
    assert "Clay" not in report["surface"]["groups"]


def test_same_model_version_upsert_does_not_duplicate_rows() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE player_prop_predictions (
                    player_id TEXT NOT NULL,
                    match_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    prop_type TEXT NOT NULL,
                    prediction NUMERIC NOT NULL,
                    lowerci NUMERIC,
                    upperci NUMERIC,
                    modelversion TEXT NOT NULL,
                    predictiontimestamp TIMESTAMP NOT NULL,
                    fold_number INTEGER,
                    fold_cutoff_date DATE,
                    fold_test_end_date DATE,
                    UNIQUE (player_id, match_id, prop_type, modelversion)
                )
                """
            )
        )
        predictions = pd.DataFrame(
            [
                {
                    "player_id": "p1",
                    "match_id": "m1",
                    "sport": "tennis",
                    "prop_type": "aces",
                    "prediction": 8.5,
                    "lowerci": 6.5,
                    "upperci": 10.5,
                    "modelversion": "baseline_v1_aces",
                    "predictiontimestamp": datetime.now(timezone.utc),
                }
            ]
        )

        upsert_predictions(connection, predictions)
        predictions.loc[0, "prediction"] = 9.5
        upsert_predictions(connection, predictions)

        count = connection.execute(
            text("SELECT COUNT(*) FROM player_prop_predictions")
        ).scalar_one()
        value = connection.execute(
            text("SELECT prediction FROM player_prop_predictions")
        ).scalar_one()

    assert count == 1
    assert float(value) == 9.5