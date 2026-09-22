"""Apply only unapplied, ordered PipelineInsights SQL migrations."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, text

MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def apply_migrations() -> tuple[list[str], list[str]]:
    """Apply unapplied migrations and return (applied, skipped) names."""

    from db.connection import get_engine

    migration_files = sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    if not migration_files:
        raise RuntimeError(f"No migration files found in {MIGRATIONS_DIR}")

    applied: list[str] = []
    skipped: list[str] = []
    with get_engine().begin() as connection:
        has_tracking_table = inspect(connection).has_table(
            "pipelineinsights_schema_migrations"
        )
        for migration_file in migration_files:
            version = migration_file.stem
            if has_tracking_table:
                already_applied = connection.execute(
                    text(
                        "SELECT 1 FROM pipelineinsights_schema_migrations "
                        "WHERE version = :version"
                    ),
                    {"version": version},
                ).scalar_one_or_none()
                if already_applied is not None:
                    skipped.append(version)
                    continue
            elif version != "001_core_tables":
                raise RuntimeError(
                    "Migration tracking table is missing before the first migration."
                )

            connection.exec_driver_sql(
                migration_file.read_text(encoding="utf-8")
            )
            applied.append(version)
            has_tracking_table = True
    return applied, skipped


if __name__ == "__main__":
    try:
        applied, skipped = apply_migrations()
        print(
            f"Applied {len(applied)} migrations: "
            f"{', '.join(applied) if applied else 'none'}"
        )
        print(
            f"Skipped {len(skipped)} migrations: "
            f"{', '.join(skipped) if skipped else 'none'}"
        )
    except Exception as error:
        raise SystemExit(f"Migration failed: {error}") from error