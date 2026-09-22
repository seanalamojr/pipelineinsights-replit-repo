from datetime import date, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest
import yaml

from evaluation.backtest import (
    BacktestSettings,
    accumulate_ensemble_fold_history,
    build_ensemble_oof_inputs,
    assert_future_cutoff,
    build_walk_forward_folds,
    calibration_by_prediction_bin,
    fit_baseline_fold,
    Fold,
    prepare_backtest_predictions,
    run_ensemble_backtest,
    score_predictions,
    shuffled_target_sabotage,
)
from models.baseline import BaselineSettings
from models.baseline import insert_backtest_predictions
from models.ensemble import EnsembleMember, EnsembleSettings


def _settings() -> BaselineSettings:
    return BaselineSettings(
        target="aces",
        feature_version="test_v1",
        base_window=10,
        context_columns=("surface",),
        minimum_group_size=1,
    )


def _frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for index in range(12):
        surface = "Grass" if index < 6 else "Clay"
        rows.append(
            {
                "player_id": f"p{index}",
                "match_id": f"m{index}",
                "event_date": date(2024, 1, 1) + timedelta(days=index),
                "sport": "tennis",
                "stat_target": "aces",
                "target_value": 10.0 if surface == "Grass" else 1.0,
                "has_sufficient_history": True,
                "is_training_eligible": True,
                "rolling_mean_10": 5.0,
                "rolling_std_10": 1.0,
                "surface": surface,
            }
        )
    rows.extend(
        [
            {
                "player_id": "p_test_grass",
                "match_id": "m_test_grass",
                "event_date": date(2024, 2, 1),
                "sport": "tennis",
                "stat_target": "aces",
                "target_value": 10.0,
                "has_sufficient_history": True,
                "is_training_eligible": False,
                "rolling_mean_10": 5.0,
                "rolling_std_10": 1.0,
                "surface": "Grass",
            },
            {
                "player_id": "p_test_clay",
                "match_id": "m_test_clay",
                "event_date": date(2024, 2, 1),
                "sport": "tennis",
                "stat_target": "aces",
                "target_value": 1.0,
                "has_sufficient_history": True,
                "is_training_eligible": False,
                "rolling_mean_10": 5.0,
                "rolling_std_10": 1.0,
                "surface": "Clay",
            },
        ]
    )
    return pd.DataFrame(rows)


def test_tennis_config_has_walk_forward_defaults() -> None:
    raw = yaml.safe_load(open("config/tennis.yaml", encoding="utf-8"))

    assert raw["backtest"]["step_months"] == 1
    assert raw["backtest"]["end_date"] > raw["backtest"]["start_date"]


def test_future_cutoff_rejects_lookahead_training_rows() -> None:
    frame = _frame()

    assert_future_cutoff(frame.iloc[:2], date(2024, 2, 1))
    with pytest.raises(AssertionError, match="on or after cutoff"):
        assert_future_cutoff(frame.iloc[:2], date(2024, 1, 2))


def test_ensemble_fold_history_appends_only_after_current_fold_is_scored() -> None:
    prior_predictions: dict[str, list[pd.DataFrame]] = {
        "baseline_v1_aces": [],
        "gbm_v1_aces": [],
    }
    prior_tests: list[pd.DataFrame] = []
    current_predictions = {
        "baseline_v1_aces": pd.DataFrame(
            {"player_id": ["p-current"], "match_id": ["m-current"], "prediction": [1.0]}
        ),
        "gbm_v1_aces": pd.DataFrame(
            {"player_id": ["p-current"], "match_id": ["m-current"], "prediction": [2.0]}
        ),
    }
    current_test = pd.DataFrame(
        {
            "player_id": ["p-current"],
            "match_id": ["m-current"],
            "target_value": [1.5],
        }
    )

    assert prior_tests == []
    assert all(not frames for frames in prior_predictions.values())

    next_predictions, next_tests = accumulate_ensemble_fold_history(
        prior_predictions,
        prior_tests,
        fold_predictions=current_predictions,
        fold_test=current_test,
    )

    assert prior_tests == []
    assert all(not frames for frames in prior_predictions.values())
    assert len(next_tests) == 1
    assert all(len(frames) == 1 for frames in next_predictions.values())
    assert next_tests[0]["match_id"].tolist() == ["m-current"]


