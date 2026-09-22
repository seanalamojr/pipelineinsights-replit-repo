"""Build config-driven, leakage-safe rows in player_game_features."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
import json
import math
from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd
import yaml

from config._schema import validate_sport_config
from features.transforms import (
    career_to_date,
    days_since_previous,
    head_to_head,
    opponent_rolling,
    rolling_by_category,
    rolling_stat,
)


DEFAULT_CONFIG = Path("config/tennis.yaml")
IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
KEY_COLUMNS = [
    "player_id",
    "match_id",
    "stat_target",
    "feature_version",
]
METADATA_COLUMNS = [
    "player_id",
    "match_id",
    "event_date",
    "sport",
    "feature_version",
    "stat_target",
]


@dataclass(frozen=True)
class AuditResult:
    sampled_recomputation: bool
    first_match_null: bool
    current_target_perturbation: bool
    correlation_guard: bool
    max_absolute_target_correlation: float | None


def load_feature_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    validated = validate_sport_config(raw)
    if not validated.features.targets:
        raise ValueError(f"{path}: features.targets must define at least one target")
    if validated.features.date_tie_policy != "prior_event_dates_only":
        raise ValueError(
            "Only date_tie_policy=prior_event_dates_only is leakage-safe with "
            "estimated event dates"
        )
    return raw


def load_match_frame(connection: object) -> pd.DataFrame:
    """Read real ATP player-match facts and static player context."""

    query = """
        SELECT
            match_row.match_id,
            match_row.player_id,
            match_row.opponent_id,
            match_row.event_date,
            COALESCE(match_row.tourney_date, match_row.event_date) AS tourney_date,
            match_row.tournament,
            match_row.surface,
            match_row.round,
            match_row.match_num,
            match_row.match_completed,
            match_row.is_winner,
            match_row.minutes,
            match_row.aces,
            match_row.double_faults,
            match_row.service_games,
            match_row.serve_points,
            match_row.first_serves_in,
            match_row.best_of,
            match_row.tourney_level,
            match_row.player_rank,
            match_row.opponent_rank,
            player.height_cm AS player_height_cm
        FROM matches AS match_row
        JOIN players AS player
          ON player.player_id = match_row.player_id
        WHERE player.tour = 'ATP'
          AND match_row.player_id NOT LIKE 'demo_%%'
        ORDER BY
            match_row.event_date,
            COALESCE(match_row.tourney_date, match_row.event_date),
            match_row.match_num,
            match_row.match_id,
            match_row.player_id
    """
    return pd.read_sql_query(query, connection)


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = pd.to_numeric(denominator, errors="coerce")
    numerator = pd.to_numeric(numerator, errors="coerce")
    ratio = numerator / denominator.where(denominator > 0)
    return ratio.replace([np.inf, -np.inf], np.nan)


def _add_conceded_stat(
    frame: pd.DataFrame,
    *,
    source_column: str,
    output_column: str,
) -> None:
    lookup = {
        (row.match_id, row.player_id): getattr(row, source_column)
        for row in frame.itertuples(index=False)
    }
    frame[output_column] = [
        lookup.get((row.match_id, row.opponent_id), np.nan)
        for row in frame.itertuples(index=False)
    ]


def _normalizable(value: object) -> object:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.date()
    return value


def _feature_json(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    return [
        {column: _normalizable(row[column]) for column in columns}
        for row in frame[columns].to_dict(orient="records")
    ]


def build_target_features(
    matches: pd.DataFrame,
    *,
    sport: str,
    feature_version: str,
    minimum_history: int,
    rolling_windows: Iterable[int],
    target_name: str,
    definition: Mapping[str, Any],
) -> tuple[pd.DataFrame, list[str]]:
    """Build one target's rows exclusively from configured definitions."""

    frame = matches.copy().reset_index(drop=True)
    frame["event_date"] = pd.to_datetime(frame["event_date"])
    frame["tourney_date"] = pd.to_datetime(frame["tourney_date"])
    target_column = str(definition["source_column"])
    feature_columns: list[str] = []

    rolling = definition["rolling"]
    for aggregation in rolling["aggregations"]:
        for window in rolling_windows:
            output = f"rolling_{aggregation}_{window}"
            frame[output] = rolling_stat(
                frame,
                "player_id",
                "event_date",
                target_column,
                int(window),
                aggregation,
            )
            feature_columns.append(output)

    category = definition["category"]
    category_result = rolling_by_category(
        frame,
        "player_id",
        "event_date",
        str(category["source_column"]),
        str(category["category_column"]),
        int(category["window"]),
    )
    category_value = str(category["value_output"])
    category_count = str(category["count_output"])
    frame[category_value] = category_result["value"]
    frame[category_count] = category_result["n_observations"]
    feature_columns.extend([category_value, category_count])

    rate = definition["rate"]
    rate_input = "__configured_rate"
    frame[rate_input] = _safe_ratio(
        frame[str(rate["numerator_column"])],
        frame[str(rate["denominator_column"])],
    )
    rate_output = str(rate["output"])
    frame[rate_output] = rolling_stat(
        frame,
        "player_id",
        "event_date",
        rate_input,
        int(rate["window"]),
        "mean",
    )
    feature_columns.append(rate_output)

    percentage = definition["percentage"]
    percentage_input = "__configured_percentage"
    frame[percentage_input] = _safe_ratio(
        frame[str(percentage["numerator_column"])],
        frame[str(percentage["denominator_column"])],
    )
    percentage_output = str(percentage["output"])
    frame[percentage_output] = rolling_stat(
        frame,
        "player_id",
        "event_date",
        percentage_input,
        int(percentage["window"]),
        "mean",
    )
    feature_columns.append(percentage_output)

    rest_output = str(definition["rest"]["output"])
    frame[rest_output] = days_since_previous(
        frame, "player_id", "event_date"
    )
    feature_columns.append(rest_output)

    h2h_config = definition["head_to_head"]
    h2h = head_to_head(
        frame,
        "player_id",
        "opponent_id",
        "event_date",
        str(h2h_config["source_column"]),
    )
    h2h_average = str(h2h_config["average_output"])
    h2h_matches = str(h2h_config["matches_output"])
    h2h_win_rate = str(h2h_config["win_rate_output"])
    frame[h2h_average] = h2h["stat_average"]
    frame[h2h_matches] = h2h["prior_matches"]
    frame[h2h_win_rate] = h2h["win_rate"]
    feature_columns.extend([h2h_average, h2h_matches, h2h_win_rate])

    opponent = definition["opponent"]
    conceded_input = "__configured_conceded"
    _add_conceded_stat(
        frame,
        source_column=str(opponent["conceded_source_column"]),
        output_column=conceded_input,
    )
    opponent_result = opponent_rolling(
        frame,
        "player_id",
        "opponent_id",
        "match_id",
        "event_date",
        conceded_input,
        int(opponent["window"]),
    )
    opponent_output = str(opponent["output"])
    frame[opponent_output] = opponent_result["value"]
    feature_columns.append(opponent_output)

    career = definition["career"]
    career_result = career_to_date(
        frame,
        "player_id",
        "event_date",
        str(career["source_column"]),
    )
    career_output = str(career["output"])
    history_output = str(career["count_output"])
    frame[career_output] = career_result["value"]
    frame[history_output] = career_result["n_observations"]
    feature_columns.extend([career_output, history_output])

    for output, source in definition["context"].items():
        frame[str(output)] = frame[str(source)]
        feature_columns.append(str(output))

    for output, derived in definition["derived"].items():
        frame[str(output)] = (
            pd.to_numeric(frame[str(derived["left_column"])], errors="coerce")
            - pd.to_numeric(frame[str(derived["right_column"])], errors="coerce")
        )
        feature_columns.append(str(output))

    feature_columns = list(dict.fromkeys(feature_columns))
    output = frame[
        ["player_id", "match_id", "event_date", "match_completed", target_column]
        + feature_columns
    ].copy()
    output["sport"] = sport
    output["feature_version"] = feature_version
    output["stat_target"] = target_name
    output["target_value"] = pd.to_numeric(
        output[target_column], errors="coerce"
    )
    output["has_sufficient_history"] = (
        output[history_output] >= minimum_history
    )
    output["is_training_eligible"] = (
        output["has_sufficient_history"]
        & output["match_completed"].fillna(False)
        & output["target_value"].notna()
    )
    output["feature_values"] = _feature_json(output, feature_columns)
    output["target_values"] = [
        {target_name: _normalizable(value)}
        for value in output["target_value"]
    ]
    output["event_date"] = output["event_date"].dt.date
    return (
        output[
            METADATA_COLUMNS
            + feature_columns
            + [
                "target_value",
                "has_sufficient_history",
                "is_training_eligible",
                "feature_values",
                "target_values",
            ]
        ],
        feature_columns,
    )


