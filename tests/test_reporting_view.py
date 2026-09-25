import os
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


pytestmark = pytest.mark.integration


def _connection():
    if not os.getenv("DATABASE_URL"):
        pytest.skip(
            "DATABASE_URL is not configured for reporting-view tests",
            allow_module_level=True,
        )
    from db.connection import get_engine

    return get_engine().connect()


@pytest.fixture
def isolated_connection():
    connection = _connection()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()


def _insert_synthetic_match(connection):
    suffix = uuid4().hex
    player_id = f"card_c_synthetic_player_{suffix}"
    opponent_id = f"card_c_synthetic_opponent_{suffix}"
    match_id = f"card_c_synthetic_match_{suffix}"
    event_date = date.today() + timedelta(days=30)

    connection.execute(
        text(
            """
            INSERT INTO players (player_id, full_name, tour)
            VALUES (:player_id, :player_name, 'ATP'),
                   (:opponent_id, :opponent_name, 'ATP')
            """
        ),
        {
            "player_id": player_id,
            "player_name": f"Card C Synthetic Player {suffix}",
            "opponent_id": opponent_id,
            "opponent_name": f"Card C Synthetic Opponent {suffix}",
        },
    )
    connection.execute(
        text(
            """
            INSERT INTO matches (
                match_id, event_date, tournament, surface, round,
                player_id, opponent_id, is_winner
            )
            VALUES
                (:match_id, :event_date, 'Card C Synthetic Event', 'Hard',
                 'R32', :player_id, :opponent_id, false),
                (:match_id, :event_date, 'Card C Synthetic Event', 'Hard',
                 'R32', :opponent_id, :player_id, true)
            """
        ),
        {
            "match_id": match_id,
            "event_date": event_date,
            "player_id": player_id,
            "opponent_id": opponent_id,
        },
    )
    return player_id, opponent_id, match_id


def _insert_prediction(
    connection,
    *,
    player_id,
    match_id,
    modelversion,
    prediction=10.0,
    lowerci=8.0,
    upperci=12.0,
):
    connection.execute(
        text(
            """
            INSERT INTO player_prop_predictions (
                player_id, match_id, sport, prop_type, prediction,
                lowerci, upperci, modelversion
            )
            VALUES (
                :player_id, :match_id, 'tennis', 'aces', :prediction,
                :lowerci, :upperci, :modelversion
            )
            """
        ),
        {
            "player_id": player_id,
            "match_id": match_id,
            "prediction": prediction,
            "lowerci": lowerci,
            "upperci": upperci,
            "modelversion": modelversion,
        },
    )


def _insert_odds(
    connection,
    *,
    player_id,
    match_id,
    player_name,
    book,
    line,
):
    captured_at = datetime.now(timezone.utc)
    connection.execute(
        text(
            """
            INSERT INTO odds (
                match_id, player_id, book, prop_type, line,
                over_price, under_price, captured_at, provider,
                provider_event_id, provider_market_id,
                provider_player_name, resolved_at
            )
            VALUES (
                :match_id, :player_id, :book, 'aces', :line,
                -110, -110, :captured_at, 'card-c-synthetic',
                :provider_event_id, 'card-c-synthetic-aces',
                :player_name, :resolved_at
            )
            """
        ),
        {
            "match_id": match_id,
            "player_id": player_id,
            "book": book,
            "line": line,
            "captured_at": captured_at,
            "provider_event_id": match_id,
            "player_name": player_name,
            "resolved_at": captured_at,
        },
    )


def _assert_prediction_insert_rejected(
    connection,
    *,
    player_id,
    match_id,
    modelversion,
    prediction=10.0,
    lowerci=8.0,
    upperci=12.0,
    constraint_name,
):
    savepoint = connection.begin_nested()
    try:
        _insert_prediction(
            connection,
            player_id=player_id,
            match_id=match_id,
            modelversion=modelversion,
            prediction=prediction,
            lowerci=lowerci,
            upperci=upperci,
        )
    except IntegrityError as error:
        savepoint.rollback()
        assert constraint_name in str(error.orig)
    else:
        savepoint.rollback()
        pytest.fail(f"Expected database constraint {constraint_name!r} to reject row")


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


def test_prediction_without_odds_stays_visible_with_null_market_fields(
    isolated_connection,
) -> None:
    player_id, _opponent_id, match_id = _insert_synthetic_match(
        isolated_connection
    )
    modelversion = f"card_c_no_odds_{uuid4().hex}"
    _insert_prediction(
        isolated_connection,
        player_id=player_id,
        match_id=match_id,
        modelversion=modelversion,
    )

    row = isolated_connection.execute(
        text(
            """
            SELECT prediction_id, line, over_price, under_price,
                   edge, side, normalized_edge
            FROM vw_fact_player_prop_odds
            WHERE player_id = :player_id
              AND match_id = :match_id
              AND modelversion = :modelversion
            """
        ),
        {
            "player_id": player_id,
            "match_id": match_id,
            "modelversion": modelversion,
        },
    ).mappings().one()

    assert row["prediction_id"] is not None
    assert row["line"] is None
    assert row["over_price"] is None
    assert row["under_price"] is None
    assert row["edge"] is None
    assert row["side"] is None
    assert row["normalized_edge"] is None


