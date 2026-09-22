import os
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from etl.odds.snapshots import (
    load_snapshot,
    normalize_player_name,
    normalize_tour,
    name_alias_collisions,
    prepare_snapshot,
    pivot_selections,
    resolve_player_name,
)


def _source_row(**overrides: str) -> dict[str, str]:
    row = {
        "captured_at": "2026-09-17T23:00:00Z",
        "fixture_id": "fixture-1",
        "game_id": "game-1",
        "league": "ATP",
        "tournament": "Test Open",
        "start_date": "2026-09-18T14:00:00Z",
        "status": "scheduled",
        "home_player": "Novak Djokovic",
        "away_player": "Jannik Sinner",
        "sportsbook": "Book A",
        "market_id": "market-1",
        "market": "Aces",
        "player_id": "provider-player-1",
        "player_name": "Novak Djokovic",
        "selection": "Over 5.5",
        "normalized_selection": "Over",
        "selection_line": "5.5",
        "points": "5.5",
        "price": "-110",
        "is_main": "true",
        "grouping_key": "group-1",
        "odds_id": "odds-over-1",
        "odds_timestamp": "2026-09-17T23:00:00Z",
    }
    row.update(overrides)
    return row


def _players() -> list[dict[str, str]]:
    return [
        {"player_id": "p-djokovic", "full_name": "Novak Djokovic"},
        {"player_id": "p-sinner", "full_name": "Jannik Sinner"},
    ]


def _matches() -> list[dict[str, object]]:
    return [
        {
            "match_id": "match-1",
            "event_date": date(2026, 9, 18),
            "tournament": "Test Open",
            "player_id": "p-djokovic",
            "opponent_id": "p-sinner",
        },
        {
            "match_id": "match-1",
            "event_date": date(2026, 9, 18),
            "tournament": "Test Open",
            "player_id": "p-sinner",
            "opponent_id": "p-djokovic",
        },
    ]


def test_over_and_under_rows_pivot_to_one_odds_row() -> None:
    rows = [
        _source_row(odds_id="odds-over-1", price="-110"),
        _source_row(
            selection="Under 5.5",
            normalized_selection="Under",
            price="-115",
            odds_id="odds-under-1",
        ),
    ]

    pivoted = pivot_selections(rows)

    assert len(pivoted) == 1
    assert pivoted[0]["line"] == 5.5
    assert pivoted[0]["over_price"] == -110
    assert pivoted[0]["under_price"] == -115
    assert pivoted[0]["provider_odds_id"] == "odds-over-1|odds-under-1"


def test_pivot_export_rows_are_auto_detected_and_preserve_provider_identity() -> None:
    row = {
        "captured_at": "2026-09-17T23:00:00Z",
        "fixture_id": "provider-fixture-1",
        "league": "WTA",
        "tournament": "Test Open",
        "start_date": "2026-09-18T14:00:00Z",
        "home_player": "Unknown Home",
        "away_player": "Unknown Away",
        "book": "DraftKings",
        "market_id": "player_break_points_won",
        "market": "Player Break Points Won",
        "provider_player_name": "Unknown Home",
        "provider_player_id": "provider-player-1",
        "normalized_selection": "unknown_home",
        "line": "0.5",
        "is_main": "True",
        "over_price": "-110",
        "under_price": "105",
        "over_odds_id": "provider-over-1",
        "under_odds_id": "provider-under-1",
        "grouping_key": "unknown_home:0.5",
    }

    prepared = prepare_snapshot(
        [row],
        players=[],
        matches=[],
        provider="attached-wta-archive",
    )

    assert prepared.report.source_rows == 1
    assert prepared.report.eligible_rows == 2
    assert prepared.report.pivot_rows == 1
    assert len(prepared.rows) == 1
    assert prepared.rows[0]["provider"] == "attached-wta-archive"
    assert prepared.rows[0]["provider_event_id"] == "provider-fixture-1"
    assert prepared.rows[0]["provider_player_id"] == "provider-player-1"
    assert prepared.rows[0]["provider_odds_id"] == (
        "provider-over-1|provider-under-1"
    )
    assert prepared.rows[0]["prop_type"] == "break_points_won"
    assert prepared.rows[0]["player_id"] is None
    assert prepared.rows[0]["match_id"] is None