def build_feature_frame(
    matches: pd.DataFrame,
    raw_config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    validated = validate_sport_config(dict(raw_config))
    feature_config = raw_config["features"]
    definitions = feature_config["targets"]
    frames: list[pd.DataFrame] = []
    feature_columns: dict[str, list[str]] = {}
    for target_name, definition in definitions.items():
        target_frame, columns = build_target_features(
            matches,
            sport=validated.sport,
            feature_version=validated.features.feature_version,
            minimum_history=validated.features.minimum_history,
            rolling_windows=validated.features.rolling_windows,
            target_name=target_name,
            definition=definition,
        )
        frames.append(target_frame)
        feature_columns[target_name] = columns
    return pd.concat(frames, ignore_index=True), feature_columns


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for raw in frame.to_dict(orient="records"):
        record = {key: _normalizable(value) for key, value in raw.items()}
        record["feature_values"] = json.dumps(record["feature_values"])
        record["target_values"] = json.dumps(record["target_values"])
        records.append(record)
    return records


def store_feature_rows(
    connection: object,
    frame: pd.DataFrame,
    *,
    batch_size: int = 2_000,
) -> None:
    from sqlalchemy import text

    if frame.empty:
        return
    columns = list(frame.columns)
    if any(not IDENTIFIER.fullmatch(column) for column in columns):
        raise ValueError("Feature output contains an invalid SQL identifier")

    existing_columns = {
        row[0]
        for row in connection.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'player_game_features'
                """
            )
        )
    }
    required_columns = set(
        METADATA_COLUMNS
        + [
            "target_value",
            "has_sufficient_history",
            "is_training_eligible",
            "feature_values",
            "target_values",
        ]
    )
    missing = required_columns - existing_columns
    if missing:
        raise RuntimeError(
            "Run database migrations before building features; missing columns: "
            f"{sorted(missing)}"
        )
    # Config can add sport- or target-specific values without a migration.
    # Persist every feature in feature_values and mirror only known typed
    # columns at the top level for query-friendly compatibility.
    columns = [column for column in columns if column in existing_columns]

    versions = frame[
        ["sport", "feature_version", "stat_target"]
    ].drop_duplicates()
    for row in versions.itertuples(index=False):
        connection.execute(
            text(
                """
                DELETE FROM player_game_features
                WHERE sport = :sport
                  AND feature_version = :feature_version
                  AND stat_target = :stat_target
                  AND player_id NOT LIKE 'demo_%%'
                """
            ),
            {
                "sport": row.sport,
                "feature_version": row.feature_version,
                "stat_target": row.stat_target,
            },
        )

    column_sql = ", ".join(columns)
    values_sql = ", ".join(
        (
            f"CAST(:{column} AS JSONB)"
            if column in {"feature_values", "target_values"}
            else f":{column}"
        )
        for column in columns
    )
    updates = ", ".join(
        f"{column} = EXCLUDED.{column}"
        for column in columns
        if column not in KEY_COLUMNS
    )
    statement = text(
        f"""
        INSERT INTO player_game_features ({column_sql})
        VALUES ({values_sql})
        ON CONFLICT (player_id, match_id, stat_target, feature_version)
        DO UPDATE SET {updates}
        """
    )
    rows = _records(frame)
    for start in range(0, len(rows), batch_size):
        connection.execute(statement, rows[start : start + batch_size])


def load_stored_feature_rows(
    connection: object,
    raw_config: Mapping[str, Any],
    feature_columns: Mapping[str, list[str]],
) -> pd.DataFrame:
    from sqlalchemy import text

    validated = validate_sport_config(dict(raw_config))
    configured_columns = list(
        dict.fromkeys(
            column
            for columns in feature_columns.values()
            for column in columns
        )
    )
    columns = (
        METADATA_COLUMNS
        + configured_columns
        + [
            "target_value",
            "has_sufficient_history",
            "is_training_eligible",
            "feature_values",
            "target_values",
        ]
    )
    if any(not IDENTIFIER.fullmatch(column) for column in columns):
        raise ValueError("Feature output contains an invalid SQL identifier")
    target_names = list(feature_columns)
    target_params = {
        f"target_{index}": target for index, target in enumerate(target_names)
    }
    target_placeholders = ", ".join(f":{key}" for key in target_params)
    from sqlalchemy import text as sqlalchemy_text

    available_columns = {
        row[0]
        for row in connection.execute(
            sqlalchemy_text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'player_game_features'
                """
            )
        )
    }
    selected_columns = [column for column in columns if column in available_columns]
    statement = text(
        f"""
        SELECT {", ".join(selected_columns)}
        FROM player_game_features
        WHERE sport = :sport
          AND feature_version = :feature_version
          AND stat_target IN ({target_placeholders})
          AND player_id NOT LIKE 'demo_%%'
        ORDER BY event_date, match_id, player_id, stat_target
        """
    )
    stored = pd.read_sql_query(
        statement,
        connection,
        params={
            "sport": validated.sport,
            "feature_version": validated.features.feature_version,
            **target_params,
        },
    )
    payloads = [
        json.loads(payload) if isinstance(payload, str) else (payload or {})
        for payload in stored["feature_values"]
    ]
    for column in configured_columns:
        if column not in stored:
            stored[column] = [
                _normalizable(payload.get(column)) for payload in payloads
            ]
    return stored


