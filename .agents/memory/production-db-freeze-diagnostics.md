---
name: Production database freeze diagnostics
description: How to handle a frozen production SQL endpoint when the Database pane offers no unpause control.
---

A "frozen" response from the production SQL tool does not guarantee that the Database pane exposes an Unpause button. If Production Overview, My Data, and Settings show no such control, and no conflicting DATABASE_URL secret is present, do not tell the user to keep looking or to regenerate credentials. Replit's database guidance directs this case to support for endpoint investigation.

For accounts that automatically resume after their balance recovers, there may be no manual Unpause step at all. A successful read-only production query confirms the database endpoint is responding again; an earlier frozen result is not permanent.

A filtered secret-existence check for DATABASE_URL can return true because DATABASE_URL is runtime-managed. Check the unfiltered secret-name listing before concluding that a duplicate user-added secret exists; do not remove the managed database credential.

**Why:** The read-only production query interface reported a frozen database while the visible Production Database pane showed tables and settings but no unpause control. The endpoint later answered a read-only query without a manual unpause. A targeted secret lookup reported runtime-managed DATABASE_URL existence while an unfiltered secret listing showed no user-added DATABASE_URL. A failed publish separately showed API startup and health-check failure; its logs did not expose a definitive database exception, so database causality must not be overstated.

**How to apply:** Distinguish successful compilation from failed promotion, check the available database UI and unfiltered secret names, and describe the frozen endpoint as a likely contributing issue rather than a proven startup cause. Recheck endpoint availability before escalating; if it responds, try a fresh publish instead of changing credentials. If it remains frozen without a user-accessible control, provide the exact error and publish log symptoms for support without changing or exposing credentials.