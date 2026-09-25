import json
from datetime import date

from etl.tennis.wta_results import Fixture, scorecard_candidates, verified_result


FIXTURE = Fixture(
    "fixture-1", "Sao Paulo, Brazil", date(2026, 9, 18),
    "Anna Blinkova", "Alina Charaeva",
)
URL = "https://www.wtatennis.com/tournaments/1139/sao-paulo/2026/scores/LS005"


def _page(*, date_string="2026-09-18", score="6-4,7-5"):
    event = {
        "@type": "SportsEvent", "startDate": date_string,
        "competitor": [
            {"@id": "https://www.wtatennis.com/players/324267/anna-blinkova",
             "name": "Anna Blinkova"},
            {"@id": "https://www.wtatennis.com/players/329198/alina-charaeva",
             "name": "Alina Charaeva"},
        ],
        "additionalProperty": [
            {"name": "Match Number", "value": "LS005"},
            {"name": "Final Score", "value": score},
        ],
    }
    return (f'<script type="application/ld+json">{json.dumps(event)}</script>'
            '<tr class="match-table__row js-team-a is-winner">'
            '<a href="/players/324267/anna-blinkova"></a></tr>'
            '<tr class="match-table__row js-team-b ">'
            '<a href="/players/329198/alina-charaeva"></a></tr>')


def test_official_result_requires_date_pair_winner_and_complete_score():
    result = verified_result(_page(), URL, FIXTURE)
    assert result is not None
    assert result.match_id == "wta-2026-1139-LS005"
    assert result.players == (
        ("324267", "Anna Blinkova", True, 13, 2),
        ("329198", "Alina Charaeva", False, 9, 0),
    )
    assert verified_result(_page(date_string="2026-09-19"), URL, FIXTURE) is None
    assert verified_result(_page(score="RET"), URL, FIXTURE) is None
    assert verified_result(_page(), URL, Fixture(
        "fixture-1", "Sao Paulo, Brazil", date(2026, 9, 18),
        "Anna Blinkova", "Different Opponent",
    )) is None


def test_scorecard_requires_both_players_in_same_card():
    page = (f'<div class="tennis-match js-tennis-match '
            f'href="/players/324267/anna-blinkova" '
            f'href="/players/329198/alina-charaeva" '
            f'href="/tournaments/1139/sao-paulo/2026/scores/LS005"')
    assert scorecard_candidates(page, FIXTURE) == [URL]
    assert scorecard_candidates(page.replace("alina-charaeva", "other-player"), FIXTURE) == []