def _ordered_prior(
    matches: pd.DataFrame,
    row: pd.Series,
    *,
    player_id: object,
) -> pd.DataFrame:
    prior = matches[
        (matches["player_id"] == player_id)
        & (pd.to_datetime(matches["event_date"]) < pd.Timestamp(row["event_date"]))
    ].copy()
    return prior.sort_values(
        ["event_date", "tourney_date", "match_num", "match_id"],
        kind="mergesort",
    )


def _expected_aggregate(
    values: pd.Series,
    *,
    window: int | None,
    aggregation: str,
) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if window is not None:
        clean = clean.tail(window)
    if clean.empty:
        return np.nan
    if aggregation == "mean":
        return float(clean.mean())
    if aggregation == "std":
        return float(clean.std(ddof=1)) if len(clean) >= 2 else np.nan
    if aggregation == "median":
        return float(clean.median())
    raise ValueError(aggregation)


def _same_number(actual: object, expected: object) -> bool:
    if pd.isna(actual) and pd.isna(expected):
        return True
    if isinstance(actual, (str, bool)) or isinstance(expected, (str, bool)):
        return actual == expected
    return bool(np.isclose(float(actual), float(expected), rtol=1e-9, atol=5e-4))


def assert_sampled_recomputation(
    matches: pd.DataFrame,
    features: pd.DataFrame,
    raw_config: Mapping[str, Any],
    *,
    sample_size: int = 50,
) -> None:
    """Independently recompute configured historical features for sampled rows."""

    working = matches.copy()
    working["event_date"] = pd.to_datetime(working["event_date"])
    working["tourney_date"] = pd.to_datetime(working["tourney_date"])
    sampled = features.sample(
        n=min(sample_size, len(features)),
        random_state=20250916,
    )
    source_lookup = working.set_index(["match_id", "player_id"], drop=False)
    config = raw_config["features"]

    for feature_row in sampled.to_dict(orient="records"):
        source = source_lookup.loc[
            (feature_row["match_id"], feature_row["player_id"])
        ]
        definition = config["targets"][feature_row["stat_target"]]
        target = definition["source_column"]
        prior = _ordered_prior(
            working, source, player_id=source["player_id"]
        )
        eligible = prior[prior["match_completed"].fillna(False)]

        for aggregation in definition["rolling"]["aggregations"]:
            for window in config["rolling_windows"]:
                column = f"rolling_{aggregation}_{window}"
                expected = _expected_aggregate(
                    eligible[target],
                    window=int(window),
                    aggregation=aggregation,
                )
                assert _same_number(feature_row[column], expected), column

        category = definition["category"]
        category_history = eligible[
            eligible[category["category_column"]]
            == source[category["category_column"]]
        ]
        category_expected = _expected_aggregate(
            category_history[category["source_column"]],
            window=int(category["window"]),
            aggregation="mean",
        )
        assert _same_number(
            feature_row[category["value_output"]], category_expected
        )
        category_count = (
            pd.to_numeric(
                category_history[category["source_column"]], errors="coerce"
            )
            .dropna()
            .tail(int(category["window"]))
            .shape[0]
        )
        assert int(feature_row[category["count_output"]]) == category_count

        rate = definition["rate"]
        rate_values = _safe_ratio(
            eligible[rate["numerator_column"]],
            eligible[rate["denominator_column"]],
        )
        assert _same_number(
            feature_row[rate["output"]],
            _expected_aggregate(
                rate_values, window=int(rate["window"]), aggregation="mean"
            ),
        )

        percentage = definition["percentage"]
        percentage_values = _safe_ratio(
            eligible[percentage["numerator_column"]],
            eligible[percentage["denominator_column"]],
        )
        assert _same_number(
            feature_row[percentage["output"]],
            _expected_aggregate(
                percentage_values,
                window=int(percentage["window"]),
                aggregation="mean",
            ),
        )

        expected_rest = np.nan
        if not prior.empty:
            expected_rest = (
                pd.Timestamp(source["event_date"])
                - pd.Timestamp(prior["event_date"].max())
            ).days
        assert _same_number(
            feature_row[definition["rest"]["output"]], expected_rest
        )

        h2h_config = definition["head_to_head"]
        matchup = eligible[eligible["opponent_id"] == source["opponent_id"]]
        assert _same_number(
            feature_row[h2h_config["average_output"]],
            _expected_aggregate(
                matchup[h2h_config["source_column"]],
                window=None,
                aggregation="mean",
            ),
        )
        assert int(feature_row[h2h_config["matches_output"]]) == len(matchup)
        expected_win_rate = _expected_aggregate(
            matchup["is_winner"], window=None, aggregation="mean"
        )
        assert _same_number(
            feature_row[h2h_config["win_rate_output"]], expected_win_rate
        )

        career = definition["career"]
        assert _same_number(
            feature_row[career["output"]],
            _expected_aggregate(
                eligible[career["source_column"]],
                window=None,
                aggregation="mean",
            ),
        )
        expected_history = pd.to_numeric(
            eligible[career["source_column"]], errors="coerce"
        ).notna().sum()
        assert int(feature_row[career["count_output"]]) == expected_history

        opponent = definition["opponent"]
        opponent_history = _ordered_prior(
            working, source, player_id=source["opponent_id"]
        )
        opponent_history = opponent_history[
            opponent_history["match_completed"].fillna(False)
        ].copy()
        opponent_stat_lookup = working.set_index(
            ["match_id", "player_id"]
        )[opponent["conceded_source_column"]]
        conceded = [
            opponent_stat_lookup.get(
                (history_row.match_id, history_row.opponent_id), np.nan
            )
            for history_row in opponent_history.itertuples(index=False)
        ]
        assert _same_number(
            feature_row[opponent["output"]],
            _expected_aggregate(
                pd.Series(conceded, dtype="float64"),
                window=int(opponent["window"]),
                aggregation="mean",
            ),
        )


