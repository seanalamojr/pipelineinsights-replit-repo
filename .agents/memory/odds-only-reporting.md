---
name: Odds-only reporting
description: Why verified odds and results need a separate reporting path when forecasts are absent.
---

Preserve the prediction-anchored dashboard view's contract; report independently verified odds/results through an odds-anchored path until there are genuine predictions for those matches. Do not manufacture predictions just to make paired odds visible in a prediction-based view.

**Why:** A successful odds/result pairing does not imply a model forecast was ever produced. A left join from predictions excludes those valid paired rows entirely; a synthetic forecast would compromise model evaluation.

**How to apply:** When importing a new sport or tour with verified results but no predictions, count paired rows from the odds reporting path and explicitly leave unobserved player-prop totals NULL.