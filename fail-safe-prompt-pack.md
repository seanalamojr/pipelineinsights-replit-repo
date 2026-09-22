# PipelineInsights fail-safe prompt pack

## How to use this file

This is an execution guide, not an approval to skip the active Checkpoint 13 work. Paste the
**Session preamble** once at the beginning of a working session. Then paste exactly one numbered
prompt at a time. Do not paste the next prompt until the current prompt's verification gate is
accepted with fresh evidence.

If a prerequisite is missing, the executor must say **STOP** and report the missing prerequisite.
It must not create a workaround, silently use demo data, invent historical odds, repair invalid
intervals without counting the repair, or claim that a gate passed.

The sequence is deliberately:

1. Tennis evidence and operational verification.
2. MLB portability.
3. Architecture generalization.
4. NFL implementation.
5. Dashboard, scheduled operation, monitoring, shadow operation, and go-live review.

The current task is the prompt pack only. Do not run these prompts while creating this file.

---

## Reconciled source facts

These are the current facts to carry forward when older cards, build notes, or Trello text conflict:

- Tennis is the reference implementation. The active feature pipeline is ATP men only
  (`player.tour = 'ATP'`).
- The active tennis targets are `aces`, `double_faults`, and `service_games`.
- The captured odds archive is currently entirely WTA. It is not ATP market evidence.
- Prop-odds capture began on 2026-09-17. Historical prop odds before capture are unavailable and
  must not be invented or simulated.
- Accuracy, calibration, and prediction error are not profitability. A market-edge claim requires
  a real pre-match price, a known result, and an informative sample.
- Models read only `player_game_features`, never raw sport tables.
- Backtests use chronological train/test folds only. Never use random splits.
- Predictions are append-only by `modelversion`. Never overwrite an existing version; changed
  features, hyperparameters, model type, or weights require a new version.
- Production uses configured static ensemble weights. Evaluation may fit weights only from strictly
  earlier folds. Do not change production weights during evidence work.
- The dashboard and API read only `vw_fact_player_prop_odds`, not base tables. Frontend code must
  not query base tables directly.
- The reporting view intentionally keeps predictions visible when odds are absent. A LEFT JOIN
  means no odds is an expected state, not permission to hide or replace predictions.
- Demo data uses the existing `demo_` convention. It must remain available for explicit UI work,
  but it must be visibly separated from real data and never be the silent default.
- `scripts/run_pipeline.py` is the approved real-only orchestration entry point. It requires
  explicit historical seasons and/or attached current-season files, records pre/post real and
  demo counts, fails if the real pipeline changes demo rows, and refuses to overwrite an
  existing real model version.
- The last reported backtest is historical context, not a current gate: GBM was reported as
  beating the rolling baseline by roughly 20–28% depending on target, while the ensemble lost to
  GBM on all three targets. Re-run and report current evidence before drawing conclusions.
- The Bayesian/hierarchical layer is optional. It is not to be built or retained by default; the
  tennis exit decision must explicitly say keep, defer, or drop and why.

### Reconciliation decisions

- Older material says “market comparison” or “ROI” as a future phase deliverable. The current
  evidence boundary wins: report no market result when no qualifying price sample exists.
- Older material expects the ensemble to beat the baseline. That is a hypothesis to test, not a
  guaranteed outcome. Unexpectedly strong results require leakage investigation.
- The surname card says the current archive should match at 0% because it is WTA while the
  pipeline is ATP. Preserve that as a regression observation, not as a reason to loosen matching.
- The source cards call some cleanup “complete,” while the active roadmap still requires fresh
  output. A named gate passes only from the current run, test output, or query output.

---

## Session preamble — paste once

Copy everything inside this block as one message:

```text
You are working on PipelineInsights. Work on exactly one bounded objective from the prompt I
send next. Do not proceed to a later prompt unless its named predecessor gate was accepted with
fresh evidence.

Sequence: finish tennis evidence and operational verification first; then MLB portability; then
architecture generalization; then NFL; then live operations. Do not start MLB, generalization,
NFL, a Bayesian layer, production-weight changes, or fabricated odds history early.

Non-negotiable boundaries:
- Models read only player_game_features, never raw sport tables.
- All evaluation uses chronological train/test folds. Never use a random split.
- Prediction history is append-only by modelversion. Never overwrite an existing modelversion;
  bump the version for changed features, model type, hyperparameters, or weights.
- Production uses configured static ensemble weights. Evaluation may fit weights only from
  strictly earlier folds and must show the fold boundary.
- The dashboard and API read only vw_fact_player_prop_odds. Do not query base tables from the
  frontend. Predictions must remain visible when odds are absent.
- Real and demo data must be separately queryable and visibly labeled. Never silently fall back
  to demo rows.
- Do not silently repair crossed/invalid intervals, silently resolve ambiguous names, or use
  fuzzy/edit-distance name matching. Count and report any explicit repair or unresolved row.
- Accuracy and calibration are separate from market edge and profitability. Never call accuracy a
  profit result. A market result requires a real pre-match price, a realized result, and an
  informative sample.

Known data limitations:
- The active feature pipeline is ATP men only and targets aces, double_faults, and
  service_games.
- The captured odds archive is currently entirely WTA.
- Historical prop odds before the 2026-09-17 capture start are unavailable. Do not invent,
  purchase, or simulate historical odds.
- The active end-to-end entry point must be `scripts/run_pipeline.py`; do not claim a real run
  until that non-demo path is executed with explicit source inputs.

For every response, use these headings in this order:
1. Scope
2. Files and database objects inspected
3. Preflight and prerequisites
4. Changes made (or “none”)
5. Evidence
6. Omissions and skipped work
7. Risks and unresolved findings
8. Verification gate: PASS or STOP

In Evidence, include actual command output or query output, pre/post row counts, timestamps,
model versions, relevant test output, and the exact scope of every query. Include the data source,
sport, target, fold/date range, and whether rows are real or demo. Do not summarize output when
the prompt asks to paste it.

If any prerequisite is missing, the test is skipped, the output is fabricated, or a boundary is
violated, say STOP. Do not use a workaround. A gate can pass only when every requirement for that
gate has fresh, reproducible evidence.
```

