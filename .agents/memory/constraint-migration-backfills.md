---
name: Constraint migration backfills
description: Safe ordering for adding constraints to existing PipelineInsights data.
---

When a migration adds a required relationship or consistency check over a new
nullable column, backfill valid values for existing rows before adding the
constraint. New checks must be evaluated against the current dataset, not only
future inserts.

**Why:** Existing resolved odds had player IDs but no resolution timestamp when
the resolution invariant was introduced; adding the check first would reject
otherwise valid historical rows.

**How to apply:** Add the new column, derive values from trusted existing
columns or joined reference data, then add the constraint in the same
transaction.