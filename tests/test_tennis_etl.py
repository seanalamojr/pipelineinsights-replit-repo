from pathlib import Path
from datetime import date

import pytest
import etl.tennis.sackmann as sackmann
from etl.tennis.sackmann import (
    REQUIRED_COLUMNS,
    _aggregate_season,
    _aggregate_attached_files,
    read_season_rows,
    transform_sackmann_row,
)


def _source_row(**overrides: str) -> dict[str, str]:
    row = {
        "tourney_id": "2015-001",
        "tourney_name": "Test Open",
        "surface": "Hard",
        "draw_size": "32",
        "tourney_level": "A",
        "tourney_date": "20150101",
        "match_num": "1",
        "winner_id": "100001",
        "winner_seed": "1",
        "winner_entry": "",
        "winner_name": "Winner One",
        "winner_hand": "R",
        "winner_ht": "190",
        "winner_ioc": "USA",
        "winner_age": "25.5",
        "winner_rank": "1",
        "winner_rank_points": "9000",
        "loser_id": "100002",
        "loser_seed": "",
        "loser_entry": "",
        "loser_name": "Loser Two",
        "loser_hand": "L",
        "loser_ht": "185",
        "loser_ioc": "ESP",
        "loser_age": "24.5",
        "loser_rank": "10",
        "loser_rank_points": "3000",
        "score": "6-4 6-3",
        "best_of": "3",
        "round": "R32",
        "minutes": "90",
        "w_ace": "8",
        "w_df": "2",
        "w_svpt": "60",
        "w_1stIn": "40",
        "w_1stWon": "30",
        "w_2ndWon": "10",
        "w_SvGms": "9",
        "w_bpSaved": "1",
        "w_bpFaced": "2",
        "l_ace": "",
        "l_df": "3",
        "l_svpt": "50",
        "l_1stIn": "30",
        "l_1stWon": "20",
        "l_2ndWon": "8",
        "l_SvGms": "8",
        "l_bpSaved": "0",
        "l_bpFaced": "1",
    }
    row.update(overrides)
    return row


def test_every_sackmann_input_row_expands_to_two_player_rows() -> None:
    source_rows = [
        _source_row(),
        _source_row(
            match_num="2",
            score="6-4 2-1 RET",
            w_ace="",
            surface="",
        ),
    ]

    output_rows = [
        player_row
        for source_row in source_rows
        for player_row in transform_sackmann_row(source_row)
    ]

    assert len(output_rows) == len(source_rows) * 2
    assert output_rows[0]["match_id"] == output_rows[1]["match_id"]
    assert output_rows[2]["match_completed"] is False
    assert output_rows[2]["aces"] is None


def test_break_points_won_uses_the_opponent_column_prefix() -> None:
    winner, loser = transform_sackmann_row(
        _source_row(
            w_bpFaced="4",
            w_bpSaved="3",
            l_bpFaced="7",
            l_bpSaved="5",
        )
    )

    assert winner["break_points_won"] == 2
    assert loser["break_points_won"] == 1


def test_qualifier_seed_is_missing_numeric_metadata_not_a_bad_match() -> None:
    winner, loser = transform_sackmann_row(_source_row(loser_seed="Q"))

    assert winner["player_seed"] == 1
    assert loser["player_seed"] is None


def test_impossible_service_stats_are_stored_as_missing() -> None:
    winner, loser = transform_sackmann_row(
        _source_row(
            w_svpt="0",
            w_1stIn="94",
            w_ace="7",
            l_svpt="79",
            l_df="124",
        )
    )

    for row in (winner, loser):
        assert row["aces"] is None
        assert row["double_faults"] is None
        assert row["serve_points"] is None
        assert row["first_serves_in"] is None
        assert row["bp_faced"] is None