---

## Standard result template — paste after every prompt

Use this small template when asking the executor to report its result:

```text
Scope:
Files/database objects inspected:
Preflight:
Changes:
Pre-run counts:
Post-run counts:
Timestamps and date ranges:
Model versions:
Commands and actual output:
Queries and actual output:
Test results:
Real/demo status:
Skipped work and exact reason:
Risks/findings:
Verification gate: PASS or STOP
```

## Gate checklist

Before accepting any gate, verify all of the following:

- [ ] The prompt's predecessor gate was accepted.
- [ ] The objective stayed within scope.
- [ ] Preflight prerequisites were checked.
- [ ] Pre/post counts are present, or the executor explicitly says why a count does not apply.
- [ ] Timestamps, date ranges, sport, target, and real/demo status are identified.
- [ ] Model versions are listed and no existing version was overwritten.
- [ ] Actual command, test, or query output is included.
- [ ] Skipped work is named exactly, with reasons.
- [ ] No random split, raw-table model read, frontend base-table read, fuzzy match, silent
  interval repair, fabricated odds, or unsupported market-edge claim appears.
- [ ] The result ends with exactly one clear **PASS** or **STOP** decision.

---

# Phase 1 — Tennis evidence and exit

## T0 — Audit the repository, data state, and active roadmap

**Use first. No predecessor gate.**

```text
Audit the current PipelineInsights repository and database without changing code, schema, data,
model versions, or dashboard behavior.

Bound the audit to the active Checkpoint 13 roadmap and these areas: configuration, migrations,
real versus demo data, ATP feature prerequisites, model entry points and writers, ensemble
evaluation boundaries, backtest persistence, reporting-view/API/dashboard reads, odds identity,
and tests for the reporting view and OOF guard.

Inspect the relevant files and database objects, including config/tennis.yaml,
scripts/run_pipeline.py, evaluation/backtest.py, evaluation/checkpoint12.py, models/baseline.py,
models/ensemble.py, the reporting-view migration, the API route, and the two dashboard pages.
Search for raw-table model reads, random splits, model-version overwrites, demo fallbacks, fuzzy
matching, silent interval repair, and claims that equate accuracy with profitability.

Verify that `scripts/run_pipeline.py` remains the approved non-demo execution path. If it is
missing, disabled, or bypassed, do not establish a workaround: record that fact and STOP this
gate.

Report the current counts for matches, players, player_game_features, odds, and
player_prop_predictions, split into real rows and demo rows where the schema permits. Confirm
the ATP feature rows for aces, double_faults, and service_games and their feature version. Record
the current model versions and min/max prediction timestamps. Record the odds archive tour,
markets, providers, and capture date range.

Also produce a dependency table showing which later prompt is blocked by each missing prerequisite.
Do not implement any fix in this prompt.

In your response include pre/post counts (post counts must say “unchanged” because this is
read-only), timestamps, model versions, actual commands and query output, exact skipped items,
and the final PASS or STOP decision.
```

**Verification gate T0 → T1:** PASS only if the audit is complete and an approved real, non-demo
execution path plus ATP feature prerequisites are proven. If the path is still a placeholder,
the ATP rows are absent, or any count/query was skipped, STOP.

## T1 — Execute the approved tennis pipeline on real data

**Use only after T0 passes.**

```text
Run the existing approved tennis pipeline on real ATP data. This is an execution and evidence
task, not an invitation to add features, refactor model logic, tune hyperparameters, or seed demo
rows.

Before running anything, report counts for matches, players, player_game_features, odds, and
player_prop_predictions, split into real and demo rows. Confirm that real ATP
player_game_features exist for aces, double_faults, and service_games under the configured
feature_version.

Run baseline, GBM, and ensemble for all three active targets in non-dry-run mode through the
approved path. For each run report the exact command, start/end timestamp, source data range,
target, real-row count read, real-row count written, modelversion, predictiontimestamp range, and
any shuffled-target or leakage check output. Report the configured production weights used by the
ensemble; do not change them.

After the run, query player_prop_predictions grouped by modelversion and target. Report final
counts, min/max prediction timestamps, and whether any pre-existing modelversion changed its row
count or contents. Query representative rows through vw_fact_player_prop_odds and confirm real
player names, prediction, lowerci, and upperci are populated while odds fields may be NULL.

If any prerequisite is absent, if the approved path cannot run, or if a command would overwrite a
modelversion, stop instead of creating a workaround. Do not run seed_demo.py as a substitute.

In your response include pre/post counts, timestamps, model versions, actual command/query/test
output, exact skipped work and omissions, and a final PASS or STOP decision.
```

**Verification gate T1 → T2:** PASS only if all three real tennis targets ran for baseline, GBM,
and ensemble, persisted rows under non-overwriting versions, and produced queryable real
predictions. A demo-only run, dry run, placeholder output, missing target, or absent output is
STOP.

## T2 — Prove real/demo separation and the honest empty state

**Use only after T1 passes.**

```text
Verify the dashboard's real/demo boundary without deleting demo data and without changing model
logic.

First report the current dashboard/API file, endpoint, query, and relevant UI code. Show whether
demo filtering exists and whether the mode is visible to the user.

Then verify or implement the smallest migration/API/UI change needed for these rules: the reporting
view exposes a derived is_demo value based on the established demo convention; default dashboard
queries exclude demo rows; demo rows remain reachable only through an explicit mode or parameter;
the UI labels demo mode visibly; and zero real predictions produces a clear empty state rather than
a silent demo fallback.

Do not edit an existing migration. If a migration is needed, use the next numbered migration and
record its applied version. Do not alter the reporting view's LEFT JOIN to odds and do not delete
the demo seeder or demo rows.

Prove the result with the exact default-mode and explicit-demo-mode query/endpoint output. Report
real count, demo count, overlap count, and the empty-real-data behavior. If real rows are absent,
that must be visible as an empty real state even if demo rows exist.

In your response include pre/post counts, timestamps, migration and model versions, actual test or
query output, exact skipped items, and PASS or STOP.
```