def test_ensemble_oof_inputs_exclude_the_fold_being_scored() -> None:
    prior = {
        "baseline_v1_aces": [
            pd.DataFrame(
                {
                    "player_id": ["p-prior"],
                    "match_id": ["m-prior"],
                    "prediction": [1.0],
                }
            )
        ],
        "gbm_v1_aces": [
            pd.DataFrame(
                {
                    "player_id": ["p-prior"],
                    "match_id": ["m-prior"],
                    "prediction": [2.0],
                }
            )
        ],
    }
    current = {
        modelversion: frame.assign(
            player_id="p-current",
            match_id="m-current",
        )
        for modelversion, frame in (
            ("baseline_v1_aces", prior["baseline_v1_aces"][0]),
            ("gbm_v1_aces", prior["gbm_v1_aces"][0]),
        )
    }
    current_test = pd.DataFrame(
        {
            "player_id": ["p-current"],
            "match_id": ["m-current"],
            "target_value": [100.0],
        }
    )

    fitting_predictions, fitting_actuals = build_ensemble_oof_inputs(
        prior,
        [
            pd.DataFrame(
                {
                    "player_id": ["p-prior"],
                    "match_id": ["m-prior"],
                    "target_value": [1.5],
                }
            )
        ],
        current_predictions=current,
        current_test=current_test,
    )

    assert set(fitting_actuals["match_id"]) == {"m-prior"}
    assert all(set(frame["match_id"]) == {"m-prior"} for frame in fitting_predictions.values())


def test_each_scored_fold_is_accumulated_only_after_its_weights_are_fit() -> None:
    history = {
        "baseline_v1_aces": [],
        "gbm_v1_aces": [],
    }
    prior_tests: list[pd.DataFrame] = []

    for fold_number in range(1, 4):
        match_id = f"m-{fold_number}"
        current_predictions = {
            modelversion: pd.DataFrame(
                {
                    "player_id": [f"p-{fold_number}"],
                    "match_id": [match_id],
                    "prediction": [float(fold_number)],
                }
            )
            for modelversion in history
        }
        current_test = pd.DataFrame(
            {
                "player_id": [f"p-{fold_number}"],
                "match_id": [match_id],
                "target_value": [float(fold_number)],
            }
        )

        fitting_predictions, fitting_actuals = build_ensemble_oof_inputs(
            history,
            prior_tests,
            current_predictions=current_predictions,
            current_test=current_test,
        )

        expected_prior_ids = {f"m-{number}" for number in range(1, fold_number)}
        assert set(fitting_actuals.get("match_id", [])) == expected_prior_ids
        assert match_id not in set(fitting_actuals.get("match_id", []))
        assert all(
            set(frame.get("match_id", [])) == expected_prior_ids
            and match_id not in set(frame.get("match_id", []))
            for frame in fitting_predictions.values()
        )

        history, prior_tests = accumulate_ensemble_fold_history(
            history,
            prior_tests,
            fold_predictions=current_predictions,
            fold_test=current_test,
        )


def test_run_ensemble_backtest_fits_each_fold_from_earlier_scored_rows_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    folds = []
    for fold_number in range(1, 4):
        test = pd.DataFrame(
            {
                "player_id": [f"p-{fold_number}"],
                "match_id": [f"m-{fold_number}"],
                "event_date": [date(2024, fold_number + 1, 1)],
                "target_value": [float(fold_number)],
            }
        )
        folds.append(
            Fold(
                fold_number=fold_number,
                cutoff_date=date(2024, fold_number + 1, 1),
                test_end_date=date(2024, fold_number + 2, 1),
                training=pd.DataFrame({"training": [True]}),
                test=test,
            )
        )

    ensemble_settings = EnsembleSettings(
        target="aces",
        sport="tennis",
        members=(
            EnsembleMember("baseline_v1_aces", 0.5),
            EnsembleMember("gbm_v1_aces", 0.5),
        ),
        missing_member_policy="renormalize",
    )

    def predictions_for(test: pd.DataFrame, modelversion: str) -> pd.DataFrame:
        offset = 0.5 if modelversion.startswith("baseline") else 1.0
        return pd.DataFrame(
            {
                "player_id": test["player_id"],
                "match_id": test["match_id"],
                "prediction": test["target_value"] + offset,
                "lowerci": test["target_value"] - 1.0,
                "upperci": test["target_value"] + 1.0,
                "modelversion": modelversion,
            }
        )

    class FakeConnection:
        def __enter__(self) -> "FakeConnection":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    class FakeEngine:
        def begin(self) -> FakeConnection:
            return FakeConnection()

        def dispose(self) -> None:
            return None

    import db.connection
    import models.ensemble
    import models.gbm

    monkeypatch.setattr(
        "evaluation.backtest.load_raw_config",
        lambda _path: {},
    )
    monkeypatch.setattr(
        "evaluation.backtest.validate_sport_config",
        lambda _raw: SimpleNamespace(
            sport="tennis",
            stat_targets=("aces",),
            gbm=object(),
            ensemble=object(),
        ),
    )
    monkeypatch.setattr(
        "evaluation.backtest.backtest_settings_for_config",
        lambda *_args, **_kwargs: BacktestSettings(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 5, 1),
            step_months=1,
        ),
    )
    monkeypatch.setattr(
        "evaluation.backtest.baseline_settings_for_target",
        lambda *_args: _settings(),
    )
    monkeypatch.setattr(
        "evaluation.backtest.load_feature_rows",
        lambda *_args, **_kwargs: pd.DataFrame(),
    )
    monkeypatch.setattr(
        "evaluation.backtest._expand_feature_values",
        lambda frame: frame,
    )
    monkeypatch.setattr(
        "evaluation.backtest.build_walk_forward_folds",
        lambda *_args: folds,
    )
    monkeypatch.setattr(
        "evaluation.backtest.fit_baseline_fold",
        lambda _training, test, _settings: predictions_for(
            test, "baseline_v1_aces"
        ),
    )
    monkeypatch.setattr(
        models.gbm,
        "gbm_settings_for_target",
        lambda *_args: object(),
    )
    monkeypatch.setattr(
        models.gbm,
        "fit_gbm_fold",
        lambda _training, test, _settings: predictions_for(test, "gbm_v1_aces"),
    )
    monkeypatch.setattr(
        models.ensemble,
        "ensemble_settings_for_target",
        lambda *_args: ensemble_settings,
    )
    monkeypatch.setattr(db.connection, "create_db_engine", FakeEngine)

    observed: list[tuple[int, set[str]]] = []

    def observe_fit(
        fold: Fold,
        _predictions: dict[str, pd.DataFrame],
        actuals: pd.DataFrame,
    ) -> None:
        observed.append((fold.fold_number, set(actuals.get("match_id", []))))

    run_ensemble_backtest(
        targets=["aces"],
        dry_run=True,
        oof_fit_observer=observe_fit,
    )

    assert observed == [
        (1, set()),
        (2, {"m-1"}),
        (3, {"m-1", "m-2"}),
    ]
    assert all(f"m-{fold_number}" not in match_ids for fold_number, match_ids in observed)


