---
name: Publish schema compatibility
description: Safe development-to-production schema changes for the legacy PipelineInsights production snapshot.
---

When production already contains legacy rows, shape the development schema so Publish can apply additive nullable columns and non-destructive indexes. Match existing production index names where possible, and avoid primary-key changes that force a new column to be NOT NULL before legacy rows can be backfilled.

**Why:** Replit Publish diffs the live development and production schemas. It does not replay the project's historical SQL migration sequence, so a valid development migration can still produce a destructive publish diff against older production rows.

**How to apply:** Before republishing, inspect the publish diff and require no table truncations, no structural data-loss flag, and no warnings for legacy rows. Never choose a publish option that deletes or truncates existing production data to satisfy a new constraint.

Legacy odds and prediction rows may use human-readable prop labels and may have `player_id` without a later `resolved_at` value. New reference foreign keys and resolution checks must not reject those rows during Publish.

**Why:** Publish adds schema constraints to existing production data without replaying the application's historical normalization steps.

**How to apply:** Validate every generated foreign key and check constraint against the read-only production snapshot, not only the diff warning list.

Publish schema diffs do not carry changed PostgreSQL view definitions. Production can therefore have current base tables but an older reporting view after a successful publish.

**Why:** A successful schema publish left the production reporting view without columns required by the newly deployed API.

**How to apply:** Keep deployed API reads compatible with shared base-table schemas, or verify view parity separately before depending on newly added view columns.