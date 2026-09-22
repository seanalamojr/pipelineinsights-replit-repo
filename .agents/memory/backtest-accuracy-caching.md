---
name: View-backed accuracy caching
description: Startup and caching constraints for accuracy reports built from the shared tennis reporting view.
---

Accuracy reports that aggregate the shared player-prop reporting view should be computed before the API begins serving requests and reused briefly for dashboard reads.

**Why:** The view joins realized outcomes, market rows, feature rows, and injury context. A cold aggregate can exceed the preview proxy's request window even when the resulting report is small; repeated browser requests should not repeat that work.

**How to apply:** Keep the report server-computed and view-backed, prewarm it during API route initialization, use a short cache lifetime, and invalidate or refresh it when a new backtest run is available.

Persisted fold metadata uses the unsuffixed model version, while prediction rows use a timestamped `_backtest_` suffix; pooled fold `0` is not a realized test fold.

**Why:** Joining provenance on the full prediction version silently produced zero fold counts, and counting the pooled row overstated the number of evaluated folds.

**How to apply:** Normalize the prediction version to its base prefix for provenance joins, and count only positive fold numbers when reporting realized fold coverage.