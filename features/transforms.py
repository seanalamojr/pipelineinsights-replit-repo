"""Reusable feature primitives with strict pre-event history boundaries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


Aggregation = Literal["mean", "std", "median"]


@dataclass(frozen=True)
class _HistoryValue:
    row_index: object
    event_date: pd.Timestamp
    value: float


def _aggregate(values: Sequence[float], agg: Aggregation) -> float:
    if not values:
        return np.nan
    if agg == "mean":
        return float(np.mean(values))
    if agg == "median":
        return float(np.median(values))
    if agg == "std":
        return float(np.std(values, ddof=1)) if len(values) >= 2 else np.nan
    raise ValueError(f"Unsupported rolling aggregation: {agg}")


def _strict_prior_aggregate(
    df: pd.DataFrame,
    *,
    group_cols: Sequence[str],
    date_col: str,
    value_col: str,
    agg: Aggregation,
    window: int | None,
    order_cols: Sequence[str],
    eligibility_col: str | None,
) -> tuple[pd.Series, pd.Series]:
    if not df.index.is_unique:
        raise ValueError("Feature transforms require a unique DataFrame index")
    if window is not None and window <= 0:
        raise ValueError("Rolling windows must be positive")

    required = set(group_cols) | {date_col, value_col} | set(order_cols)
    if eligibility_col:
        required.add(eligibility_col)
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing feature input columns: {sorted(missing)}")

    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])
    sort_cols = list(dict.fromkeys([*group_cols, date_col, *order_cols]))
    work = work.sort_values(sort_cols, kind="mergesort")
    values = pd.Series(np.nan, index=df.index, dtype="float64")
    observations = pd.Series(0, index=df.index, dtype="int64")
    group_key: str | list[str] = (
        group_cols[0] if len(group_cols) == 1 else list(group_cols)
    )

    for _, group in work.groupby(group_key, sort=False, dropna=False):
        history: list[_HistoryValue] = []
        for event_date, same_date_rows in group.groupby(
            date_col, sort=False, dropna=False
        ):
            selected = history[-window:] if window is not None else history
            selected_values = [item.value for item in selected]
            aggregate = _aggregate(selected_values, agg)

            for row_index in same_date_rows.index:
                # Including today's result is the most common beginner mistake in
                # sports modeling and produces spectacular fake accuracy.
                assert all(item.row_index != row_index for item in selected)
                assert all(item.event_date < event_date for item in selected)
                values.at[row_index] = aggregate
                observations.at[row_index] = len(selected)

            for row_index, row in same_date_rows.iterrows():
                is_eligible = (
                    True
                    if eligibility_col is None
                    else bool(row[eligibility_col])
                )
                raw_value = row[value_col]
                if is_eligible and pd.notna(raw_value):
                    history.append(
                        _HistoryValue(
                            row_index=row_index,
                            event_date=event_date,
                            value=float(raw_value),
                        )
                    )

    # The walk-forward evaluator treats has_sufficient_history rows as fully
    # scoreable. The rolling mean is expanding, so any row with prior history
    # must have a value; guard that cross-module invariant here.
    # Sample standard deviation is intentionally undefined for one observation;
    # all other aggregates must be non-null once history exists.
    required_observations = (
        observations.ge(2) if agg == "std" else observations.ge(1)
    )
    invalid = required_observations & values.isna()
    assert not invalid.any(), (
        "Rolling aggregates must be non-null once enough history exists; "
        "evaluation/backtest.py score_predictions depends on this invariant."
    )
    return values, observations


def rolling_stat(
    df: pd.DataFrame,
    group_col: str,
    date_col: str,
    stat_col: str,
    window: int,
    agg: Aggregation,
    *,
    order_cols: Sequence[str] = ("tourney_date", "match_num", "match_id"),
    eligibility_col: str | None = "match_completed",
) -> pd.Series:
    """Aggregate the last N eligible events strictly before each event date."""

    values, _ = _strict_prior_aggregate(
        df,
        group_cols=[group_col],
        date_col=date_col,
        value_col=stat_col,
        agg=agg,
        window=window,
        order_cols=order_cols,
        eligibility_col=eligibility_col,
    )
    return values


def rolling_by_category(
    df: pd.DataFrame,
    group_col: str,
    date_col: str,
    stat_col: str,
    category_col: str,
    window: int,
    agg: Aggregation = "mean",
    *,
    order_cols: Sequence[str] = ("tourney_date", "match_num", "match_id"),
    eligibility_col: str | None = "match_completed",
) -> pd.DataFrame:
    """Return category-specific history and its observation count."""

    values, observations = _strict_prior_aggregate(
        df,
        group_cols=[group_col, category_col],
        date_col=date_col,
        value_col=stat_col,
        agg=agg,
        window=window,
        order_cols=order_cols,
        eligibility_col=eligibility_col,
    )
    return pd.DataFrame(
        {"value": values, "n_observations": observations},
        index=df.index,
    )


def days_since_previous(
    df: pd.DataFrame,
    group_col: str,
    date_col: str,
    *,
    order_cols: Sequence[str] = ("tourney_date", "match_num", "match_id"),
) -> pd.Series:
    """Return days since the player's previous distinct event date."""

    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])
    work = work.sort_values(
        list(dict.fromkeys([group_col, date_col, *order_cols])),
        kind="mergesort",
    )
    output = pd.Series(np.nan, index=df.index, dtype="float64")
    for _, group in work.groupby(group_col, sort=False, dropna=False):
        previous_date: pd.Timestamp | None = None
        for event_date, same_date_rows in group.groupby(date_col, sort=False):
            if previous_date is not None:
                output.loc[same_date_rows.index] = (
                    event_date - previous_date
                ).days
            previous_date = event_date
    return output