def assert_first_match_features_are_null(
    matches: pd.DataFrame,
    features: pd.DataFrame,
    feature_columns: Mapping[str, list[str]],
    raw_config: Mapping[str, Any],
) -> None:
    event_dates = pd.to_datetime(matches["event_date"])
    first_dates = event_dates.groupby(matches["player_id"]).transform("min")
    first_keys = set(
        zip(
            matches.loc[event_dates == first_dates, "match_id"],
            matches.loc[event_dates == first_dates, "player_id"],
            strict=True,
        )
    )
    for target, columns in feature_columns.items():
        rest_output = raw_config["features"]["targets"][target]["rest"]["output"]
        own_history_columns = [
            column
            for column in columns
            if column.startswith("rolling_")
            or column.startswith("surface_rolling_")
            or column.startswith("career_to_date")
            or column.startswith("head_to_head_")
            or column == rest_output
        ]
        target_rows = features[features["stat_target"] == target]
        first_rows = target_rows[
            [
                (match_id, player_id) in first_keys
                for match_id, player_id in zip(
                    target_rows["match_id"],
                    target_rows["player_id"],
                    strict=True,
                )
            ]
        ]
        value_columns = [
            column
            for column in own_history_columns
            if not column.endswith("_observations")
            and not column.endswith("_matches")
        ]
        assert first_rows[value_columns].isna().all().all()


