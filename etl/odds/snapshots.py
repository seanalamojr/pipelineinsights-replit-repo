"""Load pre-match player-prop odds snapshots with auditable identity resolution.

The odds provider's player and fixture identifiers are deliberately not treated
as internal identifiers. Player names are resolved exactly after normalization,
and fixtures are resolved from the two resolved player names plus event date.
Unresolved odds remain in the odds table with nullable internal keys so they can
be mapped and reloaded later.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from sqlalchemy import text


DEFAULT_SNAPSHOT_DIR = Path("odds_snapshots")
DEFAULT_PROVIDER = "free_tier_odds_api"
SNAPSHOT_PATTERN = "tennis_props_*.csv"
REQUIRED_COLUMNS = {
    "captured_at",
    "fixture_id",
    "league",
    "tournament",
    "start_date",
    "home_player",
    "away_player",
    "sportsbook",
    "market_id",
    "market",
    "player_id",
    "selection",
    "normalized_selection",
    "points",
    "price",
    "odds_id",
}
PIVOT_REQUIRED_COLUMNS = {
    "captured_at",
    "fixture_id",
    "league",
    "tournament",
    "start_date",
    "home_player",
    "away_player",
    "book",
    "market_id",
    "market",
    "provider_player_name",
    "provider_player_id",
    "normalized_selection",
    "line",
    "is_main",
    "over_price",
    "under_price",
    "over_odds_id",
    "under_odds_id",
}
PROP_ALIASES = {
    "aces": "aces",
    "doublefaults": "double_faults",
    "double faults": "double_faults",
    "servicegames": "service_games",
    "service games": "service_games",
    "gameswon": "games_won",
    "games won": "games_won",
    "setswon": "sets_won",
    "sets won": "sets_won",
    "breakpointswon": "break_points_won",
    "break points won": "break_points_won",
    "minutes": "minutes",
}


@dataclass(frozen=True)
class UnresolvedName:
    provider_player_name: str
    league: str
    row_count: int


@dataclass(frozen=True)
class AliasCollision:
    alias: str
    player_ids: tuple[str, ...]


@dataclass(frozen=True)
class OddsLoadReport:
    source_path: Path
    provider: str
    source_rows: int
    eligible_rows: int
    skipped_post_start_rows: int
    invalid_rows: int
    pivot_rows: int
    rows_written: int
    raw_name_matches: int
    normalized_name_matches: int
    unresolved_name_rows: int
    unresolved_fixture_rows: int
    unresolved_names: tuple[UnresolvedName, ...]
    alias_collisions: tuple[AliasCollision, ...]
    source_tours: tuple[str, ...]
    reference_tours: tuple[str, ...]

    @property
    def name_match_denominator(self) -> int:
        return (
            self.raw_name_matches
            + self.normalized_name_matches
            + self.unresolved_name_rows
        )

    @property
    def raw_match_rate(self) -> float:
        denominator = self.name_match_denominator
        return 100.0 * self.raw_name_matches / denominator if denominator else 0.0

    @property
    def normalized_match_rate(self) -> float:
        denominator = self.name_match_denominator
        matched = self.raw_name_matches + self.normalized_name_matches
        return 100.0 * matched / denominator if denominator else 0.0


@dataclass(frozen=True)
class PreparedSnapshot:
    rows: tuple[dict[str, Any], ...]
    report: OddsLoadReport


@dataclass(frozen=True)
class _NameResolution:
    player_id: str | None
    stage: str


@dataclass(frozen=True)
class _MatchReference:
    match_id: str
    event_date: date
    tournament: str
    player_id: str
    opponent_id: str | None


def normalize_tour(value: object) -> str | None:
    """Normalize only conservative, well-known tour labels."""

    normalized = normalize_player_name(value)
    if normalized in {"atp", "atp tour", "atp challenger", "challenger"}:
        return "ATP"
    if normalized in {"wta", "wta tour"}:
        return "WTA"
    return None


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def normalize_player_name(value: object) -> str:
    """Normalize accents, punctuation, case, and whitespace without fuzziness."""

    text_value = unicodedata.normalize("NFKD", _clean_text(value))
    text_value = "".join(
        character for character in text_value if not unicodedata.combining(character)
    )
    # The archive uses YeXin while the official WTA profile uses Ye Xin.
    # Split visible camel-case boundaries before casefolding; never infer a
    # player from edit distance or from an incomplete name.
    text_value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text_value)
    text_value = text_value.casefold()
    text_value = re.sub(r"[^a-z0-9]+", " ", text_value)
    return " ".join(text_value.split())


def _name_aliases(full_name: object) -> set[str]:
    normalized = normalize_player_name(full_name)
    tokens = normalized.split()
    if not tokens:
        return set()
    aliases = {normalized}
    if len(tokens) >= 2:
        first = tokens[0]
        for surname_start in range(1, len(tokens)):
            surname = " ".join(tokens[surname_start:])
            aliases.update({f"{surname} {first[0]}", f"{first[0]} {surname}"})
    return aliases


def _name_index(
    players: Iterable[Mapping[str, Any]],
    *,
    tour: str | None = None,
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    raw_index: dict[str, set[str]] = defaultdict(set)
    normalized_index: dict[str, set[str]] = defaultdict(set)
    for player in players:
        player_id = _clean_text(player.get("player_id"))
        full_name = _clean_text(player.get("full_name"))
        player_tour = normalize_tour(player.get("tour"))
        if tour and player_tour != tour:
            continue
        if not player_id or not full_name:
            continue
        raw_index[full_name.casefold()].add(player_id)
        for alias in _name_aliases(full_name):
            normalized_index[alias].add(player_id)
    return dict(raw_index), dict(normalized_index)


def name_alias_collisions(
    players: Iterable[Mapping[str, Any]],
) -> tuple[AliasCollision, ...]:
    """Report every normalized alias that maps to multiple player rows."""

    _raw_index, normalized_index = _name_index(players)
    return tuple(
        AliasCollision(alias, tuple(sorted(player_ids)))
        for alias, player_ids in sorted(normalized_index.items())
        if len(player_ids) > 1
    )


def resolve_player_name(
    provider_name: object,
    players: Iterable[Mapping[str, Any]],
    *,
    tour: str | None = None,
) -> tuple[str | None, str]:
    """Resolve a name exactly, optionally within a compatible tour."""

    raw_index, normalized_index = _name_index(players, tour=tour)
    raw_key = _clean_text(provider_name).casefold()
    raw_matches = raw_index.get(raw_key, set())
    if len(raw_matches) == 1:
        return next(iter(raw_matches)), "raw"
    normalized_matches = normalized_index.get(normalize_player_name(provider_name), set())
    if len(normalized_matches) == 1:
        return next(iter(normalized_matches)), "normalized"
    return None, "unresolved"


def _parse_datetime(value: object) -> datetime:
    text_value = _clean_text(value)
    if not text_value:
        raise ValueError("timestamp is empty")
    if text_value.endswith("Z"):
        text_value = text_value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text_value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(_clean_text(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{field_name} is not numeric: {value!r}") from error


def _side(row: Mapping[str, Any]) -> str:
    for candidate in (
        _clean_text(row.get("selection_line")),
        _clean_text(row.get("normalized_selection")),
        _clean_text(row.get("selection")),
    ):
        normalized = normalize_player_name(candidate)
        if normalized in {"over", "under"}:
            return normalized
        match = re.search(r"\b(over|under)\b", normalized)
        if match:
            return match.group(1)
    return ""


def _selected_player_name(row: Mapping[str, Any]) -> str:
    """Infer the selected provider name without assuming it is the home player."""

    for field in ("player_name", "selection_player", "participant"):
        value = _clean_text(row.get(field))
        if value:
            return value
    # Some raw provider exports put the selected player's display name in
    # `selection` and the Over/Under side in `selection_line`.
    selection = _clean_text(row.get("selection"))
    if selection and _side(row) in {"over", "under"}:
        for field in ("home_player", "away_player"):
            candidate = _clean_text(row.get(field))
            if candidate and normalize_player_name(candidate) == normalize_player_name(
                selection
            ):
                return candidate
    selection_text = normalize_player_name(
        f"{row.get('selection', '')} {row.get('normalized_selection', '')}"
    )
    for field in ("home_player", "away_player"):
        candidate = _clean_text(row.get(field))
        normalized_candidate = normalize_player_name(candidate)
        if candidate and normalized_candidate in selection_text:
            return candidate
    return ""


def _prop_type(market: object) -> str:
    normalized = normalize_player_name(market)
    compact = normalized.replace(" ", "")
    if normalized in PROP_ALIASES:
        return PROP_ALIASES[normalized]
    if compact in PROP_ALIASES:
        return PROP_ALIASES[compact]
    for alias, prop_type in PROP_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", normalized):
            return prop_type
    raise ValueError(f"Unsupported odds market: {market!r}")


def _pivot_row_to_raw_rows(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Expand one pivot export row into the raw Over/Under input shape."""

    common = {
        "captured_at": row.get("captured_at"),
        "fixture_id": row.get("fixture_id"),
        "game_id": row.get("game_id"),
        "league": row.get("league"),
        "tournament": row.get("tournament"),
        "start_date": row.get("start_date"),
        "status": row.get("status"),
        "home_player": row.get("home_player"),
        "away_player": row.get("away_player"),
        "sportsbook": row.get("book"),
        "market_id": row.get("market_id"),
        "market": row.get("market"),
        "player_id": row.get("provider_player_id"),
        "player_name": row.get("provider_player_name"),
        "is_main": row.get("is_main"),
        "grouping_key": row.get("grouping_key"),
        "odds_timestamp": row.get("odds_timestamp"),
        "odds_timestamp_utc": row.get("odds_timestamp_utc"),
        "points": row.get("line"),
    }
    expanded: list[dict[str, Any]] = []
    for side in ("over", "under"):
        price = row.get(f"{side}_price")
        odds_id = row.get(f"{side}_odds_id")
        if _clean_text(price) == "" and _clean_text(odds_id) == "":
            continue
        expanded.append(
            {
                **common,
                "selection": side.title(),
                "normalized_selection": side,
                "selection_line": row.get("line"),
                "price": price,
                "odds_id": odds_id,
            }
        )
    return expanded