**Verification gate T2 → T3:** PASS only if default mode excludes demo rows, explicit demo mode is
visible and non-overlapping, real predictions remain available, and the empty real state is
honest. Any silent fallback, deleted demo data, or missing output is STOP.

## T3 — Verify the reporting view under no-odds and fan-out conditions

**Use only after T2 passes.**

```text
Write or run focused database-backed regression tests for vw_fact_player_prop_odds. Do not
redesign the view, change its join types, or query base tables from dashboard code.

Cover exactly these cases:
1. A real-shaped prediction with no matching odds appears with line, over_price, under_price,
   edge, side, and normalized_edge all NULL.
2. One prediction plus three books for the same match/player/prop returns exactly three view rows,
   with the same prediction on each row. Explain in the test why this fan-out is intentional and
   why raw-view aggregates must deduplicate prediction identity.
3. A prediction with a missing match cannot be inserted because of the foreign-key boundary, or
   the test reports the constraint failure as a finding.
4. Invalid intervals (lowerci above prediction and negative lowerci) are rejected by the
   prediction_interval_ordered CHECK.
5. Edge equals prediction minus line, including the exact-line boundary, and the expected side is
   asserted.
6. The full suite is run with DATABASE_URL unset and with a database available; report pass,
   fail, and skip counts for both runs.

Use isolated test data and clean it up only within the test's scope. Preserve real/demo labels.
Paste the actual assertions and actual output. If an expected invariant fails, report it rather
than quietly repairing the view or constraint.

In your response include pre/post counts, timestamps, model versions where relevant, actual
commands/query/test output, all skipped work and cases with reasons, and PASS or STOP.
```

**Verification gate T3 → T4:** PASS only if all six cases have actual evidence, no-odds predictions
remain visible, the intended three-book fan-out is documented, and both database/no-database test
runs report their skip counts. A silent skip or view rewrite is STOP.

## T4 — Persist chronological out-of-sample backtest predictions

**Use only after T1 passes; T3 should also be accepted before dashboard use.**

```text
Persist per-row tennis backtest predictions as queryable, explicitly labeled out-of-sample
artifacts. This is a persistence and provenance task, not a model redesign.

First inspect the current backtest producer and report the function, dataframe columns, and whether
each row retains match_id, player_id, prop_type, prediction, lowerci, upperci, fold number, and
the fold train-window end date. Report the current persisted state before writing anything.

Choose a collision-proof non-live modelversion convention, such as
gbm_v1_aces_backtest, and record the exact convention in the report. Use the existing
upsert_predictions writer; adapt the frame rather than creating a second writer. Do not reuse an
existing live or backtest version.

Persist rows produced by chronological folds only. Record fold provenance and train-window end
date. If quantile intervals cross or violate the database CHECK, count every affected row and
report the explicit clamping/order operation and resulting bounds; never silently repair or drop
them. Do not change features or hyperparameters in this prompt.

After persistence, query counts by modelversion and target, earliest/latest event_date, fold
coverage, and min/max predictiontimestamp. Show three real persisted sample rows with fold
train-window end date and event_date, proving event_date is later. Confirm no existing
modelversion was overwritten.

In your response include pre/post counts, timestamps, model versions, actual commands/query/test
output, interval-repair counts, exact skipped work and omissions, and PASS or STOP.
```

**Verification gate T4 → T5:** PASS only if persisted rows are labeled with non-live versions,
fold provenance is queryable, each sample proves train end < event date, and interval repairs or
omissions are counted. Random splits, missing provenance, or an overwrite is STOP.

## T5 — Build and verify the accuracy surface

**Use only after T4 passes.**

```text
Expose real tennis accuracy evidence through the existing reporting-view/API contract. Do not
query base tables from frontend code and do not report profitability.

Confirm where actual aces, double_faults, and service_games live and how the reporting view exposes
actual_value and prediction_error. If the view needs a change, add the next numbered migration;
leave upcoming rows visible with NULL actuals and do not edit an old migration.

Compute or expose, per target and per modelversion, mean absolute error, observed interval
coverage, the interval target, and the deduplicated scored-row count behind each metric. Use
prediction identity/fold provenance so odds fan-out does not multiply a prediction. Keep baseline,
GBM, and ensemble metrics separate and directly comparable on identical real scored rows.

The UI/API must show row count next to every metric, show the interval target next to observed
coverage, exclude demo rows by default, and visibly label demo mode if used. Add a plain-language
note that accuracy and interval coverage measure closeness to outcomes, not sportsbook
profitability or market edge.

Report current values by target/modelversion and distinguish unscorable startup folds or NULL
actuals from zero error. Do not fabricate metrics for unscored rows.

In your response include pre/post counts, timestamps, model versions, actual query/test output,
the deduplication key, exact skipped work, and PASS or STOP.
```

**Verification gate T5 → T6:** PASS only if the accuracy surface is real-data-only by default,
deduplicated, model-version-specific, row-counted, interval-targeted, and explicitly separated
from profitability. Any frontend base-table read or fabricated/unscored metric is STOP.

## T6 — Verify exact compound-surname resolution without fuzzy matching

**Independent of T2–T5, but must pass before tennis odds readiness is decided.**

