from pathlib import Path

import yaml
import pytest
from pydantic import ValidationError

from config._schema import validate_sport_config


def test_tennis_config_uses_normalized_targets() -> None:
    raw = yaml.safe_load(Path("config/tennis.yaml").read_text(encoding="utf-8"))
    config = validate_sport_config(raw)

    assert config.sport == "tennis"
    assert config.source.matches == "sackmann_kadantte"
    assert config.stat_targets == ["aces", "double_faults", "service_games"]
    assert set(config.features.targets) == set(config.stat_targets)
    assert "games_won" in config.disabled_stat_targets
    assert config.features.feature_version
    assert config.features.baseline is not None
    assert config.features.baseline.base_window == 10
    assert config.features.baseline.minimum_group_size == 30
    assert config.backtest is not None
    assert config.backtest.step_months == 1


def _valid_config() -> dict:
    return {
        "sport": "tennis",
        "source": {"matches": "sackmann", "odds": "provider"},
        "stat_targets": ["aces"],
        "features": {
            "rolling_windows": [3, 5],
            "include": ["rolling_mean"],
            "feature_version": "tennis_features_v1",
            "targets": {"aces": {}},
        },
    }


def test_empty_stat_targets_fail_validation() -> None:
    raw = _valid_config()
    raw["stat_targets"] = []

    with pytest.raises(ValidationError):
        validate_sport_config(raw)


def test_missing_feature_version_fails_validation() -> None:
    raw = _valid_config()
    del raw["features"]["feature_version"]

    with pytest.raises(ValidationError):
        validate_sport_config(raw)


def test_unrecognized_sport_value_fails_validation() -> None:
    raw = _valid_config()
    raw["sport"] = "tennis++"

    with pytest.raises(ValidationError):
        validate_sport_config(raw)


def test_stat_target_without_feature_definition_fails_validation() -> None:
    raw = _valid_config()
    raw["stat_targets"] = ["aces", "double_faults"]

    with pytest.raises(ValidationError, match="missing feature definitions"):
        validate_sport_config(raw)


def test_inactive_feature_target_fails_validation() -> None:
    raw = _valid_config()
    raw["features"]["targets"]["double_faults"] = {}

    with pytest.raises(ValidationError, match="inactive targets"):
        validate_sport_config(raw)


def test_active_and_disabled_target_overlap_fails_validation() -> None:
    raw = _valid_config()
    raw["disabled_stat_targets"] = ["aces"]

    with pytest.raises(ValidationError, match="overlap"):
        validate_sport_config(raw)


def _ensemble_config(members: list[dict[str, object]]) -> dict:
    raw = _valid_config()
    raw["ensemble"] = {
        "targets": {
            "aces": {
                "members": members,
            }
        }
    }
    return raw


def test_ensemble_weights_must_sum_to_one() -> None:
    with pytest.raises(ValidationError, match="sum to 1.0"):
        validate_sport_config(
            _ensemble_config(
                [
                    {"modelversion": "baseline_v1_aces", "weight": 0.6},
                    {"modelversion": "gbm_v1_aces", "weight": 0.6},
                ]
            )
        )


def test_ensemble_rejects_unknown_member_modelversion() -> None:
    with pytest.raises(ValidationError, match="does not produce"):
        validate_sport_config(
            _ensemble_config(
                [
                    {"modelversion": "baseline_v1_aces", "weight": 0.5},
                    {"modelversion": "unknown_v1_aces", "weight": 0.5},
                ]
            )
        )