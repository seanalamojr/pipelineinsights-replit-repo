from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from features.build_features import (
    assert_current_target_perturbation_safe,
    assert_first_match_features_are_null,
    assert_no_target_correlation,
    assert_sampled_recomputation,
    build_feature_frame,
)


def _synthetic_matches() -> pd.DataFrame:
    rng = np.random.default_rng(20250916)
    players = ["p1", "p2", "p3", "p4"]
    heights = {"p1": 188, "p2": 183, "p3": 196, "p4": 179}
    pairs = [
        ("p1", "p2"),
        ("p3", "p4"),
        ("p1", "p3"),
        ("p2", "p4"),
        ("p1", "p4"),
        ("p2", "p3"),
    ]
    rows: list[dict[str, object]] = []
    start = date(2023, 1, 1)
    for match_number in range(80):
        first, second = pairs[match_number % len(pairs)]
        match_id = f"2023-T-{match_number}"
        event_date = start + timedelta(days=match_number)
        surface = ["Hard", "Clay", "Grass"][match_number % 3]
        completed = match_number % 17 != 0
        first_aces = int(rng.poisson(7))
        second_aces = int(rng.poisson(6))
        if match_number % 19 == 0:
            first_aces = None
        for player, opponent, aces, opponent_aces, winner in [
            (first, second, first_aces, second_aces, True),
            (second, first, second_aces, first_aces, False),
        ]:
            serve_points = int(rng.integers(45, 100))
            rows.append(
                {
                    "match_id": match_id,
                    "player_id": player,
                    "opponent_id": opponent,
                    "event_date": event_date,
                    "tourney_date": event_date,
                    "tournament": "Synthetic Open",
                    "surface": surface,
                    "round": "R32",
                    "match_num": match_number,
                    "match_completed": completed,
                    "is_winner": winner,
                    "aces": aces,
                    "double_faults": int(rng.poisson(3)),
                    "minutes": int(rng.integers(60, 180)),
                    "service_games": int(rng.integers(8, 16)),
                    "serve_points": serve_points,
                    "first_serves_in": int(
                        round(serve_points * rng.uniform(0.48, 0.76))
                    ),
                    "best_of": 5 if match_number % 23 == 0 else 3,
                    "tourney_level": ["A", "M", "G"][match_number % 3],
                    "player_rank": int(rng.integers(1, 150)),
                    "opponent_rank": int(rng.integers(1, 150)),
                    "player_height_cm": heights[player],
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def feature_case():
    raw_config = yaml.safe_load(
        Path("config/tennis.yaml").read_text(encoding="utf-8")
    )
    matches = _synthetic_matches()
    features, feature_columns = build_feature_frame(matches, raw_config)
    return matches, features, raw_config, feature_columns


def test_random_50_rows_recompute_from_strictly_prior_matches(
    feature_case,
) -> None:
    matches, features, raw_config, _ = feature_case
    assert_sampled_recomputation(
        matches, features, raw_config, sample_size=50
    )


def test_first_match_rolling_features_are_null(feature_case) -> None:
    matches, features, raw_config, feature_columns = feature_case
    assert_first_match_features_are_null(
        matches, features, feature_columns, raw_config
    )


def test_inflating_current_aces_cannot_change_current_features(
    feature_case,
) -> None:
    matches, features, raw_config, feature_columns = feature_case
    assert_current_target_perturbation_safe(
        matches, features, raw_config, feature_columns
    )


def test_no_feature_has_suspicious_target_correlation(feature_case) -> None:
    _, features, _, feature_columns = feature_case
    assert_no_target_correlation(features, feature_columns, threshold=0.99)