def head_to_head(
    df: pd.DataFrame,
    player_col: str,
    opponent_col: str,
    date_col: str,
    stat_col: str,
    *,
    result_col: str = "is_winner",
    order_cols: Sequence[str] = ("tourney_date", "match_num", "match_id"),
    eligibility_col: str | None = "match_completed",
) -> pd.DataFrame:
    """Return prior matchup count, win rate, and stat average."""

    stat_average, stat_observations = _strict_prior_aggregate(
        df,
        group_cols=[player_col, opponent_col],
        date_col=date_col,
        value_col=stat_col,
        agg="mean",
        window=None,
        order_cols=order_cols,
        eligibility_col=eligibility_col,
    )
    win_rate, prior_matches = _strict_prior_aggregate(
        df,
        group_cols=[player_col, opponent_col],
        date_col=date_col,
        value_col=result_col,
        agg="mean",
        window=None,
        order_cols=order_cols,
        eligibility_col=eligibility_col,
    )
    return pd.DataFrame(
        {
            "stat_average": stat_average,
            "stat_observations": stat_observations,
            "win_rate": win_rate,
            "prior_matches": prior_matches,
        },
        index=df.index,
    )


def opponent_rolling(
    df: pd.DataFrame,
    player_col: str,
    opponent_col: str,
    match_col: str,
    date_col: str,
    stat_col: str,
    window: int,
    agg: Aggregation = "mean",
    *,
    order_cols: Sequence[str] = ("tourney_date", "match_num", "match_id"),
    eligibility_col: str | None = "match_completed",
) -> pd.DataFrame:
    """Map each opponent's strictly prior rolling form onto the current row."""

    own_values, own_observations = _strict_prior_aggregate(
        df,
        group_cols=[player_col],
        date_col=date_col,
        value_col=stat_col,
        agg=agg,
        window=window,
        order_cols=order_cols,
        eligibility_col=eligibility_col,
    )
    value_lookup = {
        (row[match_col], row[player_col]): own_values.at[index]
        for index, row in df.iterrows()
    }
    observation_lookup = {
        (row[match_col], row[player_col]): own_observations.at[index]
        for index, row in df.iterrows()
    }
    values = pd.Series(
        [
            value_lookup.get((row[match_col], row[opponent_col]), np.nan)
            for _, row in df.iterrows()
        ],
        index=df.index,
        dtype="float64",
    )
    observations = pd.Series(
        [
            observation_lookup.get((row[match_col], row[opponent_col]), 0)
            for _, row in df.iterrows()
        ],
        index=df.index,
        dtype="int64",
    )
    return pd.DataFrame(
        {"value": values, "n_observations": observations},
        index=df.index,
    )


def career_to_date(
    df: pd.DataFrame,
    group_col: str,
    date_col: str,
    stat_col: str,
    agg: Aggregation = "mean",
    *,
    order_cols: Sequence[str] = ("tourney_date", "match_num", "match_id"),
    eligibility_col: str | None = "match_completed",
) -> pd.DataFrame:
    """Return a shifted expanding career aggregate and history count."""

    values, observations = _strict_prior_aggregate(
        df,
        group_cols=[group_col],
        date_col=date_col,
        value_col=stat_col,
        agg=agg,
        window=None,
        order_cols=order_cols,
        eligibility_col=eligibility_col,
    )
    return pd.DataFrame(
        {"value": values, "n_observations": observations},
        index=df.index,
    )