def assert_current_target_perturbation_safe(
    matches: pd.DataFrame,
    features: pd.DataFrame,
    raw_config: Mapping[str, Any],
    feature_columns: Mapping[str, list[str]],
) -> None:
    candidate = features[
        features["target_value"].notna()
        & features["has_sufficient_history"]
    ].iloc[0]
    target = candidate["stat_target"]
    target_column = raw_config["features"]["targets"][target]["source_column"]
    source_row = matches[
        (matches["match_id"] == candidate["match_id"])
        & (matches["player_id"] == candidate["player_id"])
    ].iloc[0]
    involved_players = {source_row["player_id"], source_row["opponent_id"]}
    cutoff = pd.Timestamp(source_row["event_date"])
    relevant_match_ids = set(
        matches.loc[
            matches["player_id"].isin(involved_players)
            & (pd.to_datetime(matches["event_date"]) <= cutoff),
            "match_id",
        ]
    )
    baseline_matches = matches[
        matches["match_id"].isin(relevant_match_ids)
    ].copy()
    changed_matches = baseline_matches.copy()
    mask = (
        (changed_matches["match_id"] == candidate["match_id"])
        & (changed_matches["player_id"] == candidate["player_id"])
    )
    changed_matches.loc[mask, target_column] = (
        pd.to_numeric(changed_matches.loc[mask, target_column]) + 10_000
    )
    feature_config = raw_config["features"]
    definition = feature_config["targets"][target]
    validated = validate_sport_config(dict(raw_config))
    baseline_features, _ = build_target_features(
        baseline_matches,
        sport=validated.sport,
        feature_version=validated.features.feature_version,
        minimum_history=validated.features.minimum_history,
        rolling_windows=validated.features.rolling_windows,
        target_name=target,
        definition=definition,
    )
    changed_features, _ = build_target_features(
        changed_matches,
        sport=validated.sport,
        feature_version=validated.features.feature_version,
        minimum_history=validated.features.minimum_history,
        rolling_windows=validated.features.rolling_windows,
        target_name=target,
        definition=definition,
    )
    full_original = features[
        (features["match_id"] == candidate["match_id"])
        & (features["player_id"] == candidate["player_id"])
        & (features["stat_target"] == target)
    ].iloc[0]
    original = baseline_features[
        (baseline_features["match_id"] == candidate["match_id"])
        & (baseline_features["player_id"] == candidate["player_id"])
        & (baseline_features["stat_target"] == target)
    ].iloc[0]
    changed = changed_features[
        (changed_features["match_id"] == candidate["match_id"])
        & (changed_features["player_id"] == candidate["player_id"])
        & (changed_features["stat_target"] == target)
    ].iloc[0]
    for column in feature_columns[target]:
        assert _same_number(full_original[column], original[column]), column
        assert _same_number(original[column], changed[column]), column


