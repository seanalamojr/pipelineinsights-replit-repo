"""Load per-player match facts from Kadantte's maintained ATP match CSVs.

The Kadantte fork preserves the one-row-per-match winner/loser shape of the
upstream Sackmann files. This module expands each source row into two player
rows before writing it to the shared matches table.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import re
import sys
from typing import Iterable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_SEASONS = tuple(range(2015, date.today().year + 1))
SOURCE_REPOSITORY = "Kadantte/tennis_atp"
MAX_CURRENT_SEASON_AGE_DAYS = 21
# Kept as the configured-source compatibility constant for existing callers.
SOURCE_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/Kadantte/tennis_atp/master/"
    "atp_matches_{year}.csv"
)
PRIMARY_SOURCE_NAME = SOURCE_REPOSITORY
PRIMARY_SOURCE_URL_TEMPLATE = SOURCE_URL_TEMPLATE
DEFAULT_CACHE_DIR = Path(".cache") / "sackmann_kadantte"
REQUIRED_COLUMNS = {
    "tourney_id",
    "tourney_name",
    "surface",
    "draw_size",
    "tourney_level",
    "tourney_date",
    "match_num",
    "winner_id",
    "winner_name",
    "winner_hand",
    "winner_ht",
    "winner_ioc",
    "winner_age",
    "winner_seed",
    "winner_entry",
    "winner_rank",
    "winner_rank_points",
    "loser_id",
    "loser_name",
    "loser_hand",
    "loser_ht",
    "loser_ioc",
    "loser_age",
    "loser_seed",
    "loser_entry",
    "loser_rank",
    "loser_rank_points",
    "score",
    "best_of",
    "round",
    "minutes",
    "w_ace",
    "w_df",
    "w_svpt",
    "w_1stIn",
    "w_1stWon",
    "w_2ndWon",
    "w_SvGms",
    "w_bpSaved",
    "w_bpFaced",
    "l_ace",
    "l_df",
    "l_svpt",
    "l_1stIn",
    "l_1stWon",
    "l_2ndWon",
    "l_SvGms",
    "l_bpSaved",
    "l_bpFaced",
}
ROUND_OFFSETS = {
    "Q1": -1,
    "Q2": -1,
    "Q3": -1,
    "Q4": -1,
    "R128": 0,
    "R64": 1,
    "R32": 2,
    "R16": 3,
    "QF": 4,
    "SF": 5,
    "F": 6,
}
SET_SCORE_PATTERN = re.compile(r"^(\d+)-(\d+)")
INCOMPLETE_MARKERS = ("RET", "W/O", "WO", "DEF", "ABN", "ABD")


class SeasonUnavailable(RuntimeError):
    """Raised when the configured source has no CSV for a requested season."""


@dataclass(frozen=True)
class SeasonStats:
    season: int
    source_rows: int
    output_rows: int
    non_null_ace_rows: int
    incomplete_matches: int
    null_surface_matches: int
    min_event_date: date | None
    max_event_date: date | None
    source: str = SOURCE_REPOSITORY
    invalid_rows: int = 0
    invalid_stat_rows: int = 0


def _text(row: Mapping[str, str | None], key: str) -> str:
    value = row.get(key)
    return value.strip() if value is not None else ""


def _nullable_int(value: str | None) -> int | None:
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def _nullable_decimal(value: str | None) -> Decimal | None:
    cleaned = (value or "").strip()
    return Decimal(cleaned) if cleaned else None


def _parse_tourney_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y%m%d").date()


def estimate_event_date(tourney_date: date, round_name: str) -> date:
    """Estimate a match date from tournament start and draw round.

    Sackmann supplies the tournament start date, not the date of each match.
    The offsets are a transparent approximation based on the round ordering;
    they are not presented as exact observed dates.
    """

    return tourney_date + timedelta(days=ROUND_OFFSETS.get(round_name.upper(), 0))


def is_match_completed(score: str, best_of: int | None) -> bool:
    """Flag completed matches without converting missing stats into zeros."""

    normalized = score.upper().replace(".", "").strip()
    if not normalized or any(marker in normalized for marker in INCOMPLETE_MARKERS):
        return False

    set_scores = [
        (int(match.group(1)), int(match.group(2)))
        for token in normalized.split()
        if (match := SET_SCORE_PATTERN.match(token))
    ]
    if not set_scores or not best_of:
        return False

    sets_to_win = best_of // 2 + 1
    winner_sets = sum(first > second for first, second in set_scores)
    loser_sets = sum(second > first for first, second in set_scores)
    return max(winner_sets, loser_sets) >= sets_to_win


def _side_snapshot(
    row: Mapping[str, str | None],
    prefix: str,
    snapshot_date: date,
) -> dict[str, object]:
    return {
        "player_id": _text(row, f"{prefix}_id"),
        "full_name": _text(row, f"{prefix}_name"),
        "tour": "ATP",
        "hand": _text(row, f"{prefix}_hand") or None,
        "country": _text(row, f"{prefix}_ioc") or None,
        "height_cm": _nullable_int(row.get(f"{prefix}_ht")),
        "rank_position": _nullable_int(row.get(f"{prefix}_rank")),
        "rank_points": _nullable_int(row.get(f"{prefix}_rank_points")),
        "profile_as_of": snapshot_date,
    }


def _side_stats_valid(row: Mapping[str, str | None], prefix: str) -> bool:
    """Reject impossible service-stat blocks without discarding the match."""

    fields = {
        name: _nullable_int(row.get(f"{prefix}_{suffix}"))
        for name, suffix in {
            "serve_points": "svpt",
            "first_serves_in": "1stIn",
            "first_serves_won": "1stWon",
            "second_serves_won": "2ndWon",
            "aces": "ace",
            "double_faults": "df",
            "service_games": "SvGms",
            "bp_saved": "bpSaved",
            "bp_faced": "bpFaced",
        }.items()
    }
    numeric_values = [value for value in fields.values() if value is not None]
    if any(value < 0 for value in numeric_values):
        return False
    serve_points = fields["serve_points"]
    first_serves_in = fields["first_serves_in"]
    first_serves_won = fields["first_serves_won"]
    if serve_points is not None:
        if first_serves_in is not None and first_serves_in > serve_points:
            return False
        if fields["aces"] is not None and fields["aces"] > serve_points:
            return False
        if fields["double_faults"] is not None and fields["double_faults"] > serve_points:
            return False
    if (
        first_serves_in is not None
        and first_serves_won is not None
        and first_serves_won > first_serves_in
    ):
        return False
    if (
        fields["bp_saved"] is not None
        and fields["bp_faced"] is not None
        and fields["bp_saved"] > fields["bp_faced"]
    ):
        return False
    return True


def _side_match_row(
    row: Mapping[str, str | None],
    *,
    match_id: str,
    tourney_date: date,
    event_date: date,
    side: str,
    opponent: str,
    is_winner: bool,
    match_completed: bool,
) -> dict[str, object]:
    opponent_prefix = "l" if side == "w" else "w"
    player_prefix = "winner" if side == "w" else "loser"
    side_stats_valid = _side_stats_valid(row, side)
    opponent_stats_valid = _side_stats_valid(row, opponent_prefix)
    side_ace = _nullable_int(row.get(f"{side}_ace")) if side_stats_valid else None
    side_double_faults = (
        _nullable_int(row.get(f"{side}_df")) if side_stats_valid else None
    )
    side_service_games = (
        _nullable_int(row.get(f"{side}_SvGms")) if side_stats_valid else None
    )
    return {
        "match_id": match_id,
        "event_date": event_date,
        "tourney_date": tourney_date,
        "tournament": _text(row, "tourney_name"),
        "surface": _text(row, "surface") or None,
        "round": _text(row, "round") or None,
        "player_id": _text(row, f"{player_prefix}_id"),
        "opponent_id": _text(row, f"{'loser' if side == 'w' else 'winner'}_id"),
        "is_winner": is_winner,
        "games_won": None,
        "sets_won": None,
        "aces": side_ace,
        "double_faults": side_double_faults,
        "minutes": _nullable_int(row.get("minutes")),
        "service_games": side_service_games,
        "draw_size": _nullable_int(row.get("draw_size")),
        "tourney_level": _text(row, "tourney_level") or None,
        "match_num": _nullable_int(row.get("match_num")),
        "best_of": _nullable_int(row.get("best_of")),
        "score": _text(row, "score") or None,
        "match_completed": match_completed,
        "player_seed": _nullable_int(row.get(f"{player_prefix}_seed")),
        "player_entry": _text(row, f"{player_prefix}_entry") or None,
        "opponent_seed": _nullable_int(row.get(f"{'loser' if side == 'w' else 'winner'}_seed")),
        "opponent_entry": _text(
            row, f"{'loser' if side == 'w' else 'winner'}_entry"
        )
        or None,
        "player_rank": _nullable_int(row.get(f"{player_prefix}_rank")),
        "opponent_rank": _nullable_int(
            row.get(f"{'loser' if side == 'w' else 'winner'}_rank")
        ),
        "player_rank_points": _nullable_int(
            row.get(f"{player_prefix}_rank_points")
        ),
        "opponent_rank_points": _nullable_int(
            row.get(f"{'loser' if side == 'w' else 'winner'}_rank_points")
        ),
        "player_age": _nullable_decimal(row.get(f"{player_prefix}_age")),
        "serve_points": (
            _nullable_int(row.get(f"{side}_svpt")) if side_stats_valid else None
        ),
        "first_serves_in": (
            _nullable_int(row.get(f"{side}_1stIn")) if side_stats_valid else None
        ),
        "first_serves_won": (
            _nullable_int(row.get(f"{side}_1stWon")) if side_stats_valid else None
        ),
        "second_serves_won": (
            _nullable_int(row.get(f"{side}_2ndWon")) if side_stats_valid else None
        ),
        "bp_saved": (
            _nullable_int(row.get(f"{side}_bpSaved")) if side_stats_valid else None
        ),
        "bp_faced": (
            _nullable_int(row.get(f"{side}_bpFaced")) if side_stats_valid else None
        ),
        "break_points_won": (
            None
            if not side_stats_valid
            or not opponent_stats_valid
            or _nullable_int(row.get(f"{opponent_prefix}_bpFaced")) is None
            or _nullable_int(row.get(f"{opponent_prefix}_bpSaved")) is None
            else _nullable_int(row.get(f"{opponent_prefix}_bpFaced"))
            - _nullable_int(row.get(f"{opponent_prefix}_bpSaved"))
        ),
    }


def transform_sackmann_row(
    row: Mapping[str, str | None],
) -> tuple[dict[str, object], dict[str, object]]:
    """Expand one winner/loser source row into exactly two player rows."""

    tourney_id = _text(row, "tourney_id")
    match_num = _nullable_int(row.get("match_num"))
    winner_id = _text(row, "winner_id")
    loser_id = _text(row, "loser_id")
    if not tourney_id or match_num is None or not winner_id or not loser_id:
        raise ValueError("Sackmann row is missing a stable match or player identifier")

    tourney_date = _parse_tourney_date(_text(row, "tourney_date"))
    round_name = _text(row, "round")
    event_date = estimate_event_date(tourney_date, round_name)
    best_of = _nullable_int(row.get("best_of"))
    score = _text(row, "score")
    completed = is_match_completed(score, best_of)
    match_id = f"{tourney_id}-{match_num}"

    winner = _side_match_row(
        row,
        match_id=match_id,
        tourney_date=tourney_date,
        event_date=event_date,
        side="w",
        opponent=loser_id,
        is_winner=True,
        match_completed=completed,
    )
    loser = _side_match_row(
        row,
        match_id=match_id,
        tourney_date=tourney_date,
        event_date=event_date,
        side="l",
        opponent=winner_id,
        is_winner=False,
        match_completed=completed,
    )
    return winner, loser


def parse_seasons(value: str) -> tuple[int, ...]:
    """Parse 2015-2025, 2015,2017, or a mixture of both."""

    seasons: set[int] = set()
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            seasons.update(range(min(start, end), max(start, end) + 1))
        else:
            seasons.add(int(token))
    if not seasons:
        raise argparse.ArgumentTypeError("at least one season is required")
    return tuple(sorted(seasons))


def _download_season(
    season: int,
    *,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    refresh: bool = False,
) -> tuple[Path, str]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    destination = cache_dir / f"atp_matches_{season}.csv"
    source_marker = destination.with_suffix(".source")
    if destination.exists() and not refresh:
        source = (
            source_marker.read_text(encoding="utf-8").strip()
            if source_marker.exists()
            else PRIMARY_SOURCE_NAME
        )
        return destination, source

    sources = ((PRIMARY_SOURCE_NAME, PRIMARY_SOURCE_URL_TEMPLATE),)
    unavailable: list[str] = []
    for source_name, url_template in sources:
        request = Request(
            url_template.format(year=season),
            headers={"User-Agent": "PipelineInsights/tennis-etl"},
        )
        try:
            with urlopen(request, timeout=60) as response:
                destination.write_bytes(response.read())
            source_marker.write_text(source_name, encoding="utf-8")
            return destination, source_name
        except HTTPError as error:
            if error.code == 404:
                unavailable.append(f"{source_name}: {request.full_url}")
                continue
            raise RuntimeError(
                f"{season}: source download failed with HTTP {error.code}"
            ) from error
        except URLError as error:
            raise RuntimeError(
                f"{season}: source download failed: {error.reason}"
            ) from error

    raise SeasonUnavailable(
        f"{season}: source CSV is unavailable at all configured sources "
        f"({'; '.join(unavailable)})"
    )


def download_season(
    season: int,
    *,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    refresh: bool = False,
) -> Path:
    """Download one season from the configured Kadantte source."""

    path, _source = _download_season(
        season,
        cache_dir=cache_dir,
        refresh=refresh,
    )
    return path


def read_season_rows(path: Path) -> Iterable[dict[str, str | None]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing required columns: {sorted(missing)}")
        for row in reader:
            yield row


def _merge_latest(
    snapshots: dict[str, dict[str, object]],
    row: Mapping[str, str | None],
    snapshot_date: date,
) -> None:
    for prefix in ("winner", "loser"):
        snapshot = _side_snapshot(row, prefix, snapshot_date)
        player_id = str(snapshot["player_id"])
        if not player_id:
            raise ValueError("Sackmann row contains an empty player ID")
        existing = snapshots.get(player_id)
        if existing is None or snapshot_date >= existing["profile_as_of"]:
            snapshots[player_id] = snapshot


def _aggregate_season(
    season: int,
    path: Path,
    snapshots: dict[str, dict[str, object]],
    *,
    source: str = PRIMARY_SOURCE_NAME,
) -> tuple[SeasonStats, list[dict[str, object]]]:
    output_rows: list[dict[str, object]] = []
    source_rows = 0
    incomplete_matches = 0
    null_surface_matches = 0
    non_null_ace_rows = 0
    event_dates: list[date] = []

    for raw_row in read_season_rows(path):
        source_rows += 1
        tourney_date = _parse_tourney_date(_text(raw_row, "tourney_date"))
        _merge_latest(snapshots, raw_row, tourney_date)
        transformed = transform_sackmann_row(raw_row)
        output_rows.extend(transformed)
        if not transformed[0]["match_completed"]:
            incomplete_matches += 1
        if not _text(raw_row, "surface"):
            null_surface_matches += 1
        non_null_ace_rows += sum(row["aces"] is not None for row in transformed)
        event_dates.extend(row["event_date"] for row in transformed)

    stats = SeasonStats(
        season=season,
        source_rows=source_rows,
        output_rows=len(output_rows),
        non_null_ace_rows=non_null_ace_rows,
        incomplete_matches=incomplete_matches,
        null_surface_matches=null_surface_matches,
        min_event_date=min(event_dates) if event_dates else None,
        max_event_date=max(event_dates) if event_dates else None,
        source=source,
    )
    return stats, output_rows


def _raw_match_signature(row: Mapping[str, str | None]) -> tuple[str, ...]:
    return (
        _text(row, "tourney_id"),
        _text(row, "match_num"),
        _text(row, "tourney_date"),
        _text(row, "winner_id"),
        _text(row, "loser_id"),
        _text(row, "score"),
    )


def _unique_match_id(
    row: Mapping[str, str | None],
    seen: dict[str, tuple[str, ...]],
) -> str | None:
    """Keep exact duplicates once and disambiguate conflicting source keys."""

    tourney_id = _text(row, "tourney_id")
    match_num = _text(row, "match_num")
    base_id = f"{tourney_id}-{match_num}"
    signature = _raw_match_signature(row)
    previous = seen.get(base_id)
    if previous is None:
        seen[base_id] = signature
        return base_id
    if previous == signature:
        return None

    disambiguated = (
        f"{base_id}-{_text(row, 'tourney_date')}-"
        f"{_text(row, 'winner_id')}-{_text(row, 'loser_id')}"
    )
    previous_disambiguated = seen.get(disambiguated)
    if previous_disambiguated not in (None, signature):
        raise ValueError(
            f"Cannot disambiguate conflicting match key {base_id}: "
            f"{signature}"
        )
    seen[disambiguated] = signature
    return disambiguated


def _aggregate_attached_files(
    paths: Sequence[Path],
    *,
    season: int,
    source_name: str = "attached_current_data",
) -> tuple[list[SeasonStats], list[dict[str, object]], int]:
    """Transform attached current-season CSVs without trusting duplicate keys."""

    snapshots: dict[str, dict[str, object]] = {}
    seen_match_keys: dict[str, tuple[str, ...]] = {}
    reports: list[SeasonStats] = []
    all_match_rows: list[dict[str, object]] = []
    duplicate_rows = 0

    for path in paths:
        source_rows = 0
        output_rows: list[dict[str, object]] = []
        incomplete_matches = 0
        null_surface_matches = 0
        non_null_ace_rows = 0
        invalid_rows = 0
        invalid_stat_rows = 0
        event_dates: list[date] = []
        for raw_row in read_season_rows(path):
            source_rows += 1
            if (
                not _text(raw_row, "tourney_id")
                or not _text(raw_row, "match_num")
                or not _text(raw_row, "winner_id")
                or not _text(raw_row, "loser_id")
            ):
                invalid_rows += 1
                continue
            unique_match_id = _unique_match_id(raw_row, seen_match_keys)
            if unique_match_id is None:
                duplicate_rows += 1
                continue
            tourney_date = _parse_tourney_date(_text(raw_row, "tourney_date"))
            _merge_latest(snapshots, raw_row, tourney_date)
            if not (
                _side_stats_valid(raw_row, "w")
                and _side_stats_valid(raw_row, "l")
            ):
                invalid_stat_rows += 1
            transformed = list(transform_sackmann_row(raw_row))
            for player_row in transformed:
                player_row["match_id"] = unique_match_id
            output_rows.extend(transformed)
            if not transformed[0]["match_completed"]:
                incomplete_matches += 1
            if not _text(raw_row, "surface"):
                null_surface_matches += 1
            non_null_ace_rows += sum(
                player_row["aces"] is not None for player_row in transformed
            )
            event_dates.extend(
                player_row["event_date"] for player_row in transformed
            )

        reports.append(
            SeasonStats(
                season=season,
                source=f"{source_name}:{path.name}",
                source_rows=source_rows,
                output_rows=len(output_rows),
                non_null_ace_rows=non_null_ace_rows,
                incomplete_matches=incomplete_matches,
                null_surface_matches=null_surface_matches,
                min_event_date=min(event_dates) if event_dates else None,
                max_event_date=max(event_dates) if event_dates else None,
                invalid_rows=invalid_rows,
                invalid_stat_rows=invalid_stat_rows,
            )
        )
        all_match_rows.extend(output_rows)

    return reports, all_match_rows, duplicate_rows


def load_attached_files(
    paths: Sequence[Path],
    *,
    season: int = 2026,
    inspect_player: str = "",
    inspect_season: int | None = None,
    max_current_season_age_days: int = MAX_CURRENT_SEASON_AGE_DAYS,
    today: date | None = None,
) -> list[SeasonStats]:
    """Ingest user-provided current-season ATP and Challenger CSVs."""

    if not paths:
        raise ValueError("At least one attached current-data CSV is required")
    reports, match_rows, duplicate_rows = _aggregate_attached_files(
        paths, season=season
    )
    assert_current_season_fresh(
        reports,
        today=today,
        max_age_days=max_current_season_age_days,
    )

    snapshots: dict[str, dict[str, object]] = {}
    for path in paths:
        for raw_row in read_season_rows(path):
            if (
                not _text(raw_row, "tourney_id")
                or not _text(raw_row, "match_num")
                or not _text(raw_row, "winner_id")
                or not _text(raw_row, "loser_id")
            ):
                continue
            tourney_date = _parse_tourney_date(_text(raw_row, "tourney_date"))
            _merge_latest(snapshots, raw_row, tourney_date)

    from db.connection import create_db_engine

    engine = create_db_engine()
    try:
        with engine.begin() as connection:
            _upsert_rows(connection, "players", list(snapshots.values()))
            _upsert_rows(connection, "matches", match_rows)
            if inspect_player:
                selected_season = inspect_season or season
                _print_player_history(
                    connection,
                    player_name=inspect_player,
                    season=selected_season,
                )
    finally:
        engine.dispose()

    print("\nAttached current-data ETL report")
    print(f"source files: {len(paths)}")
    print(f"duplicate source rows skipped: {duplicate_rows}")
    print(f"players upserted: {len(snapshots)}")
    print(f"matches rows upserted: {len(match_rows)}")
    for report in reports:
        percent = (
            100 * report.non_null_ace_rows / report.output_rows
            if report.output_rows
            else 0
        )
        print(
            f"{report.source} | source rows: {report.source_rows} | "
            f"player rows: {report.output_rows} | aces present: {percent:.2f}% | "
            f"incomplete: {report.incomplete_matches} | "
            f"invalid: {report.invalid_rows} | "
            f"invalid stats: {report.invalid_stat_rows} | "
            f"latest event_date: {report.max_event_date}"
        )
    return reports


def _upsert_rows(connection: object, table: str, rows: list[dict[str, object]]) -> None:
    from sqlalchemy import text

    if not rows:
        return
    columns = list(rows[0])
    column_sql = ", ".join(columns)
    value_sql = ", ".join(f":{column}" for column in columns)
    updates = ", ".join(
        f"{column} = EXCLUDED.{column}"
        for column in columns
        if column not in {"match_id", "player_id"}
    )
    primary_key = (
        "(player_id)"
        if table == "players"
        else "(match_id, player_id)"
    )
    where_clause = ""
    if table == "players":
        where_clause = (
            " WHERE players.profile_as_of IS NULL "
            "OR EXCLUDED.profile_as_of >= players.profile_as_of"
        )
    statement = text(
        f"""
        INSERT INTO {table} ({column_sql})
        VALUES ({value_sql})
        ON CONFLICT {primary_key} DO UPDATE SET {updates}{where_clause}
        """
    )
    connection.execute(statement, rows)


def _print_player_history(
    connection: object,
    *,
    player_name: str,
    season: int,
) -> int:
    from sqlalchemy import text

    result = connection.execute(
        text(
            """
            SELECT
                match_row.event_date,
                match_row.tournament,
                match_row.surface,
                opponent.full_name AS opponent,
                match_row.score,
                match_row.aces
            FROM matches AS match_row
            JOIN players AS player
              ON player.player_id = match_row.player_id
            LEFT JOIN players AS opponent
              ON opponent.player_id = match_row.opponent_id
            WHERE player.full_name = :player_name
              AND EXTRACT(
                    YEAR FROM COALESCE(match_row.tourney_date, match_row.event_date)
                  ) = :season
            ORDER BY match_row.event_date, match_row.match_id
            """
        ),
        {"player_name": player_name, "season": season},
    )
    rows = result.fetchall()
    print(f"\n{player_name} match history for {season}")
    print("date | tournament | surface | opponent | score | aces")
    for row in rows:
        print(
            " | ".join(
                "NULL" if value is None else str(value)
                for value in row
            )
        )
    if not rows:
        print("(no rows loaded for this player and season)")
    return len(rows)


def load_seasons(
    seasons: Iterable[int],
    *,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    refresh: bool = False,
    inspect_player: str = "Novak Djokovic",
    inspect_season: int | None = None,
    max_current_season_age_days: int = MAX_CURRENT_SEASON_AGE_DAYS,
    today: date | None = None,
) -> list[SeasonStats]:
    """Download, transform, and idempotently upsert the requested seasons."""

    from db.connection import create_db_engine

    snapshots: dict[str, dict[str, object]] = {}
    all_match_rows: list[dict[str, object]] = []
    reports: list[SeasonStats] = []
    unavailable: list[str] = []

    for season in sorted(set(seasons)):
        try:
            path, source = _download_season(
                season,
                cache_dir=cache_dir,
                refresh=refresh,
            )
        except SeasonUnavailable as error:
            unavailable.append(str(error))
            continue
        report, match_rows = _aggregate_season(
            season,
            path,
            snapshots,
            source=source,
        )
        reports.append(report)
        all_match_rows.extend(match_rows)

    if not reports:
        details = "; ".join(unavailable) or "no seasons were requested"
        raise RuntimeError(f"No requested seasons could be loaded: {details}")

    assert_current_season_fresh(
        reports,
        today=today,
        max_age_days=max_current_season_age_days,
    )

    player_rows = list(snapshots.values())
    engine = create_db_engine()
    try:
        with engine.begin() as connection:
            _upsert_rows(connection, "players", player_rows)
            _upsert_rows(connection, "matches", all_match_rows)
            selected_season = inspect_season or reports[0].season
            _print_player_history(
                connection,
                player_name=inspect_player,
                season=selected_season,
            )
    finally:
        engine.dispose()

    print("\nSackmann ETL report")
    print("sources:")
    for source in dict.fromkeys(report.source for report in reports):
        if source == PRIMARY_SOURCE_NAME:
            url = PRIMARY_SOURCE_URL_TEMPLATE
        else:
            url = "cached local CSV"
        print(f"  - {source}: {url}")
    print(f"requested seasons: {', '.join(str(season) for season in sorted(set(seasons)))}")
    if unavailable:
        print("unavailable seasons:")
        for message in unavailable:
            print(f"  - {message}")
    print(f"players upserted: {len(player_rows)}")
    print(f"matches rows upserted: {len(all_match_rows)}")
    print(
        "season | source | source matches | player rows | ace stats present | "
        "incomplete | null surfaces"
    )
    for report in reports:
        percent = (
            100 * report.non_null_ace_rows / report.output_rows
            if report.output_rows
            else 0
        )
        print(
            f"{report.season} | {report.source} | {report.source_rows} | "
            f"{report.output_rows} | "
            f"{percent:.2f}% | {report.incomplete_matches} | "
            f"{report.null_surface_matches}"
        )
    total_rows = sum(report.output_rows for report in reports)
    total_ace_rows = sum(report.non_null_ace_rows for report in reports)
    total_incomplete = sum(report.incomplete_matches for report in reports)
    total_null_surfaces = sum(report.null_surface_matches for report in reports)
    min_date = min(report.min_event_date for report in reports if report.min_event_date)
    max_date = max(report.max_event_date for report in reports if report.max_event_date)
    print(f"percent of player rows with non-null aces: {100 * total_ace_rows / total_rows:.2f}%")
    print(f"retirements/walkovers: {total_incomplete}")
    print(f"null surfaces: {total_null_surfaces}")
    print(f"event_date range: {min_date} through {max_date}")
    return reports


def assert_current_season_fresh(
    reports: Iterable[SeasonStats],
    *,
    today: date | None = None,
    max_age_days: int = MAX_CURRENT_SEASON_AGE_DAYS,
) -> None:
    """Reject explicitly loaded current-season data that has gone stale."""

    current_date = today or date.today()
    for report in reports:
        if report.season != current_date.year:
            continue
        if report.max_event_date is None:
            raise RuntimeError(
                f"{report.season}: current-season source has no event dates"
            )
        age_days = (current_date - report.max_event_date).days
        if age_days > max_age_days:
            raise RuntimeError(
                f"{report.season}: source data is {age_days} days stale "
                f"(latest estimated event_date {report.max_event_date}); "
                f"refusing to ingest beyond the {max_age_days}-day "
                "freshness limit"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seasons",
        type=parse_seasons,
        default=DEFAULT_SEASONS,
        help="Season list or range, such as 2015-2025 or 2015,2017.",
    )
    parser.add_argument("--refresh", action="store_true", help="Redownload cached CSVs.")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="Directory for downloaded source CSVs.",
    )
    parser.add_argument("--inspect-player", default="Novak Djokovic")
    parser.add_argument("--inspect-season", type=int)
    parser.add_argument(
        "--attached-file",
        action="append",
        type=Path,
        default=[],
        help=(
            "Current-season Sackmann CSV to ingest. Repeat for ATP and "
            "Challenger files; bypasses the remote season downloader."
        ),
    )
    parser.add_argument(
        "--max-current-season-age-days",
        type=int,
        default=MAX_CURRENT_SEASON_AGE_DAYS,
        help=(
            "Fail current-season ingestion when its latest estimated event "
            "date is older than this many days."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.attached_file:
            load_attached_files(
                args.attached_file,
                inspect_player=args.inspect_player,
                inspect_season=args.inspect_season,
                max_current_season_age_days=args.max_current_season_age_days,
            )
        else:
            load_seasons(
                args.seasons,
                cache_dir=args.cache_dir,
                refresh=args.refresh,
                inspect_player=args.inspect_player,
                inspect_season=args.inspect_season,
                max_current_season_age_days=args.max_current_season_age_days,
            )
    except Exception as error:
        print(f"Sackmann ETL failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())