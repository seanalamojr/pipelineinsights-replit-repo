"""One-time, additive transfer of the real PipelineInsights snapshot.

Run from the development workspace. DATABASE_URL is the development source;
PIPELINEINSIGHTS_PRODUCTION_DATABASE_URL is a temporary development-only secret
pointing at the existing production database. No data or connection URLs are
written to disk by this script. The default mode is read-only.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

import psycopg
from psycopg import IsolationLevel
from psycopg import sql


@dataclass(frozen=True)
class Table:
    name: str
    real_only: bool = True
    sequence_column: str | None = None
    real_model_only: bool = False
    include_unresolved: bool = False


# Foreign-key order: the view is derived and must NOT be imported.
TABLES = (
    Table("prop_types", real_only=False),
    Table("players"),
    Table("matches"),
    Table("player_game_features"),
    Table("odds", sequence_column="odds_id", include_unresolved=True),
    Table("player_prop_predictions", sequence_column="prediction_id"),
    Table("injuries", sequence_column="injury_id"),
    Table(
        "model_backtest_results",
        real_only=False,
        sequence_column="result_id",
        real_model_only=True,
    ),
    Table(
        "model_feature_importances",
        real_only=False,
        sequence_column="importance_id",
        real_model_only=True,
    ),
)
PREDICATE = sql.SQL("LEFT(player_id, 5) <> 'demo_'")
REAL_MODEL_PREDICATE = sql.SQL(
    "modelversion IN (SELECT DISTINCT modelversion FROM public.player_prop_predictions "
    "WHERE LEFT(player_id, 5) <> 'demo_')"
)
REQUIRED_VIEW_COLUMNS = {
    "prediction_id", "player_id", "player", "tour", "match_id", "event_date",
    "tournament", "surface", "sport", "prop_type", "prediction", "lowerci",
    "upperci", "modelversion", "predictiontimestamp", "book", "line",
    "over_price", "under_price", "captured_at", "edge", "side", "opponent",
    "matchup", "status", "actual_value", "rolling_average",
}


def selected_rows(table: Table, *, source: bool) -> sql.Composable:
    if table.real_only:
        if table.include_unresolved:
            return sql.SQL("(player_id IS NULL OR LEFT(player_id, 5) <> 'demo_')")
        return PREDICATE
    if table.real_model_only and source:
        return REAL_MODEL_PREDICATE
    return sql.SQL("TRUE")


def count_rows(
    connection: psycopg.Connection, table: Table, *, source: bool = False
) -> tuple[int, int]:
    query = sql.SQL(
        "SELECT COUNT(*)::bigint, COUNT(*) FILTER (WHERE {})::bigint "
        "FROM public.{}"
    ).format(selected_rows(table, source=source), sql.Identifier(table.name))
    with connection.cursor() as cursor:
        cursor.execute(query)
        total, selected = cursor.fetchone()
    return total, selected


def columns(connection: psycopg.Connection, table: Table) -> tuple[tuple[str, str], ...]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table.name,),
        )
        return tuple(cursor.fetchall())


def identity(connection: psycopg.Connection) -> tuple[str, str, int, str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database(), COALESCE(inet_server_addr()::text, ''), "
            "COALESCE(inet_server_port(), 0), current_user"
        )
        return cursor.fetchone()


def check_reporting_view(connection: psycopg.Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'vw_fact_player_prop_odds'"
        )
        available = {row[0] for row in cursor.fetchall()}
    missing = REQUIRED_VIEW_COLUMNS - available
    if missing:
        raise RuntimeError(
            "Reporting view lacks API-required columns: "
            + ", ".join(sorted(missing))
        )


def view_definition(connection: psycopg.Connection) -> str:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_get_viewdef('public.vw_fact_player_prop_odds'::regclass, true)"
        )
        return cursor.fetchone()[0]


def audit(
    source: psycopg.Connection, target: psycopg.Connection | None
) -> dict[str, tuple[int, int, int, int]]:
    if target is not None and identity(source) == identity(target):
        raise RuntimeError("Source and target resolve to the same database; stopped.")
    check_reporting_view(source)
    if target is not None:
        check_reporting_view(target)
        if view_definition(source) != view_definition(target):
            print(
                "WARNING: Production reporting view differs from Preview. "
                "Dry-run can continue, but --apply will refuse to import."
            )

    result: dict[str, tuple[int, int, int, int]] = {}
    for table in TABLES:
        source_cols = columns(source, table)
        if not source_cols:
            raise RuntimeError(f"Source table {table.name} is missing.")
        if target is not None and source_cols != columns(target, table):
            raise RuntimeError(f"Source/target columns differ for {table.name}; stopped.")

        source_total, selected = count_rows(source, table, source=True)
        target_total, existing = count_rows(target, table) if target else (0, 0)
        result[table.name] = (source_total, selected, target_total, existing)
        print(
            f"{table.name}: development {source_total} total / {selected} to copy; "
            f"production {target_total} total / {existing} in transfer scope"
            if target
            else f"{table.name}: development {source_total} total / {selected} to copy"
        )

    if result["player_prop_predictions"][1] == 0:
        raise RuntimeError("No real predictions in development; stopped.")
    if target is not None:
        existing = [name for name, (_, _, _, count) in result.items() if count]
        if existing:
            raise RuntimeError(
                "Production already has rows in the transfer scope ("
                + ", ".join(existing)
                + "); this one-time importer refuses to merge or overwrite them."
            )
    return result


def transfer_table(
    source: psycopg.Connection, target: psycopg.Connection, table: Table
) -> None:
    names = [name for name, _ in columns(source, table)]
    projected = sql.SQL(", ").join(map(sql.Identifier, names))
    export = sql.SQL(
        "COPY (SELECT {} FROM public.{} WHERE {}) TO STDOUT WITH (FORMAT CSV)"
    ).format(projected, sql.Identifier(table.name), selected_rows(table, source=True))
    load = sql.SQL("COPY public.{} ({}) FROM STDIN WITH (FORMAT CSV)").format(
        sql.Identifier(table.name), projected
    )
    with source.cursor() as reader, target.cursor() as writer:
        with reader.copy(export) as outbound, writer.copy(load) as inbound:
            for chunk in outbound:
                inbound.write(chunk)


def advance_sequence(target: psycopg.Connection, table: Table) -> None:
    if table.sequence_column is None:
        return
    relation = f"public.{table.name}"
    with target.cursor() as cursor:
        cursor.execute(
            "SELECT pg_get_serial_sequence(%s, %s)",
            (relation, table.sequence_column),
        )
        sequence = cursor.fetchone()[0]
        if sequence:
            cursor.execute(
                sql.SQL("SELECT last_value, is_called FROM {}").format(
                    sql.Identifier(*sequence.split("."))
                )
            )
            last_value, is_called = cursor.fetchone()
            cursor.execute(
                sql.SQL("SELECT MAX({}) FROM public.{}").format(
                    sql.Identifier(table.sequence_column), sql.Identifier(table.name)
                )
            )
            maximum = cursor.fetchone()[0]
            if maximum is not None and (
                maximum > last_value or (maximum == last_value and not is_called)
            ):
                # setval is not transactional. Only move forwards; a later
                # rollback may leave gaps, but cannot make IDs collide.
                cursor.execute("SELECT setval(%s::regclass, %s, true)", (sequence, maximum))


def apply(
    source: psycopg.Connection,
    target: psycopg.Connection,
    baseline: dict[str, tuple[int, int, int, int]],
) -> None:
    # The caller holds a single target transaction. Any error before commit
    # rolls back all copied rows; nothing is deleted or updated.
    with target.cursor() as cursor:
        for table in TABLES:
            cursor.execute(
                sql.SQL("LOCK TABLE public.{} IN SHARE ROW EXCLUSIVE MODE").format(
                    sql.Identifier(table.name)
                )
            )
    # Re-audit under locks so a concurrent import cannot race the preflight.
    if audit(source, target) != baseline:
        raise RuntimeError("Data changed since preflight; stopped without importing.")

    for table in TABLES:
        expected = baseline[table.name][1]
        print(f"Copying {table.name}: {expected} rows...")
        transfer_table(source, target, table)
        after_total, after_selected = count_rows(target, table)
        if after_total != baseline[table.name][2] + expected or after_selected != expected:
            raise RuntimeError(f"Count mismatch for {table.name}; rolling back.")

    # Exercise the headline reporting aggregates, not just a single row.
    # The target may have an older view definition, so compare its output.
    reporting_query = (
        "SELECT COUNT(DISTINCT prediction_id)::bigint, "
        "COUNT(DISTINCT (match_id, player_id, prop_type))::bigint "
        "FROM vw_fact_player_prop_odds "
        "WHERE LEFT(player_id, 5) <> 'demo_'"
    )
    with source.cursor() as source_cursor, target.cursor() as target_cursor:
        target_cursor.execute("SET LOCAL statement_timeout = '120s'")
        source_cursor.execute(reporting_query)
        expected = source_cursor.fetchone()
        target_cursor.execute(reporting_query)
        actual = target_cursor.fetchone()
        if expected[0] == 0 or actual != expected:
            raise RuntimeError(
                "Reporting totals do not match Preview; rolling back. "
                f"Development={expected}, production={actual}."
            )
    for table in TABLES:
        advance_sequence(target, table)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-only", action="store_true", help="Audit development without connecting to production"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Copy data into production; dry-run is the default"
    )
    parser.add_argument(
        "--backup-confirmed",
        action="store_true",
        help="Confirm an independently verified production recovery/backup plan",
    )
    args = parser.parse_args()
    if args.source_only and args.apply:
        parser.error("--source-only and --apply cannot be combined")
    if args.apply and not args.backup_confirmed:
        parser.error("--apply requires --backup-confirmed")
    source_url = os.getenv("DATABASE_URL")
    target_url = os.getenv("PIPELINEINSIGHTS_PRODUCTION_DATABASE_URL")
    if not source_url:
        parser.error("The development DATABASE_URL is unavailable.")
    if not args.source_only and not target_url:
        parser.error(
            "Set PIPELINEINSIGHTS_PRODUCTION_DATABASE_URL as a temporary "
            "development-only Secret before connecting to production."
        )
    if target_url and source_url == target_url and not args.source_only:
        parser.error("Source and target URL are identical.")

    try:
        with psycopg.connect(source_url) as source:
            # Every table is copied from one stable, read-only source snapshot.
            source.read_only = True
            source.isolation_level = IsolationLevel.REPEATABLE_READ
            if args.source_only:
                audit(source, None)
                return 0
            with psycopg.connect(target_url) as target:
                if not args.apply:
                    target.read_only = True
                baseline = audit(source, target)
                if not args.apply:
                    print("Dry run complete. No production data changed.")
                    return 0
                if view_definition(source) != view_definition(target):
                    raise RuntimeError(
                        "Production reporting view differs from development. "
                        "Align and verify the view before importing real data."
                    )
                apply(source, target, baseline)
                target.commit()
                print("Committed. Real snapshot copied; existing production rows preserved.")
                return 0
    except (psycopg.Error, RuntimeError) as error:
        # Database/connection exceptions can contain connection details. Only
        # display a class, SQLSTATE, and the controlled messages above.
        if isinstance(error, psycopg.Error):
            print(
                f"Transfer stopped: {type(error).__name__} "
                f"(SQLSTATE {error.sqlstate or 'unavailable'}). "
                "Any uncommitted production rows were rolled back.",
                file=sys.stderr,
            )
        else:
            print(f"Transfer stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())