def _normalize_snapshot_rows(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Accept either raw captures or pivoted exports.

    Pivot rows are expanded before pre-match filtering so each side keeps its
    original provider odds ID and the existing preparation path remains the
    single source of truth for identity resolution.
    """

    source_rows = len(rows)
    if not rows:
        return [], source_rows
    columns = set(rows[0])
    if PIVOT_REQUIRED_COLUMNS.issubset(columns):
        missing = PIVOT_REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                "Pivot odds export is missing required columns: "
                + ", ".join(sorted(missing))
            )
        expanded = [
            expanded_row
            for row in rows
            for expanded_row in _pivot_row_to_raw_rows(row)
        ]
        return expanded, source_rows
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(
            "Odds export is neither a supported raw nor pivot format; "
            f"missing columns: {', '.join(sorted(missing))}"
        )
    return [dict(row) for row in rows], source_rows


def pivot_selections(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Pivot separate Over/Under selections into one odds-table row."""

    grouped: dict[tuple[str, str, str, str, Decimal], dict[str, Any]] = {}
    for source_row in rows:
        fixture_id = _clean_text(source_row.get("fixture_id"))
        sportsbook = _clean_text(source_row.get("sportsbook"))
        market = _clean_text(source_row.get("market"))
        provider_player_id = _clean_text(source_row.get("player_id"))
        points = _parse_decimal(source_row.get("points"), "points")
        key = (fixture_id, sportsbook, market, provider_player_id, points)
        output = grouped.setdefault(
            key,
            {
                "fixture_id": fixture_id,
                "sportsbook": sportsbook,
                "market": market,
                "market_id": _clean_text(source_row.get("market_id")) or None,
                "provider_player_id": provider_player_id,
                "provider_player_name": _selected_player_name(source_row),
                "home_player": _clean_text(source_row.get("home_player")),
                "away_player": _clean_text(source_row.get("away_player")),
                "league": _clean_text(source_row.get("league")),
                "tournament": _clean_text(source_row.get("tournament")),
                "start_date": source_row.get("start_date"),
                "captured_at": source_row.get("captured_at"),
                "line": points,
                "over_price": None,
                "under_price": None,
                "over_provider_odds_id": None,
                "under_provider_odds_id": None,
            },
        )
        side = _side(source_row)
        if side not in {"over", "under"}:
            raise ValueError(
                f"Selection is neither Over nor Under: "
                f"{source_row.get('selection')!r}"
            )
        output[f"{side}_price"] = _parse_decimal(source_row.get("price"), "price")
        output[f"{side}_provider_odds_id"] = _clean_text(
            source_row.get("odds_id")
        ) or None
        # Preserve the selected player's name when the source exposes it.
        selected_name = _selected_player_name(source_row)
        if selected_name:
            output["provider_player_name"] = selected_name
    result: list[dict[str, Any]] = []
    for output in grouped.values():
        provider_ids = sorted(
            {
                provider_id
                for provider_id in (
                    output.pop("over_provider_odds_id"),
                    output.pop("under_provider_odds_id"),
                )
                if provider_id
            }
        )
        output["provider_odds_id"] = "|".join(provider_ids) or None
        result.append(output)
    return result


def _match_reference(
    matches: Iterable[Mapping[str, Any]],
) -> list[_MatchReference]:
    return [
        _MatchReference(
            match_id=_clean_text(row.get("match_id")),
            event_date=row["event_date"],
            tournament=_clean_text(row.get("tournament")),
            player_id=_clean_text(row.get("player_id")),
            opponent_id=_clean_text(row.get("opponent_id")) or None,
        )
        for row in matches
    ]


def _resolve_fixture(
    row: Mapping[str, Any],
    *,
    home_id: str | None,
    away_id: str | None,
    selected_player_id: str,
    matches: Sequence[_MatchReference],
) -> str | None:
    start_date = _parse_datetime(row["start_date"]).date()
    tournament = normalize_player_name(row.get("tournament"))
    if not home_id or not away_id or home_id == away_id:
        return None
    candidates = [
        match
        for match in matches
        if match.event_date == start_date
        and (
            not tournament
            or normalize_player_name(match.tournament) == tournament
        )
        and {match.player_id, match.opponent_id} == {home_id, away_id}
        and selected_player_id in {home_id, away_id}
    ]
    match_ids = sorted({match.match_id for match in candidates})
    return match_ids[0] if len(match_ids) == 1 else None


def prepare_snapshot(
    rows: Sequence[Mapping[str, Any]],
    *,
    players: Sequence[Mapping[str, Any]],
    matches: Sequence[Mapping[str, Any]],
    provider: str,
    source_path: Path = Path("<memory>"),
) -> PreparedSnapshot:
    """Validate, filter, pivot, and resolve a snapshot without database I/O."""

    normalized_rows, source_rows = _normalize_snapshot_rows(rows)
    source_tours = tuple(
        sorted(
            {
                tour
                for row in normalized_rows
                if (tour := normalize_tour(row.get("league"))) is not None
            }
        )
    )
    reference_tours = tuple(
        sorted(
            {
                tour
                for player in players
                if (tour := normalize_tour(player.get("tour"))) is not None
            }
        )
    )
    eligible: list[dict[str, Any]] = []
    skipped_post_start = 0
    invalid = 0
    for source_row in normalized_rows:
        try:
            captured_at = _parse_datetime(source_row.get("captured_at"))
            start_date = _parse_datetime(source_row.get("start_date"))
            if start_date <= captured_at:
                skipped_post_start += 1
                continue
            row = dict(source_row)
            row["captured_at"] = captured_at
            row["start_date"] = start_date
            if not _clean_text(row.get("player_id")):
                raise ValueError("provider player_id is empty")
            eligible.append(row)
        except (TypeError, ValueError):
            invalid += 1

    pivoted: list[dict[str, Any]] = []
    for row in eligible:
        try:
            # Pivoting is intentionally done after the pre-match filter.
            pivoted = pivot_selections(eligible)
            break
        except (TypeError, ValueError):
            invalid += 1
            break
    if not eligible:
        pivoted = []

    references = _match_reference(matches)
    raw_matches = 0
    normalized_matches = 0
    unresolved_fixture_rows = 0
    unresolved_counter: Counter[tuple[str, str]] = Counter()
    prepared: list[dict[str, Any]] = []

    for row in pivoted:
        source_tour = normalize_tour(row.get("league"))
        raw_index, normalized_index = _name_index(players, tour=source_tour)
        provider_name = _clean_text(row.get("provider_player_name"))
        raw_candidates = raw_index.get(provider_name.casefold(), set())
        if len(raw_candidates) == 1:
            player_id = next(iter(raw_candidates))
            raw_matches += 1
        else:
            normalized_candidates = normalized_index.get(
                normalize_player_name(provider_name), set()
            )
            if len(normalized_candidates) == 1:
                player_id = next(iter(normalized_candidates))
                normalized_matches += 1
            else:
                player_id = None
                unresolved_counter[
                    (provider_name or "<blank>", _clean_text(row.get("league")))
                ] += 1

        home_id, _ = resolve_player_name(
            row.get("home_player"),
            players,
            tour=source_tour,
        )
        away_id, _ = resolve_player_name(
            row.get("away_player"),
            players,
            tour=source_tour,
        )
        match_id = (
            _resolve_fixture(
                row,
                home_id=home_id,
                away_id=away_id,
                selected_player_id=player_id,
                matches=references,
            )
            if player_id is not None
            else None
        )
        # A resolved name by itself is not enough to safely attach odds to a
        # result. Keep both internal keys null until the entire fixture pairs.
        if match_id is None:
            unresolved_fixture_rows += 1
            player_id = None

        prepared.append(
            {
                "match_id": match_id,
                "player_id": player_id,
                "book": _clean_text(row.get("sportsbook")),
                "prop_type": _prop_type(row.get("market")),
                "line": row["line"],
                "over_price": row["over_price"],
                "under_price": row["under_price"],
                "captured_at": row["captured_at"],
                "provider": provider,
                "provider_event_id": _clean_text(row.get("fixture_id")),
                "provider_event_start_at": row["start_date"],
                "provider_market_id": row.get("market_id"),
                "provider_odds_id": row.get("provider_odds_id"),
                "provider_player_id": _clean_text(row.get("provider_player_id")),
                "provider_player_name": provider_name or "<blank>",
                "provider_team_name": None,
                "resolved_at": row["captured_at"] if player_id and match_id else None,
            }
        )

    unresolved_names = tuple(
        UnresolvedName(name, league, count)
        for (name, league), count in sorted(
            unresolved_counter.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )
    )
    report = OddsLoadReport(
        source_path=source_path,
        provider=provider,
        source_rows=source_rows,
        eligible_rows=len(eligible),
        skipped_post_start_rows=skipped_post_start,
        invalid_rows=invalid,
        pivot_rows=len(pivoted),
        rows_written=0,
        raw_name_matches=raw_matches,
        normalized_name_matches=normalized_matches,
        unresolved_name_rows=sum(unresolved_counter.values()),
        unresolved_fixture_rows=unresolved_fixture_rows,
        unresolved_names=unresolved_names,
        alias_collisions=name_alias_collisions(players),
        source_tours=source_tours,
        reference_tours=reference_tours,
    )
    return PreparedSnapshot(tuple(prepared), report)


def _read_snapshot(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        supported = (
            PIVOT_REQUIRED_COLUMNS.issubset(columns)
            or REQUIRED_COLUMNS.issubset(columns)
        )
        missing = REQUIRED_COLUMNS - columns
        missing_description = ", ".join(sorted(missing))
        if PIVOT_REQUIRED_COLUMNS.issubset(columns):
            missing = PIVOT_REQUIRED_COLUMNS - columns
            missing_description = ", ".join(sorted(missing))
        if not supported:
            missing_description = (
                "raw: " + ", ".join(sorted(REQUIRED_COLUMNS - columns))
                + "; pivot: "
                + ", ".join(sorted(PIVOT_REQUIRED_COLUMNS - columns))
            )
        if not supported or missing:
            raise ValueError(
                f"{path}: missing required columns: {missing_description}"
            )
        return [dict(row) for row in reader]


def _reference_rows(connection: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    players = [
        dict(row)
        for row in connection.execute(
            text("SELECT player_id, full_name, tour FROM players")
        ).mappings()
    ]
    matches = [
        dict(row)
        for row in connection.execute(
            text(
                """
                SELECT match_id, event_date, tournament, player_id, opponent_id
                FROM matches
                """
            )
        ).mappings()
    ]
    return players, matches


def _upsert_rows(connection: Any, rows: Sequence[Mapping[str, Any]]) -> int:
    if not rows:
        return 0
    update_by_provider_id = text(
        """
        UPDATE odds
        SET match_id = :match_id,
            player_id = :player_id,
            book = :book,
            prop_type = :prop_type,
            line = :line,
            over_price = :over_price,
            under_price = :under_price,
            captured_at = :captured_at,
            provider_event_start_at = :provider_event_start_at,
            provider_market_id = :provider_market_id,
            provider_odds_id = :provider_odds_id,
             provider_player_id = :provider_player_id,
            provider_player_name = :provider_player_name,
            provider_team_name = :provider_team_name,
            resolved_at = :resolved_at
        WHERE provider = :provider
          AND provider_event_id = :provider_event_id
          AND provider_odds_id = :provider_odds_id
        """
    )
    insert_or_update_snapshot = text(
        """
        INSERT INTO odds (
            match_id, player_id, book, prop_type, line, over_price,
            under_price, captured_at, provider, provider_event_id,
            provider_event_start_at, provider_market_id, provider_odds_id, provider_player_id,
            provider_player_name, provider_team_name, resolved_at
        )
        VALUES (
            :match_id, :player_id, :book, :prop_type, :line, :over_price,
            :under_price, :captured_at, :provider, :provider_event_id,
            :provider_event_start_at, :provider_market_id, :provider_odds_id, :provider_player_id,
            :provider_player_name, :provider_team_name, :resolved_at
        )
        ON CONFLICT (match_id, player_id, book, prop_type, line, captured_at)
        DO UPDATE SET
            match_id = EXCLUDED.match_id,
            player_id = EXCLUDED.player_id,
            book = EXCLUDED.book,
            prop_type = EXCLUDED.prop_type,
            line = EXCLUDED.line,
            over_price = EXCLUDED.over_price,
            under_price = EXCLUDED.under_price,
            captured_at = EXCLUDED.captured_at,
            provider_event_start_at = EXCLUDED.provider_event_start_at,
            provider_market_id = EXCLUDED.provider_market_id,
            provider_odds_id = EXCLUDED.provider_odds_id,
            provider_player_id = EXCLUDED.provider_player_id,
            provider_player_name = EXCLUDED.provider_player_name,
            provider_team_name = EXCLUDED.provider_team_name,
            resolved_at = EXCLUDED.resolved_at
        """
    )
    for row in rows:
        if row.get("provider_odds_id"):
            updated = connection.execute(update_by_provider_id, row)
            if updated.rowcount:
                continue
        connection.execute(insert_or_update_snapshot, row)
    return len(rows)


def _upsert_unresolved_names(
    connection: Any,
    *,
    report: OddsLoadReport,
) -> None:
    if not report.unresolved_names:
        return
    captured_at = datetime.now(timezone.utc)
    connection.execute(
        text(
            """
            INSERT INTO odds_unresolved_names (
                provider, provider_player_name, league, row_count,
                first_seen, last_seen
            )
            VALUES (
                :provider, :provider_player_name, :league, :row_count,
                :first_seen, :last_seen
            )
            ON CONFLICT (provider, provider_player_name, league)
            DO UPDATE SET
                row_count = EXCLUDED.row_count,
                first_seen = LEAST(odds_unresolved_names.first_seen, EXCLUDED.first_seen),
                last_seen = EXCLUDED.last_seen,
                updated_at = CURRENT_TIMESTAMP
            """
        ),
        [
            {
                "provider": report.provider,
                "provider_player_name": item.provider_player_name,
                "league": item.league,
                "row_count": item.row_count,
                "first_seen": captured_at,
                "last_seen": captured_at,
            }
            for item in report.unresolved_names
        ],
    )


def load_snapshot(
    connection: Any,
    path: Path,
    *,
    provider: str = DEFAULT_PROVIDER,
    dry_run: bool = False,
) -> OddsLoadReport:
    """Load one CSV snapshot and return a complete audit report."""

    players, matches = _reference_rows(connection)
    prepared = prepare_snapshot(
        _read_snapshot(path),
        players=players,
        matches=matches,
        provider=provider,
        source_path=path,
    )
    if dry_run:
        return prepared.report
    written = _upsert_rows(connection, prepared.rows)
    _upsert_unresolved_names(connection, report=prepared.report)
    report = prepared.report
    return OddsLoadReport(
        **{
            **report.__dict__,
            "rows_written": written,
        }
    )


def _print_report(report: OddsLoadReport) -> None:
    print(f"\nOdds snapshot: {report.source_path}")
    print(f"source rows: {report.source_rows}")
    print(f"eligible pre-match rows: {report.eligible_rows}")
    print(f"skipped post-start/in-play rows: {report.skipped_post_start_rows}")
    print(f"invalid rows: {report.invalid_rows}")
    print(f"pivoted odds rows: {report.pivot_rows}")
    print(
        f"player match rate before normalization: "
        f"{report.raw_match_rate:.2f}%"
    )
    print(
        f"player match rate after normalization: "
        f"{report.normalized_match_rate:.2f}%"
    )
    print(f"unresolved player-name rows: {report.unresolved_name_rows}")
    print(f"unresolved fixture rows: {report.unresolved_fixture_rows}")
    print(f"source tours: {', '.join(report.source_tours) or '<unknown>'}")
    print(
        "player-reference tours: "
        f"{', '.join(report.reference_tours) or '<unknown>'}"
    )
    print(f"ambiguous normalized aliases: {len(report.alias_collisions)}")
    for collision in report.alias_collisions[:15]:
        print(
            f"  {collision.alias} | "
            f"{', '.join(collision.player_ids)}"
        )
    print(f"odds rows {'computed' if report.rows_written == 0 else 'written'}: {report.rows_written}")
    if report.unresolved_names:
        print("top unresolved provider names:")
        for item in report.unresolved_names[:15]:
            print(
                f"  {item.row_count:>6} rows | {item.league or '<blank>':<12} | "
                f"{item.provider_player_name}"
            )
    else:
        print("top unresolved provider names: none")


def run_archive(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    *,
    provider: str = DEFAULT_PROVIDER,
    dry_run: bool = False,
) -> list[OddsLoadReport]:
    """Load every matching monthly snapshot in deterministic order."""

    paths = sorted(snapshot_dir.glob(SNAPSHOT_PATTERN))
    if not paths:
        raise FileNotFoundError(
            f"No odds snapshots found in {snapshot_dir}; expected "
            "tennis_props_YYYY-MM.csv"
        )
    from db.connection import create_db_engine

    engine = create_db_engine()
    reports: list[OddsLoadReport] = []
    try:
        with engine.begin() as connection:
            for path in paths:
                report = load_snapshot(
                    connection,
                    path,
                    provider=provider,
                    dry_run=dry_run,
                )
                reports.append(report)
                _print_report(report)
    finally:
        engine.dispose()
    return reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_archive(
        args.snapshot_dir,
        provider=args.provider,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())