def assert_no_target_correlation(
    features: pd.DataFrame,
    feature_columns: Mapping[str, list[str]],
    *,
    threshold: float = 0.99,
) -> float | None:
    max_correlation: float | None = None
    for target, columns in feature_columns.items():
        target_rows = features[
            (features["stat_target"] == target)
            & features["target_value"].notna()
        ]
        numeric_columns = [
            column
            for column in columns
            if pd.api.types.is_numeric_dtype(target_rows[column])
        ]
        for column in numeric_columns:
            paired = target_rows[[column, "target_value"]].dropna()
            if len(paired) < 3 or paired[column].nunique() < 2:
                continue
            correlation = abs(
                float(paired[column].corr(paired["target_value"]))
            )
            if math.isnan(correlation):
                continue
            max_correlation = (
                correlation
                if max_correlation is None
                else max(max_correlation, correlation)
            )
            assert correlation <= threshold, (
                f"{column} has suspicious {correlation:.6f} correlation "
                f"with {target}"
            )
    return max_correlation


def run_leakage_audit(
    matches: pd.DataFrame,
    features: pd.DataFrame,
    raw_config: Mapping[str, Any],
    feature_columns: Mapping[str, list[str]],
) -> AuditResult:
    assert_sampled_recomputation(matches, features, raw_config)
    assert_first_match_features_are_null(
        matches, features, feature_columns, raw_config
    )
    # This is the strongest leakage test: changing the current outcome must not
    # alter any feature used to predict that same outcome.
    assert_current_target_perturbation_safe(
        matches, features, raw_config, feature_columns
    )
    max_correlation = assert_no_target_correlation(
        features, feature_columns
    )
    return AuditResult(
        sampled_recomputation=True,
        first_match_null=True,
        current_target_perturbation=True,
        correlation_guard=True,
        max_absolute_target_correlation=max_correlation,
    )


