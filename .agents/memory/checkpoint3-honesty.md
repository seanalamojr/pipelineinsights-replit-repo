---
name: Checkpoint 3 honesty
description: Decision for handling demo data, unavailable metrics, and reporting-view boundaries before real ETL and models.
---

Checkpoint 3 must show the pipeline and dashboard working without implying that a trained or evaluated model exists. Demo rows are labeled, predictions remain traceable to stored market snapshots, and RMSE/model-agreement values stay unavailable until a time-based backtest joins predictions to realized outcomes.

**Why:** Filling those fields with plausible-looking values would make the checkpoint visually complete but analytically misleading, especially for an MSBA learning project.

**How to apply:** Preserve the reporting-view-only dashboard boundary, use explicit empty or pending states for unimplemented evaluation, and only populate evaluation metrics from real realized outcomes in a later approved checkpoint.