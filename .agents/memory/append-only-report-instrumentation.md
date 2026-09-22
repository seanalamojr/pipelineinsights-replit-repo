---
name: Append-only report instrumentation
description: New evaluation metrics cannot be reconstructed by report-only rebuilds from older append-only runs.
---

When report instrumentation adds new metric rows, a report-only rebuild from an older append-only run must mark those values unavailable rather than infer them from unrelated metrics.

**Why:** The persisted backtest table contains the prior run's metrics but not the historical fold predictions needed to recreate newly added objective comparisons or fitted weights.

**How to apply:** Keep the report generator backward-compatible and explicit about provenance; run the corrected evaluator before claiming newly instrumented values.