```text
Verify the exact odds-name resolver behavior and close the compound-surname evidence gap. Do not
use fuzzy or edit-distance matching and do not resolve ambiguous aliases by guessing.

Before changing anything, add/run a failing test that requires Aaron Gil Garcia to match the exact
form “Gil Garcia A.”. Paste the failure and the stated reason. Print the current alias lists for
Aaron Gil Garcia, Botic Van De Zandschulp, Pierre-Hugues Herbert, Thiago Agustin Tirante, and a
single-token name.

If the test confirms the known gap, generate candidates for each plausible trailing-token surname
span while preserving existing aliases. Handle hyphenated given names, lowercase particles
including van/de/van de/del/bin, and names already supplied as “Surname F.”. Keep ambiguous
aliases unresolved.

Run the fixed test, print before/after alias lists, scan the full player table for aliases mapping
to more than one player_id, and report every collision plus the resolver's behavior for it.
Re-run matching on the captured archive and report match rate before and after. State explicitly
that the archive is WTA while the feature pipeline is ATP, so 0% is expected here and is not
evidence of an ATP resolver failure.

In your response include pre/post counts, timestamps, model versions or “unchanged,” actual
failure, passing-test, and collision-query output, exact skipped work and omissions, and the final
decision: PASS or STOP.
```

**Verification gate T6:** PASS only if the pre-fix failure, post-fix success, collision report, and
before/after archive rates are actual evidence; ambiguous matches remain unresolved and matching
stays exact. Any fuzzy fallback or unreported collision is STOP.

## T7 — Mutation-test the OOF weight guard and fold boundary

**Independent cleanup verification; do not change production weights.**

```text
Verify that the OOF weight guard test can detect lookahead and that fold accumulation is
chronological. Do not change evaluation/backtest.py's correct production accumulation order and do
not leave mutation code in the tree.

Report the full current body of test_oof_weights_ignore_the_fold_being_scored. Show that the test
changes when earlier-fold outcomes change and that weights from earlier folds differ from weights
computed after appending the scored fold. State whether the scored fold's own data enters the
asserted fit.

Temporarily mutate fit_oof_weights to return constant uniform weights, run only the guard test,
and paste the output. The test must fail under this mutation. Restore the original implementation
immediately, run the test again, and report the full-suite pass/fail/skip counts. Apply the same
mutation check to every cleanup test that claims to guard lookahead or leakage.

Also verify run_ensemble_backtest's accumulation order with a seam or a focused test: no fold's
fitted weights may be derived from rows in that fold's own test set. Report the fold number,
training rows, scoring rows, and weight-fit input boundary.

Confirm no mutation code remains anywhere in the working tree and do not change production static
ensemble weights.

In your response include pre/post counts where applicable, timestamps, model versions, actual
mutation and restore output, fold-boundary output, skipped tests and reasons, and PASS or STOP.
```

**Verification gate T7:** PASS only if the guard fails under the deliberate mutation, passes after
restoration, the fold-order test proves no lookahead, and the tree is clean. If the guard passes
under mutation, STOP and report it as vacuous.

## T8 — Review tennis edge cases and failure modes

**Use only after T4 and T5 pass; T6 and T7 should be accepted.**

```text
Stress-test the current tennis evidence without inventing new modeling work. Select real rows for
retirements or mid-match stops, surface transitions, debut or sparse-history players, missing or
NULL actuals, crossed-interval candidates, unresolved names, and predictions with no odds.

For each category, report the selection query and pre/post counts, event dates, target, modelversion,
prediction, actual value, interval, error, fold provenance, and whether the row is real or demo.
Compare errors and interval behavior by category without pooling away the category labels. State
which cases are unscorable and why. Confirm missing odds stay missing rather than being silently
filled, and invalid intervals are counted rather than silently repaired.

Write a concise failure-mode checklist for future MLB and NFL work. Do not tune features, change
model logic, add a Bayesian layer, fabricate prices, or call an accuracy result a market edge.

In your response include pre/post counts, timestamps, model versions, exact query/test output,
skipped categories and reasons, risks, and PASS or STOP.
```

**Verification gate T8 → T9:** PASS only if each requested edge category has an explicit count or
an evidence-backed “not present,” unscorable cases are labeled, and no silent repair or invented
market evidence appears.

## T9 — Make the tennis exit decision

**This is the final tennis gate. No MLB prompt may be used until it passes.**

```text
Prepare a written tennis exit review from fresh evidence produced by gates T0 through T8. Do not
run new modeling, start MLB, generalize the architecture, build NFL support, or enter live
operations in this prompt.

Decide each item separately:
1. Real-data execution: which ATP targets and model versions ran, with row counts and timestamps.
2. Real/demo separation: whether default dashboard/API reads are real-only and demo mode is visible.
3. Reporting-view behavior: no-odds visibility, odds fan-out, interval constraints, and edge
   arithmetic.
4. Out-of-sample provenance: persisted rows, fold IDs, train-window end dates, and date-order
   proof.
5. Accuracy surface: MAE, interval coverage versus target, scored row counts, startup/unscorable
   folds, and calibration limitations by target/modelversion.
6. Surname resolution: exact matching, collision behavior, and the WTA archive/ATP pipeline
   mismatch.
7. OOF weights: mutation-test result, fold boundary, and separation of evaluation-fitted weights
   from production static weights.
8. Edge cases: observed failure modes, NULL actuals/odds, interval repairs, and unresolved rows.
9. Market readiness: explicitly state that the WTA archive is not ATP evidence and historical
   prop odds are unavailable; do not report profitability or market edge unless an informative
   ATP price sample exists.
10. Documentation and operating risks: omissions, remaining tests, and whether the active entry
    point is production-ready.
11. Bayesian layer: choose exactly one of KEEP, DEFER, or DROP, with evidence and scope. A keep
    decision must not silently authorize implementation or production use.

For every decision cite the gate and actual output that supports it. Mark the overall tennis exit
PASS only if the evidence is complete enough to open MLB work. Otherwise mark STOP and name the
blocking gates. Explicitly write: “MLB work is prohibited until this exit gate is accepted.”

Include pre/post counts, timestamps, model versions, actual command/query/test output, exact
skipped work and omissions, risks, and the final PASS or STOP.
```