def print_report(
    features: pd.DataFrame,
    feature_columns: Mapping[str, list[str]],
    audit: AuditResult,
    raw_config: Mapping[str, Any],
) -> None:
    print("\nPlayer-game feature report")
    print(f"rows: {len(features)}")
    for target, columns in feature_columns.items():
        target_rows = features[features["stat_target"] == target]
        print(f"\n{target} feature null rates")
        for column in columns:
            print(f"  {column}: {100 * target_rows[column].isna().mean():.2f}%")
        distribution = target_rows["target_value"].describe(
            percentiles=[0.25, 0.5, 0.75]
        )
        print(f"{target} target distribution")
        for label in ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]:
            print(f"  {label}: {distribution[label]:.4f}")

    print("\nleakage tests")
    print(f"  sampled 50-row recomputation: {'PASS' if audit.sampled_recomputation else 'FAIL'}")
    print(f"  first-ever match rolling NULLs: {'PASS' if audit.first_match_null else 'FAIL'}")
    print(
        "  current-target inflation invariance: "
        f"{'PASS' if audit.current_target_perturbation else 'FAIL'}"
    )
    print(f"  target correlation guard: {'PASS' if audit.correlation_guard else 'FAIL'}")
    print(
        "  maximum absolute target correlation: "
        + (
            "unavailable"
            if audit.max_absolute_target_correlation is None
            else f"{audit.max_absolute_target_correlation:.6f}"
        )
    )

    eligible = features[features["has_sufficient_history"]]
    sample = eligible.iloc[0]
    print("\nexample feature row")
    print(
        f"  player {sample['player_id']} before match {sample['match_id']} "
        f"on {sample['event_date']}:"
    )
    descriptions = raw_config["features"]["descriptions"]
    for column, value in sample["feature_values"].items():
        rendered = "NULL (not enough prior evidence)" if value is None else value
        explanation = descriptions.get(
            column, "Configured pre-match feature value."
        )
        print(f"  {column}: {rendered} — {explanation}")
    target = sample["stat_target"]
    print(
        f"  target_value: {sample['target_value']} {target} occurred in the "
        "match; it is stored for later training but was not used to build "
        "this row's features."
    )
    print(
        "  has_sufficient_history: "
        f"{sample['has_sufficient_history']} means at least the configured "
        "number of completed prior matches had target data."
    )
    print(
        "  Same-date policy: all outcomes sharing an estimated event_date "
        "are excluded from one another; match_num only makes ordering "
        "deterministic."
    )


def build_and_store(config_path: Path = DEFAULT_CONFIG) -> AuditResult:
    from db.connection import create_db_engine

    raw_config = load_feature_config(config_path)
    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            matches = load_match_frame(connection)
        features, feature_columns = build_feature_frame(matches, raw_config)
        with engine.begin() as connection:
            store_feature_rows(connection, features)
            stored_features = load_stored_feature_rows(
                connection, raw_config, feature_columns
            )
            if len(stored_features) != len(features):
                raise AssertionError(
                    "Stored feature row count does not match the build"
                )
            audit = run_leakage_audit(
                matches, stored_features, raw_config, feature_columns
            )
    finally:
        engine.dispose()
    print_report(stored_features, feature_columns, audit, raw_config)
    return audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Validated sport configuration file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    build_and_store(args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())