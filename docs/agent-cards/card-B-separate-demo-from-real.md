Separate demo data from real data in the dashboard

## Context

`scripts/seed_demo.py` seeds eight fake players with `demo_` id prefixes (Ava Chen, Mateo Silva, Jordan Brooks, Noah Okafor, Sofia Rossi, Mina Park, Elena Petrova, Layla Morgan), plus fake rows in `odds` and `player_prop_predictions`. Those fake rows are currently indistinguishable from real ones in the dashboard, so the app looks populated while showing nothing real.

`evaluation/checkpoint12.py` already handles this correctly for its market comparison, using `WHERE prediction.player_id NOT LIKE 'demo_%'` and `market.provider <> 'demo'`. Follow that existing precedent rather than inventing a new convention.

Run Card A first. If real predictions do not exist yet, this card has nothing to separate.

## Tasks

1. Report how the dashboard currently obtains its rows: the file, the query or endpoint, and whether any demo filtering exists today. Paste the relevant code.

2. Add an `is_demo` boolean to `vw_fact_player_prop_odds` in a new migration, derived from `player_id LIKE 'demo_%'` OR the odds provider being `'demo'`. Do not edit an existing migration file — add the next numbered one, and add its version row to `pipelineinsights_schema_migrations` the way the existing migrations do.

3. Make the dashboard exclude demo rows by default. Keep demo data reachable behind an explicit toggle or query parameter rather than deleting it, because the demo seed is useful for UI work when the database is empty.

4. Show the user which mode they are in. If the dashboard is displaying demo rows, label it visibly on screen. A dashboard silently showing fake data is worse than an empty one.

5. Handle the empty state deliberately. If there are zero real predictions, the dashboard should say so plainly and say what to run — not render a blank panel or fall back to demo rows without saying so.

6. Confirm the separation works. Report the row count the dashboard query returns in default mode and in demo mode, and confirm the two do not overlap.

## Do not

Do not delete the demo seeder or its data. Do not change the existing demo `player_id` prefix convention. Do not modify model code. Do not alter the LEFT JOIN on `odds` — predictions must remain visible when no odds exist.

## Report

Report which items you completed and explicitly list any you did not do and why. Do not silently skip items.

## What to look for

Item 4 is the one that matters most and is easiest to skip. The failure this prevents is the expensive kind: looking at a chart, believing it, making a decision on it, and only later discovering it was seeded fixture data. Any fallback to demo data must be visible on screen, not merely documented.

Item 2 asks for a derived column rather than a hardcoded exclusion so the rule lives in one place. If the demo convention ever changes, one view definition changes rather than every dashboard query.