**Verification gate T9 → MLB:** PASS only with a written decision for every item, accepted
evidence for T0–T8, and no unsupported market/profitability claim. If any predecessor is missing,
if ATP/MLB sequencing is bypassed, or if the Bayesian decision is vague, STOP.

---

# Phase 2 — MLB portability

## M1 — Map MLB sources and the sport-neutral schema

**Use only after the tennis exit gate T9 passes.**

```text
Design and verify the MLB source/schema mapping before loading or modeling MLB data. Do not write
model code, change production tennis versions, or start NFL work.

Choose and document the real MLB source, licensing/availability limits, seasons, update cadence,
stable player/team/game identifiers, and the exact fields needed for games, teams, rosters,
player game logs, injuries, odds if available, and realized outcomes. Map each source field to a
database field and identify missing, estimated, or provider-specific values.

Design the generic team/game shape needed for MLB and later NFL: home/away, game date/time,
season, rest days, travel/venue context, team IDs, player-team membership, and game identity.
Explain how the design avoids tennis-only assumptions and how it will preserve the
player_game_features model boundary.

Do not load partial or demo MLB rows as proof of readiness. If a source is unavailable, report STOP
with the missing field and do not invent it. Report schema pre/post counts (unchanged if this is
design-only), source timestamps/date ranges, actual DDL/query output if applied, model versions
(unchanged), exact skipped work and omissions, and PASS or STOP.
```

**Verification gate M1 → M2:** PASS only if a real source and complete mapping are documented,
stable IDs and team/game grain are proven, and no missing value is disguised as real data.

## M2 — Build MLB ETL and team-context features

**Use only after M1 passes.**

```text
Implement and verify the MLB-specific ETL and feature layer using the approved source and schema
map. Keep sport-specific work in sources, ETL, raw tables, and feature engineering.

Load a bounded real MLB slice first and report source rows, rejected rows, inserted/updated rows,
duplicate identifiers, coverage by season/team/player, and ingestion timestamps. Add only the
documented team-context and availability features: opponent strength, park/venue factor,
pitcher-batter or equivalent matchup context, rest/travel context, and an injury/availability
signal with provenance.

Write all model inputs to player_game_features. Prove the feature cutoff for every row: each
feature must use information available before the event. Do not let models read MLB raw tables.
Do not silently fill missing injuries, intervals, or team assignments; report NULLs, skips, and
repairs explicitly.

Run feature invariant tests and show representative real rows with player, team, opponent, game
date, feature timestamp/cutoff, target, and feature_version. Do not modify tennis feature rows or
model versions.

Include pre/post counts, timestamps, model versions (unchanged), actual load/query/test output,
exact skipped fields/rows and reasons, risks, and PASS or STOP.
```

**Verification gate M2 → M3:** PASS only if real MLB features populate the shared feature table,
team context and availability provenance are visible, temporal cutoffs are proven, and raw-table
model reads are absent.

## M3 — Reuse the model path on MLB

**Use only after M2 passes.**

```text
Run baseline, GBM, and ensemble through the existing model interfaces against the MLB
player_game_features slice. Change feature configuration and target mapping only; do not embed
MLB-specific if/else logic in shared model files.

Before running, report the MLB feature counts by target and feature_version and confirm the chosen
feature list is configuration-driven. Run a controlled non-dry-run sample, then the approved
bounded MLB execution. Use new MLB-specific modelversions; never reuse or overwrite tennis
versions or existing MLB versions.

Report each model's exact inputs, source date range, row counts read/written, prediction timestamps,
quantile interval validity, target, sport, and modelversion. Confirm the shared prediction writer,
append-only behavior, and reporting-view visibility. Keep production static weights separate from
any evaluation weights.

Do not claim model quality from a smoke test. If the shared interface requires sport-specific
logic, stop and report the boundary rather than patching around it.

Include pre/post counts, timestamps, model versions, actual command/query/test output, exact
skipped work and omissions, risks, and PASS or STOP.
```

**Verification gate M3 → M4:** PASS only if all three models run on real MLB features through the
shared path, use new non-overwriting versions, and preserve the feature-table, interval, and
reporting-view boundaries.

## M4 — Run the MLB chronological backtest

**Use only after M3 passes.**

```text
Run the reusable backtesting harness on MLB across the approved multi-season range. Use
chronological train/test folds only and the same report structure used for tennis.

Report fold date ranges, train/test counts, target, modelversion, MAE, RMSE, signed bias, interval
coverage and target, scored rows, unscorable startup folds, and any calibration-by-bin results.
Compare baseline, GBM, and ensemble on identical deduplicated test rows. If odds or market lines
are unavailable or non-informative, say so and report no edge, hit rate, ROI, or profitability.

Prove for sampled rows that feature/prediction inputs precede the event and that fitted ensemble
weights use only earlier folds. Persist or reference append-only result and prediction versions
without overwriting older results. Investigate unexpectedly good results for leakage before
calling the model successful.

Include pre/post counts, timestamps, model versions, actual command/query/test output, exact
skipped work and reasons, risks, and PASS or STOP.
```

**Verification gate M4 → M5:** PASS only if the MLB report is chronological, comparable,
deduplicated, provenance-backed, and honest about market evidence. A strong number without a
leakage check or a random split is STOP.

## M5 — Write and accept the tennis-to-MLB change log

**Use only after M1–M4 pass.**