def test_kadantte_sackmann_rows_keep_the_same_contract(tmp_path: Path) -> None:
    source_path = tmp_path / "atp_matches_2018.csv"
    source_path.write_text(
        ",".join(sorted(REQUIRED_COLUMNS))
        + "\n"
        + ",".join(
            {
                **{column: "" for column in REQUIRED_COLUMNS},
                **_source_row(
                    tourney_id="2018-001",
                    tourney_date="20180101",
                    score="6-4 2-1 RET",
                    w_ace="",
                    l_ace="4",
                ),
            }[column]
            for column in sorted(REQUIRED_COLUMNS)
        )
        + "\n",
        encoding="utf-8",
    )

    rows = list(read_season_rows(source_path))
    snapshots: dict[str, dict[str, object]] = {}
    report, output_rows = _aggregate_season(
        2018,
        source_path,
        snapshots,
        source="Kadantte/tennis_atp",
    )

    assert len(rows) == 1
    assert report.source == "Kadantte/tennis_atp"
    assert report.source_rows == 1
    assert report.output_rows == 2
    assert report.non_null_ace_rows == 1
    assert report.incomplete_matches == 1
    assert report.min_event_date is not None
    assert report.min_event_date == report.max_event_date
    assert {row["player_id"] for row in output_rows} == {"100001", "100002"}


def test_download_uses_the_configured_kadantte_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return b"tourney_id\n"

    def fake_urlopen(request, timeout: int):
        del timeout
        calls.append(request.full_url)
        return _Response()

    monkeypatch.setattr(sackmann, "urlopen", fake_urlopen)
    path, source = sackmann._download_season(
        2018,
        cache_dir=tmp_path,
        refresh=True,
    )

    assert path.read_bytes() == b"tourney_id\n"
    assert source == "Kadantte/tennis_atp"
    assert calls == [sackmann.SOURCE_URL_TEMPLATE.format(year=2018)]


def test_attached_files_preserve_conflicting_match_keys(tmp_path: Path) -> None:
    source_path = tmp_path / "current.csv"
    rows = [
        _source_row(
            tourney_id="2026-001",
            tourney_date="20260101",
            winner_id="100001",
            loser_id="100002",
        ),
        _source_row(
            tourney_id="2026-001",
            tourney_date="20260102",
            winner_id="100003",
            loser_id="100004",
        ),
    ]
    source_path.write_text(
        ",".join(sorted(REQUIRED_COLUMNS))
        + "\n"
        + "\n".join(
            ",".join({**{column: "" for column in REQUIRED_COLUMNS}, **row}[column]
                      for column in sorted(REQUIRED_COLUMNS))
            for row in rows
        )
        + "\n",
        encoding="utf-8",
    )

    reports, output_rows, duplicate_rows = _aggregate_attached_files(
        [source_path],
        season=2026,
    )

    assert reports[0].source_rows == 2
    assert duplicate_rows == 0
    assert len(output_rows) == 4
    assert {
        str(row["match_id"])
        for row in output_rows
    } == {
        "2026-001-1",
        "2026-001-1-20260102-100003-100004",
    }


def test_attached_files_report_rows_without_stable_player_ids(tmp_path: Path) -> None:
    source_path = tmp_path / "current.csv"
    row = _source_row(
        tourney_id="2026-002",
        loser_id="",
    )
    source_path.write_text(
        ",".join(sorted(REQUIRED_COLUMNS))
        + "\n"
        + ",".join(
            {**{column: "" for column in REQUIRED_COLUMNS}, **row}[column]
            for column in sorted(REQUIRED_COLUMNS)
        )
        + "\n",
        encoding="utf-8",
    )

    reports, output_rows, duplicate_rows = _aggregate_attached_files(
        [source_path],
        season=2026,
    )

    assert reports[0].invalid_rows == 1
    assert output_rows == []
    assert duplicate_rows == 0


def test_current_season_freshness_guard_rejects_stale_data() -> None:
    report = sackmann.SeasonStats(
        season=2026,
        source_rows=1,
        output_rows=2,
        non_null_ace_rows=2,
        incomplete_matches=0,
        null_surface_matches=0,
        min_event_date=date(2026, 1, 1),
        max_event_date=date(2026, 5, 25),
    )

    with pytest.raises(RuntimeError, match="source data is"):
        sackmann.assert_current_season_fresh(
            [report],
            today=date(2026, 9, 17),
        )