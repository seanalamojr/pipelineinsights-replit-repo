"""Import verified WTA results for fixtures in a captured odds archive.

WTA match pages supply stable player IDs, match numbers, the actual match date,
final score and winner. Tournament scorecards are used only to find candidates;
the match page must independently confirm the pair and scheduled UTC date.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from html import unescape
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import text

from etl.odds.snapshots import _parse_datetime, normalize_player_name

BASE = "https://www.wtatennis.com"
TOURNAMENTS = {
    "Sao Paulo, Brazil": (1139, "sao-paulo"),
    "Singapore, Singapore": (1152, "singapore"),
    "Seoul, Korea Republic": (1024, "seoul"),
    "Guadalajara, Mexico": (2075, "guadalajara-500"),
}
PLAYER_LINK = re.compile(r'href="/players/(\d+)/([^"/]+)"')
MATCH_LINK = re.compile(r'href="(/tournaments/\d+/[^"/]+/2026/scores/[LR]S\d+)"')
CARD_SPLIT = re.compile(r'<div\s+class="tennis-match js-tennis-match ')
LD_JSON = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S
)
TEAM_ROW = re.compile(
    r'<tr class="match-table__row js-team-[ab]([^"]*)".*?'
    r'href="/players/(\d+)/[^"]+"',
    re.S,
)


@dataclass(frozen=True)
class Fixture:
    event_id: str
    tournament: str
    scheduled_date: date
    home: str
    away: str


@dataclass(frozen=True)
class Result:
    match_id: str
    event_date: date
    tournament: str
    source_url: str
    score: str
    round: str
    players: tuple[tuple[str, str, bool, int, int], ...]  # ID, name, winner, games, sets


def _get(url: str) -> str:
    cache = Path(".cache/wta_results") / (url.removeprefix(BASE).strip("/").replace("/", "_") + ".html")
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for delay in (0, 3, 8, 15):
        if delay:
            time.sleep(delay)
        try:
            with urlopen(request, timeout=35) as response:
                content = response.read().decode("utf-8")
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(content, encoding="utf-8")
            return content
        except HTTPError as error:
            if error.code != 429 or delay == 15:
                raise
    raise RuntimeError(f"Unable to fetch official WTA page: {url}")


def _key(name: str) -> str:
    return normalize_player_name(name).replace(" ", "")


def archive_fixtures(path: Path) -> list[Fixture]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    fixtures: dict[str, Fixture] = {}
    for row in rows:
        if row["league"].strip().upper() != "WTA":
            raise ValueError("WTA results importer requires a WTA-only odds archive")
        fixture = Fixture(
            row["fixture_id"], row["tournament"],
            _parse_datetime(row["start_date"]).date(),
            row["home_player"], row["away_player"],
        )
        if fixture.event_id in fixtures and fixtures[fixture.event_id] != fixture:
            raise ValueError(f"Conflicting provider fixture: {fixture.event_id}")
        fixtures[fixture.event_id] = fixture
    return list(fixtures.values())


def scorecard_candidates(html: str, fixture: Fixture) -> list[str]:
    """Require both full-name slugs in the same singles scorecard."""
    target = {_key(fixture.home), _key(fixture.away)}
    if len(target) != 2:
        return []
    candidates = []
    for card in CARD_SPLIT.split(html)[1:]:
        players = PLAYER_LINK.findall(card)
        links = MATCH_LINK.findall(card)
        if len(players) == 2 and {_key(slug) for _, slug in players} == target and links:
            candidates.append(BASE + links[0])
    return sorted(set(candidates))


def verified_result(html: str, url: str, fixture: Fixture) -> Result | None:
    """Fail closed if the official result doesn't confirm IDs, pair, date and winner."""
    events = []
    for blob in LD_JSON.findall(html):
        data = json.loads(unescape(blob))
        if data.get("@type") == "SportsEvent" and data.get("competitor") and data.get("startDate"):
            events.append(data)
    if len(events) != 1:
        return None
    event = events[0]
    competitors = event["competitor"]
    if len(competitors) != 2:
        return None
    ids = []
    for person in competitors:
        match = re.fullmatch(r"https://www\.wtatennis\.com/players/(\d+)/[^/]+", person.get("@id", ""))
        if not match:
            return None
        ids.append((match[1], person["name"]))
    if {_key(name) for _, name in ids} != {_key(fixture.home), _key(fixture.away)}:
        return None
    if date.fromisoformat(event["startDate"]) != fixture.scheduled_date:
        return None
    props = {item["name"]: item["value"] for item in event.get("additionalProperty", [])}
    score = props.get("Final Score", "")
    match_number = props.get("Match Number", "")
    if not score or not match_number or not url.endswith("/scores/" + match_number):
        return None
    winners = {player_id for state, player_id in TEAM_ROW.findall(html) if "is-winner" in state}
    if len(winners) != 1 or not winners.issubset({player_id for player_id, _ in ids}):
        return None
    # WTA publishes final-score sets from the winner's perspective. Count only
    # complete numeric sets; a retirement/walkover cannot establish prop totals.
    sets = [re.fullmatch(r"(\d+)-(\d+)(?:\(\d+\))?", part.strip())
            for part in score.split(",")]
    if not sets or any(part is None for part in sets):
        return None
    winner_games = sum(int(part[1]) for part in sets)
    loser_games = sum(int(part[2]) for part in sets)
    winner_sets = sum(int(part[1]) > int(part[2]) for part in sets)
    loser_sets = sum(int(part[1]) < int(part[2]) for part in sets)
    if winner_sets <= loser_sets:
        return None
    tourney_id = TOURNAMENTS[fixture.tournament][0]
    return Result(
        f"wta-2026-{tourney_id}-{match_number}", fixture.scheduled_date,
        fixture.tournament, url, score, props.get("Round", ""),
        tuple(
            (player_id, name, player_id in winners,
             winner_games if player_id in winners else loser_games,
             winner_sets if player_id in winners else loser_sets)
            for player_id, name in ids
        ),
    )