```text
Write a concise tennis-to-MLB translation playbook based only on accepted evidence. Do not start
generalization or NFL work in this prompt.

Separate the diff into: source and licensing, identifiers, schema/grain, schedule/team/game
context, ETL, feature configuration, injuries/availability, targets, model inputs, model code that
did not change, reporting-view/API changes, backtesting assumptions, market-data limitations, and
operational risks.

For every changed item cite the file/schema/query and the pre/post counts, timestamps, and
modelversion evidence. Explicitly list what stayed shared and what must remain configurable.
Include a “do not repeat” section for any leakage, fan-out, stale-version, ambiguous-name, demo
mixing, or unsupported market claim found during MLB work.

The playbook must end with a binary decision: MLB portability ACCEPTED or STOP. If accepted, state
that the next permitted phase is architecture generalization, not NFL implementation.

Include pre/post counts, timestamps, model versions (or “unchanged”), actual document/test/query
output, exact skipped work and omissions, risks, and PASS or STOP.
```

**Verification gate M5 → Generalization:** PASS only if the change log is evidence-linked and
explicitly distinguishes shared interfaces from sport-specific work. Do not open NFL directly.

---

# Phase 3 — Architecture generalization

## G1 — Move feature lists and sport settings into configuration

**Use only after M5 passes.**

```text
Make feature lists and sport settings configuration-driven for the already accepted tennis and
MLB paths. Do not add NFL features yet and do not change model behavior beyond removing duplicated
hardcoded feature lists.

Define the configuration contract for sport, targets, feature_version, feature columns, target
mapping, interval settings, fold schedule, and data-source metadata. Show the tennis and MLB
configs side by side. Prove that changing sport/config changes the selected feature inputs without
editing shared model scripts.

Run configuration validation, print the resolved configuration for each sport, and run a tennis
and MLB smoke path against fixed real rows. Report pre/post feature-row counts, timestamps,
feature versions, model versions (new versions only if outputs change), exact commands and tests,
and any config fields that remain hardcoded.

Do not silently default an absent feature or sport. Stop on invalid configuration. Include
pre/post counts, timestamps, model versions, actual command/test output, exact skipped work and
reasons, and PASS or STOP.
```

**Verification gate G1 → G2:** PASS only if both accepted sports resolve their features from
configuration, invalid settings fail explicitly, and no model behavior is silently changed.

## G2 — Verify shared model interfaces

**Use only after G1 passes.**

```text
Refactor or verify baseline, GBM, ensemble, and optional Bayesian interfaces so they accept a
validated feature table plus sport configuration, with no sport-specific logic in shared model
code.

Use the accepted tennis and MLB configs to run the same interfaces. Report function inputs,
resolved features, targets, fold settings, prediction schema, interval checks, writer behavior,
and modelversion naming for each sport. Prove models never query raw sport tables.

For ensemble evaluation, prove fitted weights use only earlier folds and production static weights
remain unchanged. For the optional Bayesian component, keep it behind an explicit configuration
flag and do not enable it unless the accepted tennis exit decision said KEEP.

Run interface and contract tests, including an invalid config test and a no-feature/no-target
STOP path. Include pre/post counts, timestamps, model versions, actual command/test output, exact
skipped work and reasons, risks, and PASS or STOP.
```

**Verification gate G2 → G3:** PASS only if one shared model path runs both sports through
configuration, raw reads are absent, and no production weight or unapproved Bayesian behavior
changed.

## G3 — Run cross-sport regression checks

**Use only after G2 passes.**

```text
Run cross-sport regression checks on accepted tennis and MLB fixtures and real bounded data.

Verify the shared output contract: prediction rows contain stable sport/player/game identifiers,
target, prediction, lowerci, upperci, modelversion, predictiontimestamp, and provenance; intervals
obey their invariant; append-only versions remain unchanged; chronological folds remain ordered;
and missing odds do not hide predictions.

Verify dashboard/API queries still use only vw_fact_player_prop_odds and that demo filtering is
preserved per sport. Verify no model or frontend path reads raw sport tables. Compare pre/post
counts, query plans or query output where useful, and exact test results for both sports.

Do not add NFL code or accept synthetic fixtures as evidence of cross-sport portability. Include
pre/post counts, timestamps, model versions, actual commands/tests/queries, exact skipped work and
reasons, risks, and PASS or STOP.
```

**Verification gate G3 → G4:** PASS only if both sports pass the shared contract and all boundary
regressions are evidenced. Any sport-specific bypass or raw-table read is STOP.

## G4 — Define and verify the generic reporting contract

**Use only after G3 passes.**

```text
Specify the generic reporting-view/API contract for tennis and MLB without changing the frontend
to read base tables.

Document required dimensions and measures: sport, event/game identity, player, team context when
present, prop type/target, modelversion, predictiontimestamp, prediction, lowerci, upperci,
actual_value, prediction_error, odds fields, edge fields, is_demo, and provenance/fold fields.
Document NULL behavior for upcoming rows and no-odds rows, fan-out behavior for multiple books, and
the deduplication key for accuracy metrics.

Run contract queries for real tennis and MLB predictions, with and without odds, and show the API
payloads consumed by the dashboard. Verify demo mode is explicit and visible. If a migration is
needed, add the next numbered migration and report it; never edit an old migration.

Include pre/post counts, timestamps, model versions, actual schema/query/test output, exact
skipped work and omissions, risks, and PASS or STOP.
```

**Verification gate G4 → G5:** PASS only if the same reporting contract explains both sports,
including NULL/no-odds and fan-out behavior, and the dashboard remains view-only.

## G5 — Write and accept the new-sport onboarding runbook

**Use only after G1–G4 pass.**

