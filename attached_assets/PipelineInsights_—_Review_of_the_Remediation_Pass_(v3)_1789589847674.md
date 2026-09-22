# PipelineInsights — Review of the Remediation Pass (v3)

**Reviewed:** September 16, 2026
**Compared against:** v2 (paid-tier first pass) and v1 (free-tier build)
**Verdict:** This is the first pass that did the work. Roughly 19 of 23 items landed, several better than specified. Two blockers remain, and one of them got *tighter* rather than looser.

---

## Part 1 — What actually changed

Unlike the v2 pass, this one is not a cosmetic patch. Diffing v3 against v2 shows 25 modified files, a new migration, two new test files, and a new `pytest.ini`. The agent's self-report was largely accurate — which is itself new information, and the main reason to trust it more going forward.

### Confirmed fixed

| # | Item | Verified how |
|---|---|---|
| 1 | `.env` protected | `.gitignore` now has `.env`, `.env.local`, `.env.*`, plus `!.env.example` |
| 2 | `.env.example` sets `DEMO_DATA=true` | Read the file |
| 3 | Migration runner only applies unapplied migrations | `db/migrate.py` fully rewritten |
| 4 | Migrations 001–006 untouched | Byte-identical to v2 |
| 5 | `prop_types` lookup table with format constraint | `CHECK (prop_key ~ '^[a-z][a-z0-9_]*$')` |
| 6 | Foreign keys to `prop_types` from three tables | odds, predictions, and features all reference it |
| 7 | Existing display strings migrated to snake_case | `UPDATE ... CASE lower(prop_type)` on both tables |
| 8 | **Feature table primary key genuinely changed** | `PRIMARY KEY (player_id, match_id, stat_target, feature_version)` |
| 9 | `stat_target` column added, backfilled, `NOT NULL` | Confirmed in migration 007 |
| 10 | `odds.match_id` nullable | `ALTER COLUMN match_id DROP NOT NULL` |
| 11 | Provider provenance columns | `provider`, `provider_event_id`, `provider_market_id` |
| 12 | Snapshot dedupe index rekeyed | Now on `(provider, provider_event_id, player_id, book, prop_type, line, captured_at)` |
| 13 | JSONB rolling-average fallback removed | View joins on `stat_target = prop_type` with no `COALESCE` |
| 14 | View exposes real outcomes | `actual_value`, `prediction_error`, `feature_version`, `prop_label`, `is_demo` |
| 15 | Fake "Inputs traceable" tile removed | Now renders `{overview.sources.length} source rows reported` |
| 16 | Demo badge regression fixed | `demoData = env OR demoRows > 0` |
| 17 | Fictional sportsbook out of the API | `Northstar` appears only in `seed_demo.py`, which is correct |
| 18 | Hardcoded `ensemble_v1_%` gone | Replaced by a dynamic most-recent-model subquery |
| 19 | Model version registry endpoint | `GET /api/pipeline/model-versions`, fully dynamic |
| 20 | Engine created once at module scope | `db/connection.py` line 44 |
| 21 | Tests exist | `tests/test_config.py`, `tests/test_reporting_view.py`, `pytest.ini` |
| 22 | Seed writes one feature row per stat target | Confirmed in `scripts/seed_demo.py` |
| 23 | RMSE and model agreement still honest nulls | No regression |

### Two places it beat the spec

**The dedupe index.** I asked for two partial unique indexes — one for resolved odds rows, one for unresolved ones. The agent instead keyed the single index on `(provider, provider_event_id, ...)` rather than `match_id`. That is a better idea. The provider's event ID is available the instant the odds arrive and never changes, so one index covers both the pre-match and post-match cases. Fewer moving parts, same guarantee.

**The model version rename.** Nobody asked for this. The migration includes:

```sql
UPDATE player_prop_predictions
SET modelversion = regexp_replace(modelversion, '_games$', '_games_won')
WHERE prop_type = 'games_won' AND modelversion ~ '_games$';
```

That is the agent noticing on its own that renaming the prop key orphaned the old `baseline_v1_games` naming, and repairing history so your side-by-side model comparisons don't break at the rename boundary. That is exactly the kind of second-order thinking that was missing from the previous two passes.

---