def collect_results(fixtures: list[Fixture]) -> tuple[list[Result], dict[str, str]]:
    pages = {}
    for tournament in sorted({f.tournament for f in fixtures}):
        if tournament not in TOURNAMENTS:
            raise ValueError(f"Unknown WTA tournament: {tournament}")
        event_id, slug = TOURNAMENTS[tournament]
        pages[tournament] = _get(f"{BASE}/tournaments/{event_id}/{slug}/2026/scores")
    candidates = {}
    unresolved = {}
    for fixture in fixtures:
        links = scorecard_candidates(pages[fixture.tournament], fixture)
        if len(links) == 1:
            candidates[fixture.event_id] = links[0]
        else:
            unresolved[fixture.event_id] = f"scorecard candidates: {len(links)}"
    with ThreadPoolExecutor(max_workers=2) as pool:
        pages_by_url = dict(zip(
            sorted(set(candidates.values())),
            pool.map(_get, sorted(set(candidates.values()))),
        ))
    results = []
    for fixture in fixtures:
        url = candidates.get(fixture.event_id)
        if not url:
            continue
        result = verified_result(pages_by_url[url], url, fixture)
        if result is None:
            unresolved[fixture.event_id] = "official page did not confirm pair, date, score and winner"
        else:
            results.append(result)
    if len({r.match_id for r in results}) != len(results):
        raise ValueError("Multiple provider fixtures mapped to the same official WTA match")
    return results, unresolved


def import_results(connection: object, results: list[Result]) -> None:
    for result in results:
        for player_id, name, is_winner, games, sets_won in result.players:
            internal_id = f"wta-{player_id}"
            connection.execute(text("""
                INSERT INTO players (player_id, full_name, tour)
                VALUES (:id, :name, 'WTA')
                ON CONFLICT (player_id) DO UPDATE
                SET full_name = EXCLUDED.full_name
                WHERE players.tour = 'WTA'
            """), {"id": internal_id, "name": name})
        for player_id, name, is_winner, games, sets_won in result.players:
            internal_id = f"wta-{player_id}"
            opponent = next(p for p, *_ in result.players if p != player_id)
            connection.execute(text("""
                INSERT INTO matches
                    (match_id, event_date, tourney_date, tournament, round,
                     player_id, opponent_id, is_winner, score, games_won,
                     sets_won, match_completed)
                VALUES
                    (:match_id, :event_date, :event_date, :tournament, :round,
                     :player_id, :opponent_id, :is_winner, :score, :games,
                     :sets_won, TRUE)
                ON CONFLICT (match_id, player_id) DO UPDATE SET
                    event_date = EXCLUDED.event_date,
                    opponent_id = EXCLUDED.opponent_id,
                    is_winner = EXCLUDED.is_winner,
                    score = EXCLUDED.score,
                    games_won = EXCLUDED.games_won,
                    sets_won = EXCLUDED.sets_won
            """), {
                "match_id": result.match_id, "event_date": result.event_date,
                "tournament": result.tournament, "round": result.round,
                "player_id": internal_id, "opponent_id": f"wta-{opponent}",
                "is_winner": is_winner, "score": result.score,
                "games": games, "sets_won": sets_won,
            })
        connection.execute(text("""
            INSERT INTO wta_match_sources (match_id, source_url, final_score)
            VALUES (:id, :url, :score)
            ON CONFLICT (match_id) DO UPDATE SET
                source_url = EXCLUDED.source_url, final_score = EXCLUDED.final_score
        """), {"id": result.match_id, "url": result.source_url, "score": result.score})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Captured WTA odds CSV (raw or pivoted)")
    parser.add_argument("--provider", default="free_tier_odds_api")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    fixtures = archive_fixtures(args.archive)
    results, unresolved = collect_results(fixtures)
    print(f"Verified WTA fixtures: {len(results)}/{len(fixtures)}")
    for event_id, reason in sorted(unresolved.items()):
        print(f"  unresolved {event_id}: {reason}")
    if args.dry_run:
        return
    from db.connection import create_db_engine
    from etl.odds.snapshots import load_snapshot
    engine = create_db_engine()
    try:
        with engine.begin() as connection:
            import_results(connection, results)
            report = load_snapshot(connection, args.archive, provider=args.provider)
            # The unresolved-name register is a current queue, not a permanent
            # list of names already paired by the verified WTA import.
            connection.execute(text("""
                DELETE FROM odds_unresolved_names n
                WHERE n.provider = :provider AND lower(n.league) = 'wta'
                  AND NOT EXISTS (
                      SELECT 1 FROM odds o
                      WHERE o.provider = n.provider
                        AND o.provider_player_name = n.provider_player_name
                        AND o.match_id IS NULL
                  )
            """), {"provider": args.provider})
            paired = connection.execute(text("""
                SELECT count(*) FILTER (WHERE match_id IS NOT NULL),
                       count(*) FILTER (WHERE match_id IS NULL)
                FROM odds WHERE provider = :provider
            """), {"provider": args.provider}).one()
            visible = connection.execute(text("""
                SELECT count(*) FROM vw_wta_odds_results WHERE provider = :provider
            """), {"provider": args.provider}).scalar_one()
            if visible != paired[0]:
                raise RuntimeError("Paired odds are not all visible in the WTA reporting view")
            print(f"Odds pivot rows: {report.pivot_rows}; paired: {paired[0]}; "
                  f"unresolved: {paired[1]}; reporting view paired rows: {visible}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()