```text
Write a new-sport onboarding runbook that a person who did not build PipelineInsights can follow.
Do not implement NFL in this prompt.

The runbook must require, in order: source/licensing review; stable identifiers; raw schema and
game/team grain; ETL with counts and timestamps; feature configuration and temporal cutoff;
player_game_features validation; shared baseline/GBM/ensemble execution; append-only model
versions; chronological backtest; reporting-view/API contract; accuracy/calibration; market-data
availability; demo separation; edge-case review; and an explicit exit gate.

For each step state inputs, outputs, evidence, stop conditions, and prohibited shortcuts. Include
the tennis-to-MLB lessons: no random splits, no raw-table model reads, no frontend base-table
reads, no fuzzy identity matching, no silent repairs, and no accuracy-to-profit leap.

Test the runbook against the accepted tennis and MLB evidence and list any step that cannot be
reproduced. Include pre/post counts where applicable, timestamps, model versions, actual
validation output, exact skipped work and omissions, risks, and PASS or STOP.
```

**Verification gate G5 → NFL:** PASS only if the runbook is complete, reproducible against tennis
and MLB, and blocks an onboarding step when evidence is missing.

---

# Phase 4 — NFL implementation

## N1 — Map NFL sources, identifiers, and game grain

**Use only after G5 passes.**

```text
Map the approved real NFL sources before loading or modeling NFL data. Do not change the shared
model path or start live operation.

Document source and licensing/availability, seasons, update cadence, stable game/team/player
identifiers, play-by-play versus player-game-log grain, rosters, depth charts, injuries,
weather/venue, targets, realized outcomes, and odds availability. Map fields to the generic
team/game schema and identify every missing or estimated value.

Prove the source can support the required seasons and a bounded real slate. Report source row
counts, date range, teams/players/games, duplicate IDs, rejected rows, and ingestion timestamps
without treating demo data as NFL evidence. Stop if a required field or source is unavailable.

Include pre/post counts, timestamps, model versions (unchanged), actual schema/query output,
exact skipped work and omissions, risks, and PASS or STOP.
```

**Verification gate N1 → N2:** PASS only if a real NFL source and generic mapping are proven for
the bounded slate, with missing fields explicitly handled.

## N2 — Build NFL feature configuration and temporal features

**Use only after N1 passes.**

```text
Populate NFL player_game_features through the generalized configuration path. Keep NFL-specific
work in configuration and feature engineering, not shared model code.

Define and validate NFL features for short-season sample limits, weather, injury-report severity,
availability/depth-chart changes, positional matchups, opponent/team context, rest, travel, and
venue. For every feature report source timestamp and event cutoff; no feature may use information
published after the event.

Load a bounded real slate and report source/pre/post row counts, NULL/rejected rows, feature
version, targets, timestamps, and representative rows. Do not silently fill a late scratch or
missing weather value. Run feature/config invariants and prove models will read only
player_game_features.

Include pre/post counts, timestamps, model versions (unchanged), actual command/query/test output,
exact skipped work and reasons, risks, and PASS or STOP.
```

**Verification gate N2 → N3:** PASS only if NFL features are real, configuration-driven,
time-valid, and populated through the shared feature table with explicit missing-data behavior.

## N3 — Run NFL models and multi-season evaluation

**Use only after N2 passes.**

```text
Run baseline, GBM, and ensemble on NFL through the shared model path, then evaluate across the
approved multiple-season chronological folds.

Use new NFL modelversions and preserve every older version. Report feature config, targets,
train/test date ranges, rows read/written, prediction timestamps, interval validity, fold
provenance, model versions, and any ensemble weights. Prove evaluation weights use only earlier
folds and production static weights are unchanged.

Report MAE, RMSE, signed bias, interval coverage with target, scored rows, unscorable folds, and
edge/market status. Do not require the ensemble to win as a condition for hiding evidence; report
the actual result and investigate unexpectedly strong numbers for leakage. Do not call accuracy
profitability and do not claim market edge without real pre-match prices and an informative
sample.

Include pre/post counts, timestamps, model versions, actual commands/query/test output, exact
skipped work and omissions, risks, and PASS or STOP.
```

**Verification gate N3 → N4:** PASS only if NFL model outputs and multi-season metrics are
chronological, provenance-backed, versioned, and honestly separated from market evidence.

## N4 — Add sport switching through the reporting contract

**Use only after N3 passes.**

```text
Add or verify dashboard sport switching for accepted tennis, MLB, and NFL rows through
vw_fact_player_prop_odds and the existing API contract only.

Before changes, report the current dashboard routes, API queries, selected model/version filters,
and real/demo behavior. Implement the smallest scoped change needed for an explicit sport
selector. Each selector state must show the selected sport, mode, target/modelversion, row count,
and empty state. Do not query raw tables from frontend code and do not use a silent fallback to
another sport or demo data.

Test each sport with real rows, no-odds rows, upcoming NULL-actual rows, and explicit demo mode.
Report endpoint/UI output, pre/post counts, timestamps, model versions, and browser/test output.
Confirm accuracy metrics remain deduplicated and edge language remains separate from accuracy.

Include pre/post counts, timestamps, model versions, actual UI/API/test output, exact skipped work
and paths with reasons, risks, and PASS or STOP.
```

**Verification gate N4:** PASS only if all three sports switch through the reporting contract with
visible mode/sport state, correct empty behavior, no raw reads, and actual UI/API evidence.

---

# Phase 5 — Live operations and go-live

## O1 — Schedule ETL, features, and predictions

**Use only after N4 passes.**

```text
Design, implement, and exercise a scheduled pipeline for the approved live sport without
changing historical model versions or silently using demo data.

Define the schedule, dependency order, idempotency key, source watermark, retry/backoff behavior,
rate-limit handling, feature refresh boundary, prediction run, modelversion selection, and
dashboard freshness signal. The sequence must be ETL → validated features → predictions → reporting
visibility, with failures stopping downstream stages.

Run a bounded live or paper-trading exercise and report scheduled start/end timestamps, source
watermarks, pre/post counts for raw rows/features/predictions/reporting rows, model versions,
freshness, retries, and actual logs/output. Prove rerunning the same watermark does not overwrite
an existing modelversion or duplicate a prediction. Do not silently repair schema drift or missing
fields.

Include pre/post counts, timestamps, model versions, actual scheduler/log/query output, exact
skipped work and reasons, risks, rollback point, and PASS or STOP.
```