def test_pivot_export_supports_one_sided_rows_without_fabricating_ids() -> None:
    row = {
        "captured_at": "2026-09-17T23:00:00Z",
        "fixture_id": "provider-fixture-1",
        "league": "WTA",
        "tournament": "Test Open",
        "start_date": "2026-09-18T14:00:00Z",
        "home_player": "Unknown Home",
        "away_player": "Unknown Away",
        "book": "DraftKings",
        "market_id": "player_games_won",
        "market": "Player Games Won",
        "provider_player_name": "Unknown Home",
        "provider_player_id": "provider-player-1",
        "normalized_selection": "unknown_home",
        "line": "11.5",
        "is_main": "True",
        "over_price": "",
        "under_price": "100",
        "over_odds_id": "",
        "under_odds_id": "provider-under-1",
    }

    prepared = prepare_snapshot(
        [row],
        players=[],
        matches=[],
        provider="attached-wta-archive",
    )

    assert prepared.report.pivot_rows == 1
    assert prepared.rows[0]["provider_odds_id"] == "provider-under-1"
    assert prepared.rows[0]["provider_player_id"] == "provider-player-1"
    assert prepared.rows[0]["over_price"] is None
    assert prepared.rows[0]["under_price"] == 100


def test_name_normalization_handles_initial_surname_and_accents() -> None:
    players = [{"player_id": "p", "full_name": "Éléna Rybakina"}]

    assert normalize_player_name("Rybakina E.") == "rybakina e"
    assert resolve_player_name("Rybakina E.", players) == ("p", "normalized")
    assert resolve_player_name("E. Rybakina", players) == ("p", "normalized")
    assert resolve_player_name("Elena Rybakina", players) == ("p", "normalized")


def test_wta_row_does_not_resolve_identically_named_atp_player() -> None:
    row = _source_row(
        league="WTA",
        home_player="Shared Name",
        away_player="WTA Opponent",
        player_name="Shared Name",
    )
    players = [
        {"player_id": "atp-shared", "full_name": "Shared Name", "tour": "ATP"},
        {"player_id": "wta-opponent", "full_name": "WTA Opponent", "tour": "WTA"},
    ]
    matches = [
        {
            "match_id": "atp-match",
            "event_date": date(2026, 9, 18),
            "tournament": "Test Open",
            "player_id": "atp-shared",
            "opponent_id": "wta-opponent",
        }
    ]

    prepared = prepare_snapshot(
        [row],
        players=players,
        matches=matches,
        provider="attached-wta-archive",
    )

    assert normalize_tour("WTA Tour") == "WTA"
    assert prepared.rows[0]["player_id"] is None
    assert prepared.rows[0]["match_id"] is None
    assert prepared.report.unresolved_name_rows == 1


def test_name_normalization_handles_compound_and_three_token_surnames() -> None:
    players = [
        {"player_id": "p-compound", "full_name": "Aaron Gil Garcia"},
        {"player_id": "p-three", "full_name": "Maria Lopez Alvarez"},
    ]

    assert resolve_player_name("Gil Garcia A.", players) == (
        "p-compound",
        "normalized",
    )
    assert resolve_player_name("A. Gil Garcia", players) == (
        "p-compound",
        "normalized",
    )
    assert resolve_player_name("Lopez Alvarez M.", players) == (
        "p-three",
        "normalized",
    )
    assert resolve_player_name("M. Lopez Alvarez", players) == (
        "p-three",
        "normalized",
    )


def test_full_table_alias_collisions_are_reported_and_remain_unresolved() -> None:
    players = [
        {"player_id": "p-aaron", "full_name": "Aaron Gil Garcia", "tour": "ATP"},
        {"player_id": "p-alex", "full_name": "Alex Gil Garcia", "tour": "ATP"},
        {"player_id": "p-opponent", "full_name": "Test Opponent", "tour": "ATP"},
    ]

    collisions = name_alias_collisions(players)
    prepared = prepare_snapshot(
        [
            _source_row(
                player_name="Gil Garcia A.",
                home_player="Gil Garcia A.",
                away_player="Test Opponent",
            )
        ],
        players=players,
        matches=[],
        provider="test-provider",
    )

    collision_by_alias = {item.alias: item.player_ids for item in collisions}
    assert collision_by_alias["gil garcia a"] == ("p-aaron", "p-alex")
    assert prepared.report.alias_collisions == collisions
    assert prepared.rows[0]["player_id"] is None
    assert prepared.report.unresolved_name_rows == 1


