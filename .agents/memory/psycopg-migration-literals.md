---
name: Psycopg migration literals
description: A driver-specific constraint for raw SQL migration execution.
---

Raw SQL migrations executed through SQLAlchemy's psycopg driver must escape
literal percent signs as `%%` when using `exec_driver_sql`; psycopg parses `%`
as a parameter placeholder even when the statement has no bound parameters.

**Why:** A view predicate containing a normal SQL `LIKE '%...'` pattern caused
the migration to fail before PostgreSQL received the statement.

**How to apply:** Check migration SQL for percent operators and `LIKE` patterns
before applying a new migration through the Python runner.