def test_three_books_repeat_one_prediction_exactly_three_times(
    isolated_connection,
) -> None:
    player_id, _opponent_id, match_id = _insert_synthetic_match(
        isolated_connection
    )
    suffix = uuid4().hex
    modelversion = f"card_c_book_fanout_{suffix}"
    player_name = f"Card C Synthetic Player {suffix}"
    _insert_prediction(
        isolated_connection,
        player_id=player_id,
        match_id=match_id,
        modelversion=modelversion,
        prediction=9.25,
        lowerci=7.0,
        upperci=11.5,
    )
    books = ("Synthetic Book A", "Synthetic Book B", "Synthetic Book C")
    for line, book in zip((8.5, 9.0, 9.5), books):
        _insert_odds(
            isolated_connection,
            player_id=player_id,
            match_id=match_id,
            player_name=player_name,
            book=book,
            line=line,
        )

    rows = isolated_connection.execute(
        text(
            """
            SELECT book, prediction
            FROM vw_fact_player_prop_odds
            WHERE player_id = :player_id
              AND match_id = :match_id
              AND modelversion = :modelversion
            ORDER BY book
            """
        ),
        {
            "player_id": player_id,
            "match_id": match_id,
            "modelversion": modelversion,
        },
    ).mappings().all()

    # Three rows are correct: one prediction repeated once per book keeps
    # each shop's line visible for line shopping.
    assert len(rows) == 3
    assert {row["book"] for row in rows} == set(books)
    assert {float(row["prediction"]) for row in rows} == {9.25}


def test_prediction_with_missing_match_is_rejected_and_not_visible(
    isolated_connection,
) -> None:
    suffix = uuid4().hex
    player_id = f"card_c_synthetic_player_{suffix}"
    match_id = f"card_c_missing_match_{suffix}"
    isolated_connection.execute(
        text(
            """
            INSERT INTO players (player_id, full_name, tour)
            VALUES (:player_id, :player_name, 'ATP')
            """
        ),
        {
            "player_id": player_id,
            "player_name": f"Card C Synthetic Player {suffix}",
        },
    )
    modelversion = f"card_c_missing_match_{suffix}"

    _assert_prediction_insert_rejected(
        isolated_connection,
        player_id=player_id,
        match_id=match_id,
        modelversion=modelversion,
        constraint_name="player_prop_predictions_match_fk",
    )
    visible_rows = isolated_connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM vw_fact_player_prop_odds
            WHERE player_id = :player_id
              AND match_id = :match_id
              AND modelversion = :modelversion
            """
        ),
        {
            "player_id": player_id,
            "match_id": match_id,
            "modelversion": modelversion,
        },
    ).scalar_one()

    assert visible_rows == 0


def test_prediction_interval_check_rejects_invalid_lower_bounds(
    isolated_connection,
) -> None:
    player_id, _opponent_id, match_id = _insert_synthetic_match(
        isolated_connection
    )

    _assert_prediction_insert_rejected(
        isolated_connection,
        player_id=player_id,
        match_id=match_id,
        modelversion=f"card_c_interval_above_prediction_{uuid4().hex}",
        prediction=10.0,
        lowerci=11.0,
        upperci=12.0,
        constraint_name="prediction_interval_ordered",
    )
    _assert_prediction_insert_rejected(
        isolated_connection,
        player_id=player_id,
        match_id=match_id,
        modelversion=f"card_c_interval_negative_{uuid4().hex}",
        prediction=10.0,
        lowerci=-1.0,
        upperci=12.0,
        constraint_name="prediction_interval_ordered",
    )


def test_edge_and_side_arithmetic_including_equal_line_boundary(
    isolated_connection,
) -> None:
    above_player_id, _opponent_id, above_match_id = _insert_synthetic_match(
        isolated_connection
    )
    above_modelversion = f"card_c_edge_above_{uuid4().hex}"
    suffix = uuid4().hex
    _insert_prediction(
        isolated_connection,
        player_id=above_player_id,
        match_id=above_match_id,
        modelversion=above_modelversion,
        prediction=10.0,
        lowerci=8.0,
        upperci=12.0,
    )
    _insert_odds(
        isolated_connection,
        player_id=above_player_id,
        match_id=above_match_id,
        player_name=f"Card C Synthetic Player {suffix}",
        book="Synthetic Book",
        line=8.0,
    )

    equal_player_id, _opponent_id, equal_match_id = _insert_synthetic_match(
        isolated_connection
    )
    equal_modelversion = f"card_c_edge_equal_{uuid4().hex}"
    equal_suffix = uuid4().hex
    _insert_prediction(
        isolated_connection,
        player_id=equal_player_id,
        match_id=equal_match_id,
        modelversion=equal_modelversion,
        prediction=10.0,
        lowerci=8.0,
        upperci=12.0,
    )
    _insert_odds(
        isolated_connection,
        player_id=equal_player_id,
        match_id=equal_match_id,
        player_name=f"Card C Synthetic Player {equal_suffix}",
        book="Synthetic Book",
        line=10.0,
    )

    above = isolated_connection.execute(
        text(
            """
            SELECT prediction, line, edge, side
            FROM vw_fact_player_prop_odds
            WHERE player_id = :player_id
              AND match_id = :match_id
              AND modelversion = :modelversion
            """
        ),
        {
            "player_id": above_player_id,
            "match_id": above_match_id,
            "modelversion": above_modelversion,
        },
    ).mappings().one()
    equal = isolated_connection.execute(
        text(
            """
            SELECT prediction, line, edge, side
            FROM vw_fact_player_prop_odds
            WHERE player_id = :player_id
              AND match_id = :match_id
              AND modelversion = :modelversion
            """
        ),
        {
            "player_id": equal_player_id,
            "match_id": equal_match_id,
            "modelversion": equal_modelversion,
        },
    ).mappings().one()

    assert float(above["prediction"]) == 10.0
    assert float(above["line"]) == 8.0
    assert float(above["edge"]) == 2.0
    assert above["side"] == "Over"
    assert float(equal["prediction"]) == 10.0
    assert float(equal["line"]) == 10.0
    assert float(equal["edge"]) == 0.0
    # At equality the prediction is classified as Over (prediction >= line).
    assert equal["side"] == "Over"