def test_wta_archive_and_atp_reference_coverage_is_reported_without_cross_tour_match() -> None:
    players = [
        {"player_id": "atp-shared", "full_name": "Shared Name", "tour": "ATP"},
    ]
    prepared = prepare_snapshot(
        [
            _source_row(
                league="WTA",
                player_name="Shared Name",
                home_player="Shared Name",
                away_player="Other Player",
            )
        ],
        players=players,
        matches=[],
        provider="attached-wta-archive",
    )

    assert prepared.report.source_tours == ("WTA",)
    assert prepared.report.reference_tours == ("ATP",)
    assert prepared.rows[0]["player_id"] is None
    assert prepared.report.unresolved_name_rows == 1


def test_compound_name_fixture_reports_normalized_match_rate() -> None:
    rows = [
        _source_row(
            player_name="Gil Garcia A.",
            home_player="Gil Garcia A.",
            away_player="Maria Lopez Alvarez",
        )
    ]
    matches = [
        {
            "match_id": "match-compound",
            "event_date": date(2026, 9, 18),
            "tournament": "Test Open",
            "player_id": "p-compound",
            "opponent_id": "p-three",
        }
    ]
    prepared = prepare_snapshot(
        rows,
        players=[
            {"player_id": "p-compound", "full_name": "Aaron Gil Garcia"},
            {"player_id": "p-three", "full_name": "Maria Lopez Alvarez"},
        ],
        matches=matches,
        provider="test-provider",
    )

    assert prepared.report.normalized_name_matches == 1
    assert prepared.report.normalized_match_rate == pytest.approx(100.0)


def test_unresolved_provider_name_is_reported_and_row_is_retained() -> None:
    row = _source_row(
        player_name="Unknown Player",
        home_player="Unknown Player",
        away_player="Another Unknown",
    )

    prepared = prepare_snapshot(
        [row],
        players=_players(),
        matches=_matches(),
        provider="test-provider",
    )

    assert len(prepared.rows) == 1
    assert prepared.rows[0]["player_id"] is None
    assert prepared.report.unresolved_name_rows == 1
    assert prepared.report.unresolved_names[0].provider_player_name == "Unknown Player"


def test_post_start_time_rows_are_skipped() -> None:
    row = _source_row(
        captured_at="2026-09-18T14:00:00Z",
        start_date="2026-09-18T14:00:00Z",
    )

    prepared = prepare_snapshot(
        [row],
        players=_players(),
        matches=_matches(),
        provider="test-provider",
    )

    assert prepared.rows == ()
    assert prepared.report.skipped_post_start_rows == 1


@pytest.mark.integration
def test_running_loader_twice_does_not_duplicate_rows() -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured for odds integration tests")

    from db.connection import get_engine

    rows = [
        _source_row(odds_id="db-test-over", price="-110"),
        _source_row(
            selection="Under 5.5",
            normalized_selection="Under",
            price="-115",
            odds_id="db-test-under",
        ),
    ]
    connection = get_engine().connect()
    transaction = connection.begin()
    try:
        connection.execute(
            text(
                """
                INSERT INTO players (player_id, full_name)
                VALUES ('odds_checkpoint11_p1', 'Novak Djokovic'),
                       ('odds_checkpoint11_p2', 'Jannik Sinner')
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO matches (
                    match_id, event_date, tournament, player_id, opponent_id,
                    is_winner, tourney_date
                )
                VALUES
                    ('odds_checkpoint11_match', '2026-09-18', 'Test Open',
                     'odds_checkpoint11_p1', 'odds_checkpoint11_p2', NULL, '2026-09-18'),
                    ('odds_checkpoint11_match', '2026-09-18', 'Test Open',
                     'odds_checkpoint11_p2', 'odds_checkpoint11_p1', NULL, '2026-09-18')
                """
            )
        )
        path = Path("test_odds_checkpoint11.csv")
        import csv

        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        try:
            first = load_snapshot(
                connection,
                path,
                provider="test-checkpoint11",
            )
            second = load_snapshot(
                connection,
                path,
                provider="test-checkpoint11",
            )
        finally:
            path.unlink()

        count = connection.execute(
            text(
                """
                SELECT COUNT(*), MIN(provider_player_id)
                FROM odds
                WHERE provider = 'test-checkpoint11'
                  AND provider_event_id = 'fixture-1'
                """
            )
        ).one()
        assert first.rows_written == 1
        assert second.rows_written == 1
        assert count[0] == 1
        assert count[1] == "provider-player-1"
        transaction.rollback()
    finally:
        if transaction.is_active:
            transaction.rollback()
        connection.close()