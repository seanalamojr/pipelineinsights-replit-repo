Add a dashboard accuracy panel driven by real outcomes

## Context

Once backtest predictions are persisted (Card D), the dashboard can show something it currently cannot: how close the model's predictions came to what actually happened, on real players over real matches.

This is the answer to "is the model working" that does not require any betting odds. It compares prediction to outcome. It says nothing about whether the model can beat a sportsbook — that needs prices, which only exist going forward.

The dashboard reads only `vw_fact_player_prop_odds`. If actual outcomes are not reachable through it, extend the view in a new migration rather than querying base tables from the frontend.

## Tasks

1. Report where the actual realized stat values live — the table and column for actual aces, double faults, and service games per player per match — and confirm they are reachable from the view. Paste the relevant schema.

2. Extend the reporting view in the next numbered migration to expose the actual outcome alongside the prediction, plus the signed error (prediction minus actual). Leave both NULL for matches that have not been played, and do not filter unplayed matches out of the view — the dashboard needs upcoming predictions too.

3. Build a panel showing, per prop type and per `modelversion`: mean absolute error, the share of actual outcomes that landed inside the `lowerci`–`upperci` interval, and the row count behind each figure. Always display the row count next to the metric.

4. Make the baseline and the GBM directly comparable in the panel, side by side on the same prop type, since the entire purpose of the baseline is to be the bar the GBM must clear.

5. Label the interval coverage honestly. If the intervals are built as an 80% range, state the target next to the observed number so an observed 77% reads as slightly narrow rather than as a passing grade. Do not present coverage without its target.

6. Exclude demo rows, following the convention in Card B. If demo rows are being displayed, label it on screen.

7. Add a short on-screen note distinguishing accuracy from edge — one or two sentences, in plain language, stating that these figures measure closeness to real outcomes and not profitability against a sportsbook.

## Do not

Do not query base tables from the dashboard. Do not compute metrics in the frontend that the view or API can compute. Do not mix model versions into a single blended metric. Do not display any metric without its row count.

## Report

Report which items you completed and explicitly list any you did not do and why. Do not silently skip items.

## What to look for

Item 7 is the one that protects against the most expensive misunderstanding this project can produce. An accuracy panel showing a strong improvement over baseline reads, to anyone glancing at it, like a signal to place a bet. It is not. The on-screen sentence is cheap and prevents that leap.

Item 3's row-count requirement exists because a mean absolute error computed over eleven rows and one computed over sixty thousand look identical on a card and mean entirely different things. Also watch for the row-multiplication hazard from Card C: when odds exist, one prediction fans out per book, so any metric averaged over the raw view will weight predictions by how many books priced them.
