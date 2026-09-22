from datetime import datetime, timezone

import pandas as pd
import pytest

from models.ensemble import (
    EnsembleMember,
    EnsembleSettings,
    combine_predictions,
    fit_oof_weights,
)


def _settings(policy: str = "renormalize") -> EnsembleSettings:
    return EnsembleSettings(
        target="aces",
        sport="tennis",
        members=(
            EnsembleMember("baseline_v1_aces", 0.5),
            EnsembleMember("gbm_v1_aces", 0.5),
        ),
        missing_member_policy=policy,
        oof_objective="absolute",
    )


def _member_frame(
    modelversion: str,
    rows: list[tuple[str, float, float, float]],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": player_id,
                "match_id": f"m_{player_id}",
                "sport": "tennis",
                "prop_type": "aces",
                "prediction": prediction,
                "lowerci": lower,
                "upperci": upper,
                "modelversion": modelversion,
            }
            for player_id, prediction, lower, upper in rows
        ]
    )


def test_weight_one_reproduces_member_predictions_exactly() -> None:
    settings = EnsembleSettings(
        target="aces",
        sport="tennis",
        members=(EnsembleMember("baseline_v1_aces", 1.0),),
        missing_member_policy="renormalize",
    )
    member = _member_frame(
        "baseline_v1_aces",
        [("p1", 7.25, 5.0, 9.5), ("p2", 3.0, 1.0, 4.0)],
    )

    result = combine_predictions(
        {"baseline_v1_aces": member},
        settings,
        predictiontimestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    pd.testing.assert_series_equal(
        result.predictions.sort_values("player_id")["prediction"].reset_index(
            drop=True
        ),
        member.sort_values("player_id")["prediction"].reset_index(drop=True),
        check_names=False,
    )


def test_missing_member_is_renormalized_without_treating_it_as_zero() -> None:
    settings = _settings()
    baseline = _member_frame("baseline_v1_aces", [("p1", 8.0, 6.0, 10.0)])
    gbm = _member_frame("gbm_v1_aces", [("p2", 4.0, 2.0, 6.0)])

    result = combine_predictions(
        {"baseline_v1_aces": baseline, "gbm_v1_aces": gbm},
        settings,
    )

    values = result.predictions.set_index("player_id")["prediction"]
    assert values["p1"] == pytest.approx(8.0)
    assert values["p2"] == pytest.approx(4.0)
    assert result.renormalized_rows == 2
    assert result.skipped_rows == 0


def test_emit_none_skips_rows_with_missing_members() -> None:
    settings = _settings("emit_none")
    baseline = _member_frame("baseline_v1_aces", [("p1", 8.0, 6.0, 10.0)])
    gbm = _member_frame("gbm_v1_aces", [("p2", 4.0, 2.0, 6.0)])

    result = combine_predictions(
        {"baseline_v1_aces": baseline, "gbm_v1_aces": gbm},
        settings,
    )

    assert result.predictions.empty
    assert result.skipped_rows == 2
    assert (
        result.complete_rows + result.renormalized_rows + result.skipped_rows
        == result.rows_read
    )


def test_oof_weights_depend_on_earlier_outcomes_and_exclude_scored_fold() -> None:
    settings = _settings()
    earlier = {
        "baseline_v1_aces": _member_frame(
            "baseline_v1_aces",
            [("p1", 8.0, 6.0, 10.0), ("p2", 8.0, 6.0, 10.0)],
        ),
        "gbm_v1_aces": _member_frame(
            "gbm_v1_aces",
            [("p1", 4.0, 2.0, 6.0), ("p2", 4.0, 2.0, 6.0)],
        ),
    }
    earlier_actual = pd.DataFrame(
        [
            {"player_id": "p1", "match_id": "m_p1", "target_value": 8.0},
            {"player_id": "p2", "match_id": "m_p2", "target_value": 8.0},
        ]
    )
    current_actual = pd.DataFrame(
        [
            {"player_id": "p3", "match_id": "m_p3", "target_value": 4.0},
        ]
    )

    weights_before = fit_oof_weights(earlier, earlier_actual, settings)
    changed_earlier_actual = earlier_actual.copy()
    changed_earlier_actual.loc[0, "target_value"] = 4.0
    weights_changed = fit_oof_weights(
        earlier,
        changed_earlier_actual,
        settings,
    )
    with_current_fold = {
        modelversion: pd.concat(
            [frame, _member_frame(modelversion, [("p3", 8.0 if "baseline" in modelversion else 2.0, 0.0, 0.0)])],
            ignore_index=True,
        )
        for modelversion, frame in earlier.items()
    }
    with_current_actual = pd.concat(
        [earlier_actual, current_actual],
        ignore_index=True,
    )
    weights_with_current = fit_oof_weights(
        with_current_fold,
        with_current_actual,
        settings,
    )

    assert weights_before != weights_changed
    assert weights_before != weights_with_current
    assert set(weights_before) == {
        "baseline_v1_aces",
        "gbm_v1_aces",
    }