def test_walk_forward_training_rows_are_strictly_before_each_cutoff() -> None:
    folds = build_walk_forward_folds(
        _frame(),
        BacktestSettings(
            start_date=date(2024, 1, 5),
            end_date=date(2024, 3, 1),
            step_months=1,
        ),
    )

    assert len(folds) == 2
    for fold in folds:
        assert (fold.training["event_date"] < fold.cutoff_date).all()
        assert (fold.test["event_date"] >= fold.cutoff_date).all()
        assert (fold.test["event_date"] < fold.test_end_date).all()


def test_metrics_include_bias_and_identical_baseline_row_set() -> None:
    frame = _frame()
    training = frame.iloc[:12]
    test = frame.iloc[12:]
    predictions = fit_baseline_fold(training, test, _settings())

    score = score_predictions(predictions, predictions, test)

    assert score.row_counts["mae"] == 2
    assert score.metrics["mae"] == pytest.approx(0.5)
    assert score.metrics["rmse"] == pytest.approx(0.6460304729)
    assert score.metrics["mean_bias"] == pytest.approx(-0.5)
    assert score.metrics["mae_improvement_over_baseline"] == pytest.approx(0.0)
    assert score.metrics["interval_crossing_count"] == 0
    assert score.metrics["interval_repair_count"] == 0


def test_interval_crossings_are_repaired_and_counted() -> None:
    test = pd.DataFrame(
        {
            "player_id": ["p1"],
            "match_id": ["m1"],
            "target_value": [3.0],
        }
    )
    predictions = pd.DataFrame(
        {
            "player_id": ["p1"],
            "match_id": ["m1"],
            "prediction": [3.0],
            "lowerci": [5.0],
            "upperci": [1.0],
        }
    )
    baseline = predictions.assign(lowerci=1.0, upperci=5.0)

    score = score_predictions(predictions, baseline, test)

    assert score.metrics["interval_crossing_count"] == 1
    assert score.metrics["interval_repair_count"] == 1
    assert score.scored.loc[0, "lowerci"] == pytest.approx(1.0)
    assert score.scored.loc[0, "upperci"] == pytest.approx(5.0)


def test_backtest_predictions_carry_fold_provenance_and_run_version() -> None:
    frame = _frame()
    training = frame.iloc[:12]
    test = frame.iloc[12:]
    fold = Fold(
        fold_number=7,
        cutoff_date=date(2024, 2, 1),
        test_end_date=date(2024, 3, 1),
        training=training,
        test=test,
    )
    predictions = fit_baseline_fold(training, test, _settings())
    score = score_predictions(predictions, predictions, test)

    persisted = prepare_backtest_predictions(
        score,
        fold,
        sport="tennis",
        target="aces",
        model_prefix="baseline_v1",
        run_timestamp=pd.Timestamp("2026-09-21T00:00:00Z").to_pydatetime(),
    )

    assert len(persisted) == len(test)
    assert persisted["fold_number"].eq(7).all()
    assert persisted["fold_cutoff_date"].eq(date(2024, 1, 31)).all()
    assert persisted["fold_cutoff_date"].max() < test["event_date"].min()
    assert persisted["fold_test_end_date"].eq(date(2024, 3, 1)).all()
    assert persisted["modelversion"].str.startswith(
        "baseline_v1_aces_backtest_"
    ).all()
    assert not persisted["modelversion"].eq("baseline_v1_aces").any()


