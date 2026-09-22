from pathlib import Path

import pytest

from scripts import run_pipeline


def _counts(
    *,
    real_matches: int = 10,
    demo_matches: int = 2,
) -> dict[str, run_pipeline.RowCounts]:
    return {
        "players": run_pipeline.RowCounts(7, 5, 2),
        "matches": run_pipeline.RowCounts(
            real_matches + demo_matches,
            real_matches,
            demo_matches,
        ),
        "player_game_features": run_pipeline.RowCounts(32, 30, 2),
        "player_prop_predictions": run_pipeline.RowCounts(42, 40, 2),
    }


def test_real_pipeline_runs_stages_in_dependency_order(monkeypatch) -> None:
    calls: list[object] = []
    count_snapshots = iter([_counts(), _counts(real_matches=12)])

    monkeypatch.setattr(
        run_pipeline,
        "apply_migrations",
        lambda: ([], ["001_core_tables"]),
    )
    monkeypatch.setattr(
        run_pipeline,
        "collect_row_counts",
        lambda: next(count_snapshots),
    )
    monkeypatch.setattr(
        run_pipeline,
        "expected_model_versions",
        lambda config, targets: ("baseline_v1_aces",),
    )
    monkeypatch.setattr(
        run_pipeline,
        "existing_real_prediction_versions",
        lambda versions: {"baseline_v1_aces": 40},
    )
    monkeypatch.setattr(
        run_pipeline,
        "load_seasons",
        lambda seasons, **kwargs: calls.append(("seasons", tuple(seasons))),
    )
    monkeypatch.setattr(
        run_pipeline,
        "load_attached_files",
        lambda paths, **kwargs: calls.append(
            ("attached", tuple(Path(path).name for path in paths))
        ),
    )
    monkeypatch.setattr(
        run_pipeline,
        "build_and_store",
        lambda config: calls.append("features"),
    )
    monkeypatch.setattr(
        run_pipeline,
        "run_baseline",
        lambda config, **kwargs: calls.append("baseline"),
    )
    monkeypatch.setattr(
        run_pipeline,
        "run_gbm",
        lambda config, **kwargs: calls.append("gbm"),
    )
    monkeypatch.setattr(
        run_pipeline,
        "run_ensemble",
        lambda config, **kwargs: calls.append("ensemble"),
    )

    result = run_pipeline.run_pipeline(
        seasons=(2025,),
        attached_files=(Path("current.csv"),),
        attached_season=2026,
        targets=("aces",),
    )

    assert calls == [
        ("seasons", (2025,)),
        ("attached", ("current.csv",)),
        "features",
        "baseline",
        "gbm",
        "ensemble",
    ]
    assert result["matches"].real == 12


def test_real_pipeline_requires_an_explicit_etl_source() -> None:
    with pytest.raises(ValueError, match="Provide --seasons"):
        run_pipeline.run_pipeline()


def test_demo_count_changes_fail_the_run() -> None:
    before = _counts()
    after = _counts(demo_matches=3)

    with pytest.raises(AssertionError, match="matches: 2 -> 3"):
        run_pipeline.assert_demo_counts_unchanged(before, after)


def test_prediction_writes_refuse_existing_real_versions(monkeypatch) -> None:
    monkeypatch.setattr(
        run_pipeline,
        "apply_migrations",
        lambda: ([], ["001_core_tables"]),
    )
    monkeypatch.setattr(run_pipeline, "collect_row_counts", _counts)
    monkeypatch.setattr(
        run_pipeline,
        "expected_model_versions",
        lambda config, targets: ("baseline_v1_aces",),
    )
    monkeypatch.setattr(
        run_pipeline,
        "existing_real_prediction_versions",
        lambda versions: {"baseline_v1_aces": 40},
    )

    with pytest.raises(
        RuntimeError,
        match="Refusing to overwrite existing real prediction versions",
    ):
        run_pipeline.run_pipeline(
            skip_etl=True,
            skip_features=True,
            targets=("aces",),
            write_predictions=True,
        )