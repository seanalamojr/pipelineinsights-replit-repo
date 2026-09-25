# Getting these cards into your Replit repo

The target location is `docs/agent-cards/`, next to `docs/model-card-tennis-v1.md`. Keeping them in the repo means a Replit agent can read the full card with a short prompt, rather than you pasting 40 lines each time.

There are three ways to do this. Option 1 is the simplest.

---

## Option 1 — Upload the zip (about 2 minutes)

1. Download `pipelineinsights-agent-cards.zip` from the chat.
2. In Replit, open the Files panel on the left. Click the three-dot menu, then **Upload file**, and upload the zip to the project root.
3. Open the Shell tab and paste:

```bash
mkdir -p docs/agent-cards && unzip -o pipelineinsights-agent-cards.zip -d docs/ && rm pipelineinsights-agent-cards.zip && ls docs/agent-cards
```

4. Check the listing shows 11 files: `00-INDEX.md`, `01-context-brief.md`, cards A through H, and this guide.
5. Commit the change through the Git panel with a message like `Add agent task cards`.

What that shell line does: it creates the folder, unpacks the zip into `docs/` (the zip already contains an `agent-cards/` folder inside it), deletes the zip so it does not get committed, and lists the result so you can check it.

---

## Option 2 — Let the Replit agent place them

Upload the zip as in steps 1–2 above, then paste this as a new task on your board:

> Unzip `pipelineinsights-agent-cards.zip` from the project root into `docs/`, so the files end up in `docs/agent-cards/`. Then delete the zip. Do not change the contents of any file. Do not act on any of the cards — they are task instructions for later, not for now. Report the final file list with the size of each file, and confirm the zip has been removed.

The "do not act on the cards" line matters. Agents that find instruction files sometimes start carrying them out.

---

## Option 3 — Upload files one at a time

If you prefer the individual `.md` files shared in the chat, create a `docs/agent-cards/` folder in the Files panel, open it, and upload each file into it. It works fine, it just takes more clicks.

---

## Running a card once it's in the repo

Rather than pasting the full card text, paste a short pointer into "Plan a new task…":

> Read `docs/agent-cards/01-context-brief.md` for project background, then carry out `docs/agent-cards/card-A-run-pipeline-real-data.md` exactly as written. Follow its "Do not" section and its reporting instructions.

Change the card filename each time. The prompts stay short, the instructions stay consistent, and if you edit a card later, every future run picks up the new version.

Pasting the full card text into the task box still works too, if you prefer. Every card is written to stand on its own.

---

## Suggested order

| # | Card | Why this order |
|---|---|---|
| 1 | A — Run pipeline on real data | Most likely fix for the empty dashboard. Run it alone and check the dashboard before going on. |
| 2 | G — Verify OOF guard test | Quick. Confirms your cleanup pass actually fixed the vacuous test. |
| 3 | H — ATP odds pairing | **More urgent now.** Real ATP aces odds exist, so this is the first chance for model-vs-market pairing. |
| 4 | F — Surname resolver | Improves how many ATP names match in H. Can run before or after H. |
| 5 | B — Separate demo from real | Only if A didn't already clear the fake names. |
| 6 | C — Verify reporting view | Tests only. Low risk. |
| 7 | D — Persist backtest predictions | Makes historical accuracy visible. |
| 8 | E — Accuracy panel | Needs D first. |

Your board already has #13 "Populate corrected ensemble objective results" drafted. That can run whenever you like. None of these cards depend on it, and it doesn't depend on them.
