---
name: Odds identity boundary
description: Auditable rules for bridging provider odds identities to internal tennis entities.
---

Provider player and fixture identifiers must never be treated as internal `players` or `matches` keys. Resolve names only by raw exact or deterministic normalization (case, accents, punctuation, and surname-initial aliases); do not add fuzzy matching. When the source tour is known, require a compatible internal player tour so WTA rows cannot attach to same-named ATP players. Preserve unresolved odds with provider names and stable provider player IDs, and record their league and row counts for later mapping. Keep provider odds identifiers separate from generated database primary keys.

**Why:** Silent fuzzy or cross-tour matches can attach a line to the wrong player, while dropping unresolved rows makes missing markets indistinguishable from no market being offered. Names can change or collide, so the provider player ID is needed for safe reconciliation.

**How to apply:** Keep the provider name, provider player ID, provider event ID, provider odds ID, provider event start time, and capture time in provenance columns. Some raw exports store the player in `selection` and Over/Under in `selection_line`; preserve that distinction. Use the migration-backed resolution fields and require a reported raw-versus-normalized match rate plus tour compatibility for every archive load.