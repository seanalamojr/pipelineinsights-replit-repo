from datetime import date

import numpy as np
import pandas as pd

from features.transforms import rolling_by_category, rolling_stat


def test_rolling_stat_excludes_current_and_same_date_rows() -> None:
    frame = pd.DataFrame(
        [
            {
                "player_id": "p1",
                "event_date": date(2025, 1, 1),
                "tourney_date": date(2025, 1, 1),
                "match_num": 1,
                "match_id": "m1",
                "match_completed": True,
                "aces": 5,
                "surface": "Hard",
            },
            {
                "player_id": "p1",
                "event_date": date(2025, 1, 1),
                "tourney_date": date(2025, 1, 1),
                "match_num": 2,
                "match_id": "m2",
                "match_completed": True,
                "aces": 100,
                "surface": "Hard",
            },
            {
                "player_id": "p1",
                "event_date": date(2025, 1, 2),
                "tourney_date": date(2025, 1, 1),
                "match_num": 3,
                "match_id": "m3",
                "match_completed": True,
                "aces": 7,
                "surface": "Hard",
            },
        ]
    )

    result = rolling_stat(
        frame,
        "player_id",
        "event_date",
        "aces",
        3,
        "mean",
    )
    category = rolling_by_category(
        frame,
        "player_id",
        "event_date",
        "aces",
        "surface",
        3,
    )

    assert np.isnan(result.iloc[0])
    assert np.isnan(result.iloc[1])
    assert result.iloc[2] == 52.5
    assert category.iloc[2]["value"] == 52.5
    assert category.iloc[2]["n_observations"] == 2


def test_incomplete_matches_do_not_enter_rolling_history() -> None:
    frame = pd.DataFrame(
        [
            {
                "player_id": "p1",
                "event_date": date(2025, 1, 1),
                "tourney_date": date(2025, 1, 1),
                "match_num": 1,
                "match_id": "m1",
                "match_completed": True,
                "aces": 6,
            },
            {
                "player_id": "p1",
                "event_date": date(2025, 1, 2),
                "tourney_date": date(2025, 1, 1),
                "match_num": 2,
                "match_id": "m2",
                "match_completed": False,
                "aces": 1,
            },
            {
                "player_id": "p1",
                "event_date": date(2025, 1, 3),
                "tourney_date": date(2025, 1, 1),
                "match_num": 3,
                "match_id": "m3",
                "match_completed": True,
                "aces": 9,
            },
        ]
    )

    result = rolling_stat(
        frame,
        "player_id",
        "event_date",
        "aces",
        3,
        "mean",
    )

    assert result.iloc[1] == 6
    assert result.iloc[2] == 6