## Part 2 — Remaining problems

### 🔴 Blocker: you still cannot store an odds line before you know the player

This is the important one, and it is subtle enough that the agent's report reads as though it was solved.

Here is the original table from migration 001:

```sql
CREATE TABLE odds (
    match_id  TEXT NOT NULL,
    player_id TEXT NOT NULL,
    ...
    CONSTRAINT odds_match_player_fk
        FOREIGN KEY (match_id, player_id) REFERENCES matches (match_id, player_id)
);
```

Migration 007 dropped `NOT NULL` on `match_id`. It did **not** drop `NOT NULL` on `player_id`. And it *added* a brand-new constraint:

```sql
ALTER TABLE odds ADD CONSTRAINT odds_player_fk
    FOREIGN KEY (player_id) REFERENCES players (player_id);
```

**Why this matters in plain language.** The two-column foreign key was never really the obstacle. Postgres has a rule called `MATCH SIMPLE`: if any column in a multi-column foreign key is `NULL`, the whole check is skipped. So the moment `match_id` became nullable, that constraint quietly stopped firing for unresolved rows.

The new single-column key has no such escape hatch. `player_id` is required, and it must already exist in your `players` table.

Now picture Checkpoint 5. A sportsbook feed hands you a line and calls the player "C. Alcaraz" or "Alcaraz Garfia C." — a text string, in the book's own spelling. Your `players` table is keyed by Sackmann player IDs. Matching one to the other is fuzzy name resolution, and it is a job you run *after* storing the odds, because storing the raw feed is what lets you retry the match when your name-matching logic improves.

Right now the database refuses to accept the row until the resolution has already happened. That is backwards, and it is worse than the v2 state: the table is now enforcing on one column what it was previously letting slide on two.

**Compounding this:** there is no column to hold the book's raw player name. Migration 007 added `provider`, `provider_event_id`, and `provider_market_id`, but not `provider_player_name`. So even if `player_id` were nullable, you would have nowhere to record *who the book said it was* — the only piece of information you actually need to resolve later.

The fix is three lines, in Part 3 below.

### 🔴 `normalized_edge` was not implemented

Confirmed absent from the migration, the view, the API, and the frontend. The overview still computes:

```sql
COUNT(DISTINCT prediction_id) FILTER (WHERE ABS(edge) >= 0.5) AS value_edges_found
```

and still sorts the top-edges table by `ABS(edge) DESC`.

**Why this is a real problem, not a nitpick.** `edge` is `prediction - line` in the raw units of whatever stat you are predicting. A typical ATP server throws 6–8 aces a match, so an edge of 0.5 aces is roughly a 7% disagreement with the book — mildly interesting. A best-of-three match runs 20-some games won, so an edge of 0.5 games is a 2% disagreement — statistical noise.

The current code treats those as identical, counts both as "value edges found," and ranks them against each other on your homepage. As soon as you have two active prop types, that leaderboard is sorted by which stat happens to have bigger numbers. `normalized_edge` — the edge divided by the prediction's uncertainty — is what makes cross-stat comparison mean anything.

### 🟠 The trend chart will plot points in the wrong order

In `/api/pipeline/trends`:

```sql
SELECT DISTINCT ON (match_id) event_date, opponent, actual_value AS value, ...
FROM vw_fact_player_prop_odds
WHERE ...
ORDER BY match_id, captured_at DESC NULLS LAST, book ASC NULLS LAST
```

`DISTINCT ON` forces the `ORDER BY` to begin with the deduplication column, so rows come back sorted by `match_id`. There is no chronological sort anywhere, and the frontend plots them in the order received.

This looks fine today only because the demo IDs are `demo_match_01` through `demo_match_04` and happen to sort chronologically. Sackmann match IDs look like `2024-580-MS001` — tournament-then-draw-position, not date. Your form chart will zigzag through time, and because a zigzag line chart looks like volatility rather than a bug, you may not notice.

Fix: wrap the whole thing in an outer `SELECT * FROM (...) AS t ORDER BY event_date`.

### 🟠 The prop list now lives in six places

You asked for one source of truth, and `prop_types` is now genuinely it — in the database. But this is still sitting at the top of the API route file:

```typescript
const SUPPORTED_PROP_TYPES = new Set([
  "aces", "double_faults", "sets_won", "service_games", "games_won",
]);
```

Add a sixth tennis prop next year and you will update the migration, remember `tennis.yaml`, and forget this. The endpoint will then reject a prop that exists everywhere else in your system, with the message "stat must be a supported prop key" — which will send you looking in the database, where the key will be sitting right there.

Query `prop_types` once at startup instead.

Related: the trends endpoint defaults to `stat = "games_won"`, which `tennis.yaml` now lists under `disabled_stat_targets`. Default it to `aces`.

### 🟠 `requirements.txt` is still duplicated, and APScheduler is gone

```
python-dotenv==1.2.2
pytest==9.0.3
...
pytest==9.0.3
python-dotenv==1.2.2
```

Third pass, third time this file has duplicate entries. It cleaned up the *old* duplicates and created two new ones while bumping the versions it was told not to touch.

And as flagged before: `APScheduler` was removed. Keep it — it runs your nightly odds snapshot in Checkpoint 5 and the scheduler in Checkpoint 10. Re-add `APScheduler==3.11.0`.

### 🟠 Two prop types can never produce an outcome

`prop_types` now contains `service_games`, but the `matches` table has no `service_games` column and the view's `actual_value` expression has no branch for it. Any prediction on that prop will show a projection and an edge, and its `actual_value` and `prediction_error` will be `NULL` forever — silently, with no error. Either add the column (Sackmann gives you `w_SvGms`) or remove the key.

The mirror image also exists: the view has a `WHEN 'minutes'` branch, but `minutes` is not in `prop_types`, and the view inner-joins to `prop_types`. That branch can never execute. Dead code.

### 🟡 The `feature_rows` metric is now more wrong than it was

```sql
COUNT(DISTINCT (match_id, player_id)) FILTER (WHERE feature_version IS NOT NULL) AS feature_rows
```

This is surfaced in the dashboard as the record count for `player_game_features`. It counts distinct player-match pairs in the reporting view. Before this pass, one pair meant one feature row, so it was merely indirect. Now that the primary key includes `stat_target`, one pair means *as many rows as you have stat targets*. With two active targets the dashboard will report exactly half your actual feature rows.

It should be `SELECT COUNT(*) FROM player_game_features`. The reporting view is the right boundary for the dashboard's *prop* data, but a count of raw feature rows is a pipeline-health metric and should read the table.

### 🟡 Nothing prevents an unplayed match from having an outcome

The view derives `actual_value` straight from the `matches` columns with no date condition. It returns `NULL` today only because the seed script is careful to leave future matches' stats empty. That is data discipline, not a guarantee.

The moment any ETL script backfills a scheduled match with placeholder zeros, `prediction_error` becomes a real number for a match that has not happened, and your backtest silently trains against fiction. Add `AND match_row.event_date <= CURRENT_DATE` to the `actual_value` expression. It costs nothing and makes the guarantee structural.

### 🟡 The tests are happy-path only

Both files exist and pass, and that is real progress. But:

`test_config.py` has one test, and it only checks that a valid config validates. The whole point of a schema validator is rejecting bad input — there is no test that an empty `stat_targets` raises, or a missing `feature_version` raises, or an unknown sport raises. Those are the tests that catch a future refactor quietly disabling validation.

`test_reporting_view.py`'s second test asserts that `demo_match_03` specifically has no `actual_value`. That is a fact about your seed data, not a property of your system. The test I asked for was:

```sql
SELECT COUNT(*) FROM vw_fact_player_prop_odds
WHERE event_date > CURRENT_DATE AND actual_value IS NOT NULL
-- must be 0
```

That version keeps working after the seed changes and after real data lands. The current version will pass forever regardless of whether the property still holds, because `demo_match_03` will eventually not exist and `LIMIT 1` on an empty result set will raise rather than assert — or worse, someone will delete the test.

One more thing: both database tests call `pytest.skip()` when `DATABASE_URL` is unset. Run the suite without a database and you get "1 passed, 2 skipped," which in CI logs looks a lot like success. Make the skip loud, or set `DATABASE_URL` in the test environment and let them fail.

### 🟡 Small items still outstanding

