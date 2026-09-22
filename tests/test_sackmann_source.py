from datetime import date

from etl.tennis.sackmann import (
    DEFAULT_SEASONS,
    SOURCE_REPOSITORY,
    SOURCE_URL_TEMPLATE,
)


def test_sackmann_source_uses_kadantte_repository() -> None:
    assert SOURCE_REPOSITORY == "Kadantte/tennis_atp"
    assert "Kadantte/tennis_atp" in SOURCE_URL_TEMPLATE


def test_default_sackmann_seasons_include_current_year() -> None:
    assert date.today().year in DEFAULT_SEASONS