"""Seed clearly labeled synthetic tennis records for dashboard review.

The IDs use a demo prefix, so this loader can be run repeatedly without
overwriting future live records. It never claims to be a trained model.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

import yaml
from sqlalchemy import text

from config._schema import validate_sport_config
from db.connection import create_db_engine


PLAYERS = [
    ("demo_ava_chen", "Ava Chen", "ATP", "R", "US"),
    ("demo_mateo_silva", "Mateo Silva", "ATP", "R", "ES"),
    ("demo_jordan_brooks", "Jordan Brooks", "ATP", "L", "GB"),
    ("demo_noah_okafor", "Noah Okafor", "ATP", "R", "NG"),
    ("demo_sofia_rossi", "Sofia Rossi", "WTA", "R", "IT"),
    ("demo_mina_park", "Mina Park", "WTA", "L", "KR"),
    ("demo_elena_petrova", "Elena Petrova", "WTA", "R", "CA"),
    ("demo_layla_morgan", "Layla Morgan", "WTA", "R", "AU"),
]
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "tennis.yaml"
SPORT_CONFIG = validate_sport_config(
    yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
)
ACTIVE_STAT_TARGETS = tuple(SPORT_CONFIG.stat_targets)


def seed_demo() -> int:
    """Insert a compact, plausible slate for dashboard review."""

    today = date.today()
    # A stable daily timestamp makes re-running the demo loader idempotent.
    # Change DEMO_CAPTURED_AT in a future snapshot job when a new market
    # observation is intentionally being appended.
    captured_at = datetime.combine(
        today,
        datetime.min.time(),
        tzinfo=timezone.utc,
    ).replace(hour=12)
    engine = create_db_engine()
    matches: list[dict[str, object]] = []
    features: list[dict[str, object]] = []
    odds: list[dict[str, object]] = []
    predictions: list[dict[str, object]] = []

    pairings = [
        ("demo_match_01", 0, 1, 0),
        ("demo_match_02", 2, 3, 0),
        ("demo_match_03", 4, 5, 1),
        ("demo_match_04", 6, 7, -1),
    ]
    surfaces = ["Hard", "Clay", "Hard", "Grass"]
    tournaments = ["Hudson Open", "Madrid Classic", "Seoul 250", "Queens Warmup"]
    date_offsets = [0, 0, 1, -1]

    for match_index, (match_id, first_index, second_index, winner_index) in enumerate(
        pairings
    ):
        first_id = PLAYERS[first_index][0]
        second_id = PLAYERS[second_index][0]
        event_date = today + timedelta(days=date_offsets[match_index])
        for player_index, opponent_index in (
            (first_index, second_index),
            (second_index, first_index),
        ):
            player_id = PLAYERS[player_index][0]
            is_future = event_date > today
            is_winner = (
                None
                if is_future
                else winner_index >= 0
                and player_index == (first_index if winner_index == 0 else second_index)
            )
            base_games = 7 + ((player_index * 3 + match_index) % 5)
            base_aces = 3 + ((player_index + match_index * 2) % 7)
            base_double_faults = 1 + ((player_index + match_index) % 3)
            base_service_games = 18 + ((player_index * 2 + match_index) % 7)
            stat_values = {
                "aces": base_aces,
                "double_faults": base_double_faults,
                "service_games": base_service_games,
            }
            matches.append(
                {
                    "match_id": match_id,
                    "event_date": event_date,
                    "tournament": tournaments[match_index],
                    "surface": surfaces[match_index],
                    "round": "R32",
                    "player_id": player_id,
                    "opponent_id": PLAYERS[opponent_index][0],
                    "is_winner": is_winner,
                    "games_won": None if is_future else base_games,
                    "sets_won": None if is_future else (2 if is_winner else 1),
                    "aces": None if is_future else base_aces,
                    "service_games": None if is_future else base_service_games,
                    "double_faults": None if is_future else base_double_faults,
                    "minutes": (
                        None
                        if is_future
                        else 74 + (player_index * 8) + (match_index * 5)
                    ),
                }
            )
            for stat_target in ACTIVE_STAT_TARGETS:
                stat_value = stat_values[stat_target]
                features.append(
                    {
                        "player_id": player_id,
                        "match_id": match_id,
                        "event_date": event_date,
                        "sport": "tennis",
                        "feature_version": "tennis_features_demo_v1",
                        "stat_target": stat_target,
                        "rolling_mean_3": round(stat_value - 0.8, 4),
                        "rolling_std_3": 1.1 + (player_index % 3) * 0.2,
                        "rolling_mean_5": round(stat_value - 0.5, 4),
                        "rolling_std_5": 1.4 + (match_index % 2) * 0.2,
                        "rolling_mean_10": round(stat_value - 0.2, 4),
                        "rolling_std_10": 1.7,
                        "surface_rolling_mean": round(stat_value - 0.3, 4),
                        "surface_rolling_std": 1.2,
                        "head_to_head_average": round(stat_value - 0.6, 4),
                        "rest_days": 2 + ((player_index + match_index) % 4),
                        "opponent_strength": round(0.48 + player_index * 0.025, 4),
                        "feature_values": "{}",
                        "target_values": json.dumps({stat_target: stat_value}),
                    }
                )
            for book_index, book in enumerate(("Northstar", "LineLab")):
                prop_lines = {
                    "aces": round(5.5 + ((player_index + book_index) % 3), 1),
                    "double_faults": round(
                        2.5 + ((player_index + match_index + book_index) % 3) * 0.5,
                        1,
                    ),
                    "service_games": round(
                        18.5 + ((player_index + match_index + book_index) % 4),
                        1,
                    ),
                }
                for prop_type in ACTIVE_STAT_TARGETS:
                    line = prop_lines[prop_type]
                    over_price = -108 + book_index * 4
                    under_price = -112 + book_index * 3
                    odds.append(
                        {
                            "match_id": match_id,
                            "player_id": player_id,
                            "book": book,
                            "prop_type": prop_type,
                            "line": line,
                            "over_price": over_price,
                            "under_price": under_price,
                            "captured_at": captured_at,
                            "provider": "demo",
                            "provider_event_id": match_id,
                            "provider_market_id": (
                                f"{match_id}_{player_id}_{book}_{prop_type}"
                            ),
                            "provider_player_name": PLAYERS[player_index][1],
                            "provider_team_name": PLAYERS[player_index][1],
                            "resolved_at": captured_at,
                        }
                    )
            for prop_type in ACTIVE_STAT_TARGETS:
                projection_base = stat_values[prop_type] + 0.35
                for model_offset, model_version in (
                    (-0.25, f"baseline_v1_{prop_type}"),
                    (0.15, f"gbm_v1_{prop_type}"),
                    (0.0, f"ensemble_v1_{prop_type}"),
                ):
                    projection = round(projection_base + model_offset, 3)
                    predictions.append(
                        {
                            "player_id": player_id,
                            "match_id": match_id,
                            "sport": "tennis",
                            "prop_type": prop_type,
                            "prediction": projection,
                            "lowerci": round(max(0.0, projection - 1.35), 3),
                            "upperci": round(projection + 1.35, 3),
                            "modelversion": model_version,
                            "predictiontimestamp": captured_at,
                        }
                    )

    with engine.begin() as connection:
        # The demo namespace is synthetic and fully owned by this loader.
        # Clear it first so a config target cannot remain after being disabled.
        connection.execute(
            text(
                """
                DELETE FROM odds
                WHERE player_id LIKE :demo_prefix
                """
            ),
            {"demo_prefix": "demo_%"},
        )
        connection.execute(
            text(
                """
                DELETE FROM player_prop_predictions
                WHERE player_id LIKE :demo_prefix
                """
            ),
            {"demo_prefix": "demo_%"},
        )
        connection.execute(
            text(
                """
                DELETE FROM player_game_features
                WHERE player_id LIKE :demo_prefix
                """
            ),
            {"demo_prefix": "demo_%"},
        )
        connection.execute(
            text(
                """
                INSERT INTO players (player_id, full_name, tour, hand, country)
                VALUES (:player_id, :full_name, :tour, :hand, :country)
                ON CONFLICT (player_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    tour = EXCLUDED.tour,
                    hand = EXCLUDED.hand,
                    country = EXCLUDED.country
                """
            ),
            [
                {
                    "player_id": player_id,
                    "full_name": full_name,
                    "tour": tour,
                    "hand": hand,
                    "country": country,
                }
                for player_id, full_name, tour, hand, country in PLAYERS
            ],
        )
        connection.execute(
            text(
                """
                INSERT INTO matches (
                    match_id, event_date, tourney_date, tournament, surface, round, player_id,
                    opponent_id, is_winner, games_won, sets_won, aces,
                    double_faults, minutes, service_games
                )
                VALUES (
                    :match_id, :event_date, :event_date, :tournament, :surface, :round, :player_id,
                    :opponent_id, :is_winner, :games_won, :sets_won, :aces,
                    :double_faults, :minutes, :service_games
                )
                ON CONFLICT (match_id, player_id) DO UPDATE SET
                    event_date = EXCLUDED.event_date,
                    tourney_date = EXCLUDED.tourney_date,
                    tournament = EXCLUDED.tournament,
                    surface = EXCLUDED.surface,
                    opponent_id = EXCLUDED.opponent_id,
                    is_winner = EXCLUDED.is_winner,
                    games_won = EXCLUDED.games_won,
                    sets_won = EXCLUDED.sets_won,
                    aces = EXCLUDED.aces,
                    double_faults = EXCLUDED.double_faults,
                    minutes = EXCLUDED.minutes,
                    service_games = EXCLUDED.service_games
                """
            ),
            matches,
        )
        connection.execute(
            text(
                """
                INSERT INTO player_game_features (
                    player_id, match_id, event_date, sport, feature_version,
                    stat_target,
                    rolling_mean_3, rolling_std_3, rolling_mean_5, rolling_std_5,
                    rolling_mean_10, rolling_std_10, surface_rolling_mean,
                    surface_rolling_std, head_to_head_average, rest_days,
                    opponent_strength, feature_values, target_values
                )
                VALUES (
                    :player_id, :match_id, :event_date, :sport, :feature_version,
                    :stat_target,
                    :rolling_mean_3, :rolling_std_3, :rolling_mean_5, :rolling_std_5,
                    :rolling_mean_10, :rolling_std_10, :surface_rolling_mean,
                    :surface_rolling_std, :head_to_head_average, :rest_days,
                    :opponent_strength, CAST(:feature_values AS JSONB),
                    CAST(:target_values AS JSONB)
                )
                ON CONFLICT (player_id, match_id, stat_target, feature_version)
                DO UPDATE SET
                    event_date = EXCLUDED.event_date,
                    stat_target = EXCLUDED.stat_target,
                    feature_version = EXCLUDED.feature_version,
                    rolling_mean_3 = EXCLUDED.rolling_mean_3,
                    rolling_std_3 = EXCLUDED.rolling_std_3,
                    rolling_mean_5 = EXCLUDED.rolling_mean_5,
                    rolling_std_5 = EXCLUDED.rolling_std_5,
                    rolling_mean_10 = EXCLUDED.rolling_mean_10,
                    rolling_std_10 = EXCLUDED.rolling_std_10,
                    surface_rolling_mean = EXCLUDED.surface_rolling_mean,
                    surface_rolling_std = EXCLUDED.surface_rolling_std,
                    head_to_head_average = EXCLUDED.head_to_head_average,
                    rest_days = EXCLUDED.rest_days,
                    opponent_strength = EXCLUDED.opponent_strength,
                    feature_values = EXCLUDED.feature_values,
                    target_values = EXCLUDED.target_values
                """
            ),
            features,
        )
        connection.execute(
            text(
                """
                INSERT INTO odds (
                    match_id, player_id, book, prop_type, line, over_price,
                    under_price, captured_at, provider, provider_event_id,
                    provider_market_id, provider_player_name, provider_team_name,
                    resolved_at
                )
                VALUES (
                    :match_id, :player_id, :book, :prop_type, :line, :over_price,
                    :under_price, :captured_at, :provider, :provider_event_id,
                    :provider_market_id, :provider_player_name, :provider_team_name,
                    :resolved_at
                )
                ON CONFLICT (
                    provider, provider_event_id, player_id, book, prop_type,
                    line, captured_at
                )
                DO UPDATE SET
                    over_price = EXCLUDED.over_price,
                    under_price = EXCLUDED.under_price,
                    captured_at = EXCLUDED.captured_at,
                    provider_market_id = EXCLUDED.provider_market_id,
                    provider_player_name = EXCLUDED.provider_player_name,
                    provider_team_name = EXCLUDED.provider_team_name,
                    resolved_at = EXCLUDED.resolved_at
                """
            ),
            odds,
        )
        connection.execute(
            text(
                """
                INSERT INTO player_prop_predictions (
                    player_id, match_id, sport, prop_type, prediction, lowerci,
                    upperci, modelversion, predictiontimestamp
                )
                VALUES (
                    :player_id, :match_id, :sport, :prop_type, :prediction, :lowerci,
                    :upperci, :modelversion, :predictiontimestamp
                )
                ON CONFLICT (player_id, match_id, prop_type, modelversion)
                DO UPDATE SET
                    prediction = EXCLUDED.prediction,
                    lowerci = EXCLUDED.lowerci,
                    upperci = EXCLUDED.upperci,
                    predictiontimestamp = EXCLUDED.predictiontimestamp
                """
            ),
            predictions,
        )

    engine.dispose()
    return len(predictions)


if __name__ == "__main__":
    try:
        count = seed_demo()
        print(
            "Demo data loaded: "
            f"{len(PLAYERS)} players, 8 match-player rows, {count} predictions"
        )
    except Exception as error:
        raise SystemExit(f"Demo data load failed: {error}") from error