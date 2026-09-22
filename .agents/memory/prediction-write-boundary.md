---
name: Prediction write boundary
description: Database upserts should receive standard Python scalar and datetime values rather than pandas objects.
---

Normalize pandas/NumPy scalars, PostgreSQL `Decimal` numerics, and `pd.Timestamp` objects before batch writes or metric arithmetic through SQLAlchemy.

**Why:** PostgreSQL returns `NUMERIC` values as `Decimal`, while model arithmetic uses floats; lightweight SQLite verification also does not reliably bind pandas timestamps. Normalization keeps persistence and scoring portable and testable.

**How to apply:** Convert database numeric columns with `pd.to_numeric`, nulls to `None`, timestamps to Python datetimes, and NumPy scalars to native values immediately before arithmetic or SQL execution.