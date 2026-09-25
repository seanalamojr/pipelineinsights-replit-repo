# Replit board cards — how to use this set

Plain-language guide. Read this one; paste the others.

## What this is

Your Replit board takes one prompt per card. These files are written to be pasted straight into "Plan a new task…" with no editing. One file equals one card.

Your board is at #13 with "Populate corrected ensemble objective results" already drafted, so these slot in after it.

## Paste this one first, once

`01-context-brief.md` is not a task. It is shared background — the architecture rules, the current state of the database, and the things that are already verified true. Paste it as its own message to the agent at the start of a working session, or keep it open and prepend it to any card whose agent seems confused about the project.

Every card below is written to stand alone, so you do not strictly need the brief. It exists because board cards run in isolation and agents drift when they have to guess.

## The important correction driving this set

Earlier I told you the GBM had no way to save predictions. That was wrong. `models/baseline.py` line 297 defines `upsert_predictions`, and `models/gbm.py` and `models/ensemble.py` both import and call it. All three models already persist to `player_prop_predictions`.

So nothing needs building. Your dashboard shows fake names because `scripts/seed_demo.py` is the only thing that has actually been run against your database. The real pipelines were never executed on real data.

That is why Card A is just "run the thing," and why it comes first. It is plausible that Card A alone fixes your empty dashboard.

## Order, and why

| Order | Card | What it gets you | Depends on |
|---|---|---|---|
| 1 | A — Run the pipeline on real data | Real names and real predicted values in the database | The 2018–2025 history load (your Done #3) |
| 2 | B — Separate demo from real | Dashboard stops showing Ava Chen and friends | A |
| 3 | C — Verify the reporting view | Proof the view behaves correctly with predictions but no odds | A, B |
| 4 | D — Persist backtest predictions | Historical accuracy becomes visible, not just in a report file | A |
| 5 | E — Accuracy panel | Predicted vs actual on screen | D |
| 6 | F — Fix the surname alias gap | Odds name matching stops failing on compound surnames | none |
| 7 | G — Verify the OOF weight guard test | Confirms the cleanup pass actually fixed the vacuous test | your cleanup pass |
| 8 | H — ATP resumption readiness | Catches the first real odds pairing when ATP returns | F |

Cards F, G, and H are independent of the dashboard work. Run them whenever.

**Update, 2026-09-23:** ATP prop odds started arriving on 2026-09-21: 228 rows from Chengdu and Hangzhou, including 12 Player Aces rows from FanDuel. That makes Card H more urgent, because aces is the first market where your model and a real book price can meet. See `PLACEMENT-GUIDE.md` for the revised order.

## Do A first and stop

Genuinely — run Card A, look at your dashboard, and come back. If real names appear, Cards B and C get much smaller, and you will have spent one card instead of eight. There is no point planning around a problem that a single pipeline run might resolve.

## What none of these cards do

They do not attempt to backtest against historical market odds. That is not possible: prop lines for 2015–2025 were never archived and cannot be bought. Your odds history begins where your nightly capture began.

Two separate questions, worth keeping straight:

- **Accuracy** — is the prediction close to what actually happened? Answerable from historical stats alone. Cards D and E make this visible.
- **Edge** — does the prediction beat the price a book was offering? Needs the price as it stood before the match. Only collectable going forward. Card H is the readiness check for when that starts working.

A model can be accurate and still have no edge. Proving accuracy is a prerequisite, not the finish line.

## Card format

Each card has: a title line you can use as the card name, a short context block, numbered tasks, explicit "do not" guardrails, and a closing instruction to report completions and omissions. That last line matters — it is the thing that has consistently produced honest reports rather than silent skips.

## Note on model versions

Project rule, enforced in several cards: never overwrite an existing `modelversion`. The table has `UNIQUE (player_id, match_id, prop_type, modelversion)`, so a re-run with the same version silently updates rows in place and you lose the comparison. Bump the version on any change to features, model type, hyperparameters, or ensemble weights.