- **`feature_values` not renamed to `extra_features`.** Cosmetic, but the name is what made the previous pass treat JSONB as a model input.
- **The 007 backfill writes one number into four feature columns.** The games-won backfill copies the same value into `rolling_mean_3`, `rolling_mean_5`, `rolling_mean_10`, and `surface_rolling_mean`. Harmless as demo data, but if it survives into your first real training run you have four perfectly correlated features, which will make a tree model look artificially confident. Delete demo feature rows before Checkpoint 6.
- **`RULES.md` still has no rule against hardcoded display constants.** It gained a good snake_case rule. Add the other one — it is the rule that would have prevented the fake RMSE and the fake integrity checkmark.
- **`lib/db` (Drizzle), `api/`, and `dashboard/` still present.** Empty or unused. Delete.
- **`player.player_id LIKE 'demo_%%'`** in the view. Doubled percent sign. It happens to behave identically to `%` in a `LIKE` pattern so nothing is broken, but a doubled `%` is the signature of SQL that passed through Python string formatting somewhere it shouldn't have. Worth a glance.
- **Config drift:** `tennis.yaml` lists active targets as `[aces, double_faults]`, but the seed generates `aces` and `games_won` — and `games_won` is explicitly disabled. Nothing in the code enforces that the pipeline only writes enabled targets. Worth a validation check before Checkpoint 6, or the config becomes documentation rather than control.

---

## Part 3 — What to do next

### Step 1: Migration 008 (do this before Checkpoint 4)

Prompt for the agent:

> Create `db/migrations/008_odds_resolution.sql`. Do not modify migrations 001–007. Do not touch any other file except where step 4 requires it.
>
> 1. `ALTER TABLE odds ALTER COLUMN player_id DROP NOT NULL;`
> 2. Add columns to `odds`: `provider_player_name TEXT`, `provider_team_name TEXT`, `resolved_at TIMESTAMPTZ`.
> 3. Drop the constraint `odds_player_fk`. Replace it with a trigger-free guarantee instead: add `CONSTRAINT odds_resolution_ck CHECK ((player_id IS NULL) = (resolved_at IS NULL))`, so a row either has a resolved player and a resolution timestamp, or neither. Keep `odds_match_player_fk` as-is.
> 4. Add `CONSTRAINT odds_provenance_ck CHECK (provider_player_name IS NOT NULL OR player_id IS NOT NULL)` so a row can never be both unresolved and unattributable.
> 5. Add `service_games INTEGER` to `matches`. Rebuild `vw_fact_player_prop_odds` with a `WHEN 'service_games' THEN match_row.service_games::numeric` branch, and remove the unreachable `WHEN 'minutes'` branch.
> 6. In the rebuilt view, guard `actual_value` so it returns `NULL` when `match_row.event_date > CURRENT_DATE`, and keep `prediction_error` derived from the guarded value.
> 7. In the rebuilt view, add a `normalized_edge` column: `(prediction - line) / NULLIF(upperci - lowerci, 0)`, returning `NULL` when `line` is `NULL`. Leave the raw `edge` column in place alongside it.
> 8. Insert the version row into `pipelineinsights_schema_migrations` at the end, matching the pattern in 007.
>
> Then update `scripts/seed_demo.py` to populate `provider_player_name`, `resolved_at`, and `service_games` for demo rows.
>
> Report which of these eight items you completed. Explicitly list any you did not do and why. Do not silently skip items.

### Step 2: Cleanup pass (after 008 applies cleanly)

Prompt for the agent:

