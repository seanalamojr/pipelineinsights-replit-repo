"""SQLAlchemy connection helpers for PipelineInsights.

This module is intentionally the only connection setup used by Python code.
It loads credentials from the environment and never logs the connection string.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text


def _database_url() -> str:
    """Return a psycopg-compatible URL without exposing its value."""

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to Replit Secrets or a local .env file."
        )

    # Replit may provide either postgres:// or postgresql://. Explicitly selecting
    # psycopg keeps the driver consistent with requirements.txt.
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix(
            "postgresql://"
        )
    return database_url


def create_db_engine() -> Engine:
    """Create an engine with lightweight health checking enabled."""

    return create_engine(_database_url(), pool_pre_ping=True, future=True)


_engine: Engine | None = None


def get_engine() -> Engine:
    """Create and cache the shared engine only when database access is needed."""

    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


@contextmanager
def db_connection() -> Iterator[object]:
    """Yield a checked-out connection and close it when the caller is done."""

    with get_engine().connect() as connection:
        yield connection


def verify_connection() -> int:
    """Run the checkpoint 1 health query and return its scalar result."""

    with db_connection() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar_one()
        if value != 1:
            raise RuntimeError(f"Unexpected SELECT 1 result: {value!r}")
        return int(value)


if __name__ == "__main__":
    try:
        print(f"Postgres connection OK: SELECT 1 returned {verify_connection()}")
    except Exception as error:
        # Keep the message actionable without ever printing DATABASE_URL.
        raise SystemExit(f"Postgres connection failed: {error}") from error