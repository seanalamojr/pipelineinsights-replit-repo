"""Validation boundary for sport configuration files.

The schema is intentionally small at checkpoint 1. Later sport configs can add
source- and feature-specific values without making downstream code sport-specific.
"""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceConfig(BaseModel):
    """Names of the upstream sources used by a sport's ETL layer."""

    model_config = ConfigDict(extra="allow")

    matches: str
    odds: str


class BaselineConfig(BaseModel):
    """Configuration for the deliberately simple checkpoint baseline."""

    base_window: int = Field(ge=1)
    context_columns: list[str] = Field(min_length=1)
    minimum_group_size: int = Field(ge=1)


class BacktestConfig(BaseModel):
    """Default time boundaries for walk-forward evaluation."""

    start_date: date
    end_date: date
    step_months: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_date_range(self) -> "BacktestConfig":
        if self.end_date <= self.start_date:
            raise ValueError("backtest.end_date must be after backtest.start_date")
        return self


class GbmConfig(BaseModel):
    """Configurable LightGBM quantile-model contract."""

    quantiles: list[float] = Field(min_length=3)
    features: dict[str, list[str]] = Field(min_length=1)
    categorical_features: list[str] = Field(default_factory=list)
    validation_fraction: float = Field(gt=0, lt=1)
    early_stopping_rounds: int = Field(ge=1)
    params: dict[str, Any] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_quantiles(self) -> "GbmConfig":
        if len(set(self.quantiles)) != len(self.quantiles):
            raise ValueError("gbm.quantiles must not contain duplicates")
        if any(quantile <= 0 or quantile >= 1 for quantile in self.quantiles):
            raise ValueError("gbm.quantiles must be strictly between 0 and 1")
        if self.quantiles != sorted(self.quantiles):
            raise ValueError("gbm.quantiles must be sorted from low to high")
        missing_categories = set(self.categorical_features) - {
            feature
            for features in self.features.values()
            for feature in features
        }
        if missing_categories:
            raise ValueError(
                "gbm.categorical_features are not selected features: "
                + ", ".join(sorted(missing_categories))
            )
        return self


class EnsembleMemberConfig(BaseModel):
    """One versioned prediction source and its configured starting weight."""

    modelversion: str = Field(min_length=1)
    weight: float = Field(gt=0)


class EnsembleTargetConfig(BaseModel):
    """Ensemble members for one stat target."""

    members: list[EnsembleMemberConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_weights(self) -> "EnsembleTargetConfig":
        total = sum(member.weight for member in self.members)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                "ensemble member weights must sum to 1.0 within 1e-6"
            )
        versions = [member.modelversion for member in self.members]
        if len(set(versions)) != len(versions):
            raise ValueError("ensemble member modelversion values must be unique")
        return self


class EnsembleConfig(BaseModel):
    """Walk-forward weighted ensemble contract."""

    missing_member_policy: Literal["renormalize", "emit_none"] = "renormalize"
    oof_objective: Literal["absolute", "squared"] = "absolute"
    targets: dict[str, EnsembleTargetConfig] = Field(min_length=1)


class FeatureConfig(BaseModel):
    """Feature-engineering inputs shared by all sports."""

    model_config = ConfigDict(extra="allow")

    rolling_windows: list[int] = Field(min_length=1)
    include: list[str] = Field(min_length=1)
    feature_version: str = Field(min_length=1)
    minimum_history: int = Field(default=5, ge=1)
    date_tie_policy: str = "prior_event_dates_only"
    targets: dict[str, dict[str, Any]] = Field(default_factory=dict)
    baseline: BaselineConfig | None = None


class SportConfig(BaseModel):
    """Minimum contract every sport configuration must satisfy."""

    model_config = ConfigDict(extra="allow")

    sport: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    source: SourceConfig
    stat_targets: list[str] = Field(min_length=1)
    disabled_stat_targets: list[str] = Field(default_factory=list)
    value_edge_threshold: float = Field(default=0.5, gt=0)
    features: FeatureConfig
    backtest: BacktestConfig | None = None
    gbm: GbmConfig | None = None
    ensemble: EnsembleConfig | None = None

    @model_validator(mode="after")
    def validate_stat_target_contract(self) -> "SportConfig":
        active = set(self.stat_targets)
        configured = set(self.features.targets)
        disabled = set(self.disabled_stat_targets)
        missing = sorted(active - configured)
        extra = sorted(configured - active)
        overlap = sorted(active & disabled)
        errors: list[str] = []
        if missing:
            errors.append(
                f"stat_targets missing feature definitions: {', '.join(missing)}"
            )
        if extra:
            errors.append(
                f"features.targets contains inactive targets: {', '.join(extra)}"
            )
        if overlap:
            errors.append(
                "stat_targets and disabled_stat_targets overlap: "
                + ", ".join(overlap)
            )
        if self.ensemble is not None:
            ensemble_targets = set(self.ensemble.targets)
            missing_ensemble_targets = sorted(active - ensemble_targets)
            extra_ensemble_targets = sorted(ensemble_targets - active)
            if missing_ensemble_targets:
                errors.append(
                    "ensemble is missing target definitions: "
                    + ", ".join(missing_ensemble_targets)
                )
            if extra_ensemble_targets:
                errors.append(
                    "ensemble has inactive target definitions: "
                    + ", ".join(extra_ensemble_targets)
                )
            for target, ensemble_target in self.ensemble.targets.items():
                if target not in active:
                    continue
                produced_versions = {f"baseline_v1_{target}"}
                if self.gbm is not None:
                    produced_versions.add(f"gbm_v1_{target}")
                unknown_members = sorted(
                    {
                        member.modelversion
                        for member in ensemble_target.members
                        if member.modelversion not in produced_versions
                    }
                )
                if unknown_members:
                    errors.append(
                        f"ensemble target {target} references modelversion values "
                        "the pipeline does not produce: "
                        + ", ".join(unknown_members)
                    )
        if errors:
            raise ValueError("; ".join(errors))
        return self


def validate_sport_config(raw_config: dict[str, Any]) -> SportConfig:
    """Validate a parsed YAML mapping and return a typed config."""

    return SportConfig.model_validate(raw_config)