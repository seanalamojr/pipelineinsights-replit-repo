"""Run the real tennis pipeline while proving demo rows remain unchanged.

Example:
    python -m scripts.run_pipeline \
        --seasons 2015-2025 \
        --attached-file attached_assets/2026_1789695249523.csv \
        --attached-file attached_assets/2026_challenger_1789695253916.csv
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence

from db.connection import create_db_engine
from db.migrate import apply_migrations
from etl.tennis.sackmann import (
    DEFAULT_CACHE_DIR,
    MAX_CURRENT_SEASON_AGE_DAYS,
    load_attached_files,
    load_seasons,
    parse_seasons,
)
from features.build_features import build_and_store
from models.baseline import (
    BASELINE_MODEL_PREFIX,
    load_raw_config,
    run_baseline,
)
from models.ensemble import ENSEMBLE_MODEL_PREFIX, run_ensemble
from models.gbm import GBM_MODEL_PREFIX, run_gbm
from config._schema import validate_sport_config


DEFAULT_CONFIG = Path("config/tennis.yaml")
COUNT_TABLES = (
    "players",
    "matches",
    "player_game_features",
    "player_prop_predictions",
)


@dataclass(frozen=True)
class RowCounts:
    total: int
    real: int
    demo: int


def collect_row_counts() -> dict[str, RowCounts]:
    """Return real/demo counts from the player-keyed pipeline tables."""

    from sqlalchemy import text

    engine = create_db_engine()
    counts: dict[str, RowCounts] = {}
    try:
        with engine.connect() as connection:
            for table in COUNT_TABLES:
                row = connection.execute(
                    text(
                        f"""
                        SELECT
                            COUNT(*) AS total,
                            COUNT(*) FILTER (
                                WHERE player_id NOT LIKE 'demo_%%'
                            ) AS real_rows,
                            COUNT(*) FILTER (
                                WHERE player_id LIKE 'demo_%%'
                            ) AS demo_rows
                        FROM {table}
                        """
                    )
                ).one()
                counts[table] = RowCounts(
                    total=int(row.total),
                    real=int(row.real_rows),
                    demo=int(row.demo_rows),
                )
    finally:
        engine.dispose()
    return counts


def expected_model_versions(
    config_path: Path,
    targets: Sequence[str] | None,
) -> tuple[str, ...]:
    validated = validate_sport_config(load_raw_config(config_path))
    requested_targets = tuple(targets or validated.stat_targets)
    unknown = sorted(set(requested_targets) - set(validated.stat_targets))
    if unknown:
        raise ValueError(f"Unknown target(s): {', '.join(unknown)}")
    return tuple(
        f"{prefix}_{target}"
        for target in requested_targets
        for prefix in (
            BASELINE_MODEL_PREFIX,
            GBM_MODEL_PREFIX,
            ENSEMBLE_MODEL_PREFIX,
        )
    )


def existing_real_prediction_versions(
    modelversions: Sequence[str],
) -> dict[str, int]:
    if not modelversions:
        return {}
    from sqlalchemy import bindparam, text

    statement = text(
        """
        SELECT modelversion, COUNT(*) AS row_count
        FROM player_prop_predictions
        WHERE player_id NOT LIKE 'demo_%%'
          AND modelversion IN :modelversions
        GROUP BY modelversion
        ORDER BY modelversion
        """
    ).bindparams(bindparam("modelversions", expanding=True))
    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                statement,
                {"modelversions": list(modelversions)},
            )
            return {
                str(row.modelversion): int(row.row_count)
                for row in rows
            }
    finally:
        engine.dispose()


def assert_demo_counts_unchanged(
    before: dict[str, RowCounts],
    after: dict[str, RowCounts],
) -> None:
    changed = {
        table: (before[table].demo, after[table].demo)
        for table in COUNT_TABLES
        if before[table].demo != after[table].demo
    }
    if changed:
        details = ", ".join(
            f"{table}: {old} -> {new}"
            for table, (old, new) in changed.items()
        )
        raise AssertionError(f"Real pipeline changed demo row counts: {details}")


def _print_counts(label: str, counts: dict[str, RowCounts]) -> None:
    print(f"\n{label} row counts")
    for table in COUNT_TABLES:
        count = counts[table]
        print(
            f"  {table}: total={count.total}, "
            f"real={count.real}, demo={count.demo}"
        )


def run_pipeline(
    config_path: Path = DEFAULT_CONFIG,
    *,
    seasons: Sequence[int] = (),
    attached_files: Sequence[Path] = (),
    attached_season: int | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    refresh: bool = False,
    inspect_player: str = "Novak Djokovic",
    inspect_season: int | None = None,
    max_current_season_age_days: int = MAX_CURRENT_SEASON_AGE_DAYS,
    targets: Sequence[str] | None = None,
    skip_etl: bool = False,
    skip_features: bool = False,
    write_predictions: bool = False,
) -> dict[str, RowCounts]:
    """Execute migrations, real ETL, features, and configured models."""

    if not skip_etl and not seasons and not attached_files:
        raise ValueError(
            "Provide --seasons and/or --attached-file, or use --skip-etl "
            "to rebuild from real rows already in the database."
        )

    applied, skipped = apply_migrations()
    print(
        f"Migrations: applied={len(applied)}, already applied={len(skipped)}"
    )
    before = collect_row_counts()
    _print_counts("Before real pipeline", before)
    modelversions = expected_model_versions(config_path, targets)
    existing_versions = existing_real_prediction_versions(modelversions)
    if write_predictions and existing_versions:
        details = ", ".join(
            f"{modelversion}={row_count}"
            for modelversion, row_count in existing_versions.items()
        )
        raise RuntimeError(
            "Refusing to overwrite existing real prediction versions: "
            f"{details}. Create new model versions before persisting another run."
        )

    if skip_etl:
        print("\nETL: skipped; using existing non-demo database rows")
    else:
        if seasons:
            load_seasons(
                seasons,
                cache_dir=cache_dir,
                refresh=refresh,
                inspect_player=inspect_player,
                inspect_season=inspect_season,
                max_current_season_age_days=max_current_season_age_days,
            )
        if attached_files:
            load_attached_files(
                attached_files,
                season=attached_season or date.today().year,
                inspect_player=inspect_player,
                inspect_season=inspect_season,
                max_current_season_age_days=max_current_season_age_days,
            )

    if skip_features:
        if before["player_game_features"].real == 0:
            raise RuntimeError(
                "Cannot skip features because no real feature rows exist"
            )
        print("\nFeatures: skipped; using existing non-demo feature rows")
    else:
        print("\nFeatures: rebuilding real player-game features")
        build_and_store(config_path)
    model_dry_run = not write_predictions
    mode = "writing" if write_predictions else "verifying without writing"
    print(f"\nBaseline: {mode} real predictions")
    run_baseline(config_path, targets=targets, dry_run=model_dry_run)
    print(f"\nGBM: {mode} real predictions and walk-forward evidence")
    run_gbm(config_path, targets=targets, dry_run=model_dry_run)
    print(f"\nEnsemble: {mode} persisted member predictions")
    run_ensemble(config_path, targets=targets, dry_run=model_dry_run)

    after = collect_row_counts()
    _print_counts("After real pipeline", after)
    assert_demo_counts_unchanged(before, after)
    empty = [table for table in COUNT_TABLES if after[table].real == 0]
    if empty:
        raise AssertionError(
            "Real pipeline completed without real rows in: "
            + ", ".join(empty)
        )
    print("\nDemo preservation check: PASS")
    return after


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--seasons",
        type=parse_seasons,
        default=(),
        help="Historical season list or range, such as 2015-2025.",
    )
    parser.add_argument(
        "--attached-file",
        action="append",
        type=Path,
        default=[],
        help="Current-season ATP/Challenger CSV; repeat as needed.",
    )
    parser.add_argument("--attached-season", type=int)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--inspect-player", default="Novak Djokovic")
    parser.add_argument("--inspect-season", type=int)
    parser.add_argument(
        "--max-current-season-age-days",
        type=int,
        default=MAX_CURRENT_SEASON_AGE_DAYS,
    )
    parser.add_argument("--target", action="append", dest="targets")
    parser.add_argument(
        "--skip-etl",
        action="store_true",
        help="Use existing real match rows and rerun features/models only.",
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Use existing real feature rows and rerun model verification only.",
    )
    parser.add_argument(
        "--write-predictions",
        action="store_true",
        help=(
            "Persist model outputs. Refuses to run when any requested "
            "modelversion already has real rows."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_pipeline(
        args.config,
        seasons=args.seasons,
        attached_files=args.attached_file,
        attached_season=args.attached_season,
        cache_dir=args.cache_dir,
        refresh=args.refresh,
        inspect_player=args.inspect_player,
        inspect_season=args.inspect_season,
        max_current_season_age_days=args.max_current_season_age_days,
        targets=args.targets,
        skip_etl=args.skip_etl,
        skip_features=args.skip_features,
        write_predictions=args.write_predictions,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())