---
name: Current tennis feed quality
description: Data-quality constraints observed in attached current-season Sackmann-format feeds.
---

Current-season tennis CSVs may use nonnumeric qualifier seed codes, omit player IDs on otherwise completed rows, or contain impossible service-stat combinations. Never synthesize a player ID from a name. Skip rows without stable match/player identifiers, and preserve valid match context while storing inconsistent service-stat blocks as NULL.

**Why:** A current feed included qualifier seeds, five completed rows without loser IDs, and a service-stat row where double faults exceeded serve points. Treating those values as numeric would either abort ingestion or pollute target distributions.

**How to apply:** Validate identifiers and basic service-stat invariants in the attached/current-data path before upsert and rebuild the leakage-safe feature table. Report every skipped or sanitized row.