**Verification gate O1 → O2:** PASS only if the schedule runs in dependency order, is observable
and idempotent, creates fresh versioned predictions, and stops safely on upstream failure.

## O2 — Add monitoring for freshness, data quality, schema, odds, and performance

**Use only after O1 passes.**

```text
Define and exercise monitoring for the scheduled pipeline. Cover source freshness and watermarks,
row-count changes, duplicate/stable IDs, missing features, feature distribution drift, schema
changes, odds coverage and identity resolution, prediction freshness, interval validity, realized
accuracy/calibration once outcomes arrive, and model-version drift.

For every monitor state the threshold, query/input, expected result, alert severity, and operator
action. Test a healthy run and deliberately trigger or simulate each failure in a reversible
non-production environment. Report actual logs/query/test output, pre/post counts, timestamps,
model versions, alerts generated, and whether downstream prediction/dashboard stages stopped.

Do not turn missing market prices into an edge alert, do not evaluate unscored rows, and do not
silently repair intervals or names. Include pre/post counts, timestamps, model versions, actual
monitor/query/test output, exact skipped work and omissions, risks, and PASS or STOP.
```

**Verification gate O2 → O3:** PASS only if each required monitor has a tested healthy and failure
path, with actionable alerts and safe downstream behavior.

## O3 — Run a paper-trading or shadow period

**Use only after O1 and O2 pass.**

```text
Run the approved sport in paper-trading/shadow mode. Do not place bets, claim profitability, or
change production static weights during this period.

Capture each prediction as an immutable versioned record with prediction timestamp, data watermark,
modelversion, target, real/demo status, available pre-match price if any, decision/selection
reason, and later realized outcome. Separate predictions with no odds from priced observations.
Report daily/weekly counts, missed or late jobs, stale inputs, unresolved identities, interval
violations, accuracy/calibration for realized rows, and market-edge calculations only where a real
pre-match price and sufficient sample exist.

Reconcile scheduler logs, database rows, API/reporting rows, and dashboard display. Report
pre/post counts, timestamps, model versions, actual outputs, exact skipped work and items with
reasons, risks, and PASS or STOP.
```

**Verification gate O3 → O4:** PASS only if the shadow period is complete and auditable, with
accuracy separated from market results and no live financial action.

## O4 — Test an unattended full week

**Use only after O3 passes.**

```text
Run a full unattended-week test for the approved live pipeline. No manual database edits, demo
fallbacks, ad hoc feature repairs, or version overwrites are allowed.

Report every scheduled attempt and outcome across the week: source fetches, ETL rows, feature rows,
prediction rows, reporting-view/API rows, dashboard freshness, alerts, retries, missing fields,
odds identity outcomes, realized outcomes, and operator interventions. Include daily pre/post
counts, timestamps, watermarks, modelversions, and exact logs/queries/test output.

At the end, reconcile expected games/events to ingested games, expected predictions to persisted
predictions, and dashboard rows to the reporting view. Mark the test STOP if any gap is unexplained
or was hidden by a fallback. Do not call the week profitable based on accuracy.

Include pre/post counts, timestamps, model versions, actual logs/queries/test output, exact skipped
work and omissions, risks, and PASS or STOP.
```

**Verification gate O4 → O5:** PASS only if the full week completes with no unexplained gaps or
manual interventions and every failure/repair is recorded.

## O5 — Review rollback, recalibration, and go-live readiness

**Use only after O4 passes.**

```text
Conduct the final rollback/recalibration/go-live review. Do not silently promote a new
modelversion, change production weights, or delete historical predictions.

Document the rollback trigger, last-known-good modelversion and feature_version, database/API/UI
rollback procedure, scheduler pause/resume behavior, immutable evidence retained, and how to
replay a failed watermark safely. Document recalibration triggers based on realized accuracy,
interval coverage, drift, and sample size; separate those from market-edge decisions.

Review the tennis, MLB, and NFL evidence boundaries, model cards, onboarding runbook, monitoring,
shadow period, and unattended-week logs. Confirm historical versions remain queryable and that a
new modelversion is required for every changed feature, hyperparameter, model type, or weight.
State whether go-live is ACCEPTED or STOPPED and list every blocking risk.

Include a final matrix of pre/post counts, timestamps, model versions, actual commands/queries/logs,
test output, exact skipped work and omissions, risks, rollback owner/action, and PASS or STOP. A go-live PASS must
not claim profitability unless the market evidence separately satisfies its price/result/sample
requirements.
```

**Verification gate O5:** PASS only if rollback and recalibration are executable, the unattended
week passed, monitoring and shadow evidence are accepted, and all version/data/reporting
boundaries remain intact. Otherwise STOP.

---

## Final consistency check for this prompt pack

Before using or distributing this file, confirm:

- [ ] Every prompt has one bounded objective.
- [ ] Every prompt names prerequisites, stop conditions, evidence, omissions, and a separate gate.
- [ ] Every prompt asks for pre/post counts, timestamps, model versions, actual output, and a clear
      PASS or STOP.
- [ ] Tennis gates precede MLB, generalization, NFL, and operations.
- [ ] The active model is recorded as ATP-focused; captured odds are recorded as WTA; historical
      prop odds are recorded as unavailable.
- [ ] Accuracy is never described as profitability or market edge.
- [ ] No prompt asks for a random split, raw-table model read, frontend base-table read, fuzzy
      matching, silent interval repair, model-version overwrite, fabricated odds history, or
      unsupported market claim.
- [ ] The Bayesian layer requires an explicit tennis exit decision.
- [ ] Demo data remains available only through an explicit, visible mode.
- [ ] The file is plain Markdown and each prompt can be copied without rewriting.