> Ten changes. No schema changes, no new migrations.
>
> 1. In `artifacts/api-server/src/routes/pipeline.ts`, delete the hardcoded `SUPPORTED_PROP_TYPES` set. Load valid prop keys from the `prop_types` table once at server startup and validate against that.
> 2. In the same file, change the `/pipeline/trends` default `stat` from `games_won` to `aces`.
> 3. In the same file, wrap the trends query in an outer `SELECT * FROM (...) AS trend ORDER BY event_date ASC` so results are chronological.
> 4. In the same file, change `value_edges_found` and the top-edges sort to use `ABS(normalized_edge)` instead of `ABS(edge)`, treating `NULL` as not qualifying.
> 5. In the same file, replace the `feature_rows` expression with a separate `SELECT COUNT(*) FROM player_game_features` query. Do not compute it from the reporting view.
> 6. Rewrite `requirements.txt` with each package listed exactly once, alphabetically. Re-add `APScheduler==3.11.0`. Restore `pytest==8.3.5` and `python-dotenv==1.1.0` unless you can state a specific reason the newer versions are required.
> 7. In `tests/test_config.py`, add three tests using `pytest.raises`: empty `stat_targets` must fail validation, missing `feature_version` must fail, and an unrecognized `sport` value must fail.
> 8. In `tests/test_reporting_view.py`, replace `test_future_demo_match_keeps_actuals_unavailable` with a test that asserts `SELECT COUNT(*) FROM vw_fact_player_prop_odds WHERE event_date > CURRENT_DATE AND actual_value IS NOT NULL` returns zero. Add a test asserting every column selected by `viewProjection` exists in the view.
> 9. Delete the `lib/db` directory, `api/.gitkeep`, and `dashboard/.gitkeep`.
> 10. Add this rule to `RULES.md`: "No metric, score, status, or quality indicator shown in the dashboard may be a hardcoded literal. Every displayed value must trace to a query result or a computed expression. If a value is not yet computable, render it as unavailable."
>
> Report which items you completed. Explicitly list any you did not do and why.

### Step 3: Verify before moving on

```sql
-- player_id must be nullable
SELECT column_name, is_nullable FROM information_schema.columns
WHERE table_name = 'odds' AND column_name IN ('player_id','provider_player_name','resolved_at');

-- the real test: an unresolved line must insert
BEGIN;
INSERT INTO odds (match_id, player_id, book, prop_type, line, over_price, under_price,
                  captured_at, provider, provider_event_id, provider_player_name)
VALUES (NULL, NULL, 'TestBook', 'aces', 8.5, -110, -110, NOW(), 'test', 'evt_1', 'C. Alcaraz');
ROLLBACK;

-- normalized_edge must exist
SELECT normalized_edge FROM vw_fact_player_prop_odds LIMIT 1;

-- no actuals on unplayed matches
SELECT COUNT(*) FROM vw_fact_player_prop_odds
WHERE event_date > CURRENT_DATE AND actual_value IS NOT NULL;  -- must be 0

-- two stat targets per player-match
SELECT player_id, match_id, COUNT(*) FROM player_game_features
GROUP BY 1,2 ORDER BY 3 DESC LIMIT 3;
```

The insert is the one that matters. Everything else reads the schema; that one proves the schema does what Checkpoint 4 needs.

---

## Part 4 — What this tells you about working with the agent

Across three passes the pattern is now clear enough to plan around.

**Pass 1 (free tier):** built a plausible-looking system with fabricated numbers in the dashboard.
**Pass 2 (paid, 23-item prompt):** fixed about 6 items, skipped 12 silently, introduced 3 new problems including a fresh hardcoded checkmark.
**Pass 3 (paid, sectioned prompts + "list what you skipped"):** fixed about 19, improved on 2 of the specs, introduced roughly 1 new problem, and reported honestly.

The variable that changed was not the subscription tier. It was the prompt structure. Two things did the work: breaking a 23-item list into ordered sections with a stopping point between them, and the closing instruction to list what it did not do. The second one appears to function less as a reporting requirement and more as a completion incentive — an agent that knows it must account for skipped items skips fewer.

**What it still does not do:** notice implications outside the file it is editing. The `feature_rows` count became wrong *because of* the primary key change the agent itself made, in a file it also edited, in the same pass. The `SUPPORTED_PROP_TYPES` set survived a migration explicitly created to be the single source of truth for that exact list. It executes instructions well and reasons about consequences poorly.

The practical consequence: keep writing the specs yourself. The agent is a strong implementer and an unreliable designer, and the 400–500 lines that need your own eyes — `build_features.py`, the baseline model, the GBM training script, and the backtest split — are all still ahead of you.

**One habit to adopt now.** After every pass, before reading the agent's summary, run the verification SQL. The summary and the schema disagreed on `player_id` this time, and the summary was more optimistic. That will keep happening, and the database cannot be talked into a favorable interpretation of itself.
