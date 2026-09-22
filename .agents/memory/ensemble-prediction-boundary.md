---
name: Ensemble prediction boundary
description: The separation between production ensemble generation and walk-forward weight fitting.
---

Production ensemble generation must read only versioned rows from `player_prop_predictions`; it must not rerun feature engineering or member models. Walk-forward evaluation may fit weights from member predictions and outcomes in strictly earlier scored folds, then apply those weights to the current fold. Production uses the configured static weights unless a separately persisted, time-safe weight artifact is introduced.

**Why:** The prediction table does not contain target outcomes, and using current-fold outcomes to fit weights would make the reported ensemble improvement optimistic.

**How to apply:** Keep database reads for `models/ensemble.py` limited to versioned prediction rows. In evaluation, make the prior-fold boundary explicit in both the data passed to weight fitting and the report.