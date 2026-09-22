---
name: Checkpoint 12 evaluation
description: Durable rules for historical walk-forward scoring and reporting.
---

Historical monthly folds can contain a non-empty first test window with no strictly earlier training rows. Those folds are unscorable and must be skipped explicitly, not fitted against future data or treated as zero-error results.

**Why:** The configured full-history window starts before the first eligible training observation; forcing a fit would violate the time boundary.

**How to apply:** Preserve the skipped-fold reason in detailed output and keep scored-row counts separate from the configured calendar-window count.

The stored MAE-improvement metric is a percentage-point value such as `20.25`, not a fraction such as `0.2025`.

**Why:** Reports that format the stored value as a fraction produce misleading claims like `2025%`.

**How to apply:** Format this metric directly with a percent sign; use fraction-to-percent formatting only for coverage values.

Persisted fold provenance uses the last date eligible for training, not the exclusive boundary that begins the test window.

**Why:** This makes the row-level claim literal and auditable: the stored training cutoff must be strictly earlier than every associated event date, including events on the first test day.

**How to apply:** Keep walk-forward splitting at `training < test-start` and `test >= test-start`, but persist the date immediately before test-start as the training cutoff.