def test_historical_prediction_insert_is_append_only() -> None:
    class CapturingConnection:
        def __init__(self) -> None:
            self.statement = ""
            self.rows: list[dict[str, object]] = []

        def execute(self, statement: object, rows: list[dict[str, object]]) -> None:
            self.statement = str(statement)
            self.rows = rows

    historical = pd.DataFrame(
        [
            {
                "player_id": "p1",
                "match_id": "m1",
                "sport": "tennis",
                "prop_type": "aces",
                "prediction": 4.0,
                "lowerci": 2.0,
                "upperci": 6.0,
                "modelversion": "baseline_v1_aces_backtest_20260921T000000000000Z",
                "predictiontimestamp": pd.Timestamp("2026-09-21T00:00:00Z"),
                "fold_number": 2,
                "fold_cutoff_date": date(2024, 2, 1),
                "fold_test_end_date": date(2024, 3, 1),
            }
        ]
    )
    connection = CapturingConnection()

    written = insert_backtest_predictions(connection, historical)

    assert written == 1
    assert "ON CONFLICT" not in connection.statement
    assert connection.rows[0]["fold_number"] == 2


def test_historical_prediction_insert_rejects_live_versions() -> None:
    live = pd.DataFrame(
        [
            {
                "player_id": "p1",
                "match_id": "m1",
                "sport": "tennis",
                "prop_type": "aces",
                "prediction": 4.0,
                "lowerci": 2.0,
                "upperci": 6.0,
                "modelversion": "baseline_v1_aces",
                "predictiontimestamp": pd.Timestamp("2026-09-21T00:00:00Z"),
                "fold_number": 2,
                "fold_cutoff_date": date(2024, 2, 1),
                "fold_test_end_date": date(2024, 3, 1),
            }
        ]
    )

    with pytest.raises(ValueError, match="run-specific backtest version"):
        insert_backtest_predictions(object(), live)


def test_backtest_provenance_rejects_rows_outside_test_window() -> None:
    frame = _frame()
    training = frame.iloc[:12]
    test = frame.iloc[12:].copy()
    test.loc[test.index[0], "event_date"] = date(2024, 1, 31)
    fold = Fold(
        fold_number=1,
        cutoff_date=date(2024, 2, 1),
        test_end_date=date(2024, 3, 1),
        training=training,
        test=test,
    )
    predictions = fit_baseline_fold(training, test, _settings())
    score = score_predictions(predictions, predictions, test)

    with pytest.raises(AssertionError, match="outside fold test window"):
        prepare_backtest_predictions(
            score,
            fold,
            sport="tennis",
            target="aces",
            model_prefix="baseline_v1",
            run_timestamp=pd.Timestamp("2026-09-21T00:00:00Z").to_pydatetime(),
        )


def test_improvement_compares_against_baseline_predictions() -> None:
    frame = _frame()
    training = frame.iloc[:12]
    test = frame.iloc[12:]
    baseline = fit_baseline_fold(training, test, _settings())
    improved = baseline.copy()
    improved["prediction"] = test["target_value"].to_numpy()

    score = score_predictions(improved, baseline, test)

    assert score.metrics["mae"] == pytest.approx(0.0)
    assert score.metrics["mae_improvement_over_baseline"] > 0


def test_calibration_by_prediction_bin_handles_tied_predictions() -> None:
    scored = pd.DataFrame(
        {
            "prediction": [1.0, 1.0, 2.0, 3.0],
            "lowerci": [0.0, 0.0, 1.0, 2.0],
            "upperci": [2.0, 2.0, 3.0, 4.0],
            "target_value": [1.0, 4.0, 2.0, 9.0],
        }
    )

    bins = calibration_by_prediction_bin(scored, bin_count=2)

    assert [item["row_count"] for item in bins] == [2, 2]
    assert [item["coverage"] for item in bins] == [0.5, 0.5]


def test_context_adjustments_respond_to_training_labels() -> None:
    # The baseline's base value comes from player_game_features rather than
    # training labels. Shuffling labels only perturbs context multipliers, so
    # this is not a general leakage test for the baseline.
    frame = _frame()
    ordinary_mae, shuffled_mae = shuffled_target_sabotage(
        frame.iloc[:12],
        frame.iloc[12:],
        _settings(),
        random_state=4,
    )

    assert ordinary_mae == pytest.approx(0.5)
    assert shuffled_mae > ordinary_mae + 1.0