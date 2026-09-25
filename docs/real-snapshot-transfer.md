# Move the real Preview snapshot to the existing production database

Publishing deploys code and schema changes, **not** new rows from the development database. The live dashboard's Real mode will remain empty until real rows are explicitly imported. This procedure keeps existing production rows and does not copy demo player, match, feature, or prediction rows.

**Current status: prepared, not ready to apply.** The production reporting view is older than Preview's. The script deliberately refuses `--apply` while their definitions differ, because an import of more than a million predictions could leave the live dashboard too slow or inconsistent. A safe production-view alignment and representative reporting-query verification are required first. A normal republish has not synchronized this view.

## Before running

- `scripts/transfer_real_snapshot.py` is a **one-time** data-copy tool, not a publish hook. It streams rows from development directly to production; it does not create a dump in the repository, delete rows, update rows, or copy the reporting view. Player-linked tables exclude `demo_` players. Shared prop-type lookups are copied; model metrics are copied only for versions with real predictions.
- The source is the workspace's managed development `DATABASE_URL`. The destination must be the **existing** production database connection shown under Database → Production → Settings. Do not replace the managed `DATABASE_URL`, paste the connection string into chat, or commit it to a file.
- Temporarily add the destination as a **development-only Secret** named `PIPELINEINSIGHTS_PRODUCTION_DATABASE_URL`. Never make it a shared or production secret. Remove it from Secrets after the transfer. The agent cannot read or set the credential.
- Confirm that production has a usable backup or point-in-time recovery option before importing. An error before commit rolls back inserted table rows, but PostgreSQL sequence values can remain advanced (harmless gaps in generated IDs). A completed import cannot be reversed by rerunning it. Replit's [data recovery guidance](https://docs.replit.com/features/data-and-storage/data-recovery) describes recovery availability by plan.
- Run the transfer from the **workspace Shell**, not from the published app. Keep other writers to these tables stopped during the import. The script locks target tables while copying; API reads remain available.

## Review and run

```sh
python scripts/transfer_real_snapshot.py --source-only
python scripts/transfer_real_snapshot.py
```

The second command is read-only. Confirm that its source is the development snapshot and that production has no rows in the transfer scope. It refuses to proceed if the databases resolve to the same endpoint, their table columns differ, development has no real predictions, or production already has real rows to merge.

Only **after the production reporting view has been aligned and checked**, reviewing the dry-run counts, and confirming a recovery plan, run:

```sh
python scripts/transfer_real_snapshot.py --apply --backup-confirmed
```

The script copies lookup rows, real players and matches, features, odds, predictions, injuries, and matching model backtest/importance rows in dependency order. It streams through PostgreSQL `COPY`, verifies table counts, compares the two headline reporting totals with Preview, and commits all table inserts together. A constraint violation or validation failure aborts and rolls back the inserted rows. **Do not** use a whole-database restore, `--clean`, truncation, or database recreation to solve the Preview/Production difference.

Even after view alignment, compare representative Real-mode Overview, Predictions, Trends, and Backtest queries at expected volume before treating the live experience as verified. The script checks headline counts and will roll back the copied rows if those counts time out or differ, but it cannot prove every report is fast. Remove the temporary Secret when finished. Refresh the published dashboard in Real mode and check Overview, Predictions, Trends, and Backtest. The current development snapshot has no real provider odds; this transfer does not create market prices or value edges that are not in the source.