---
name: Production data provisioning
description: Why a healthy published dashboard can differ from Preview after republishing.
---

Replit-managed production and development databases hold separate rows after the first publish. Later successful publishes update the app and schema but do not automatically copy newly generated development data into the existing production database.

**Why:** A republish successfully restored the live API, but the production database still lacked the real model snapshot that had been generated in development. Repeated publishing cannot fix a data-placement mismatch, and replacing production wholesale could discard existing records.

**How to apply:** Compare read-only real-data presence in both environments before debugging the UI. To show development-generated snapshots live, plan an explicit, selective import that preserves existing production rows and has a clear rollback path; do not reset or overwrite the production database merely to synchronize it.