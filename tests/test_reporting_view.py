import os

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.integration


def _connection():
    if not os.getenv("DATABASE_URL"):
        pytest.skip(
            "DATABASE_URL is not configured for reporting-view tests",
            allow_module_level=True,
        )
    from db.connection import get_engine

    return get_engine().connect()


def test_reporting_view_exposes_observed_values_and_errors() -> None:
    with _connection() as connection:
        row = connection.execute(
            text(
                """
                SELECT prop_type, prop_label, actual_value, prediction_error,
                       feature_version, is_demo
                FROM vw_fact_player_prop_odds
                WHERE player_id = 'demo_ava_chen'
                  AND prop_type = 'aces'
                ORDER BY prediction_id
                LIMIT 1
                """
            )
        ).mappings().one()

    assert row["prop_type"] == "aces"
    assert row["prop_label"] == "Aces"
    assert row["actual_value"] is not None
    assert row["prediction_error"] is not None
    assert row["feature_version"]
    assert row["is_demo"] is True


def test_future_matches_keep_actuals_unavailable() -> None:
    with _connection() as connection:
        count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM vw_fact_player_prop_odds
                WHERE event_date > CURRENT_DATE
                  AND actual_value IS NOT NULL
                """
            )
        ).scalar_one()

    assert count == 0


def test_reporting_view_contains_api_projection_columns() -> None:
    expected = {
        "player",
        "player_id",
        "tour",
        "sport",
        "event_date",
        "matchup",
        "prop_type",
        "prop_label",
        "line",
        "prediction",
        "lowerci",
        "upperci",
        "edge",
        "normalized_edge",
        "side",
        "book",
        "modelversion",
        "predictiontimestamp",
        "status",
        "tournament",
        "surface",
        "over_price",
        "under_price",
        "actual_value",
        "prediction_error",
        "feature_version",
        "is_demo",
    }
    with _connection() as connection:
        columns = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'vw_fact_player_prop_odds'
                    """
                )
            )
        }

    assert expected <= columns