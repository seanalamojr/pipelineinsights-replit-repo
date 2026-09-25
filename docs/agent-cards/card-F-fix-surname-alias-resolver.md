Fix the compound-surname gap in the odds name resolver

## Context

The odds name resolver builds candidate aliases from a player's name in `_name_aliases`. It derives the surname as `tokens[-1]` — the last whitespace-separated token only.

That is wrong for any compound surname. For `Aaron Gil Garcia` it generates `a garcia`, `aaron gil garcia`, and `garcia a`, but never `gil garcia a` or `a gil garcia`. So a sportsbook rendering the name as `Gil Garcia A.` will not match, even though the player is unambiguously in the table.

This was measured, not guessed: every one of 36 surname-initial misses in a real archive involved a unique surname, so the cause is alias generation, not genuine ambiguity. It disproportionately affects Spanish, Portuguese, Arabic, and Dutch names, which means it hits Challenger draws hardest — exactly where the deepest fixture lists are.

This is independent of the dashboard work and can run at any time.

## Tasks

1. Reproduce the bug before changing anything. Write a failing test asserting that `Aaron Gil Garcia` produces an alias matching the form `Gil Garcia A.`. Run it, paste the failure output, and confirm it fails for the stated reason.

2. Report the current alias list generated for these five names, before your fix: `Aaron Gil Garcia`, `Botic Van De Zandschulp`, `Pierre-Hugues Herbert`, `Thiago Agustin Tirante`, and a single-token name of your choosing. Paste actual output.

3. Change alias generation to consider multiple surname splits rather than assuming the surname is one token. Generate candidates for each plausible split point instead of picking one, since which tokens form the surname cannot be determined reliably from the string alone.

4. Handle the cases that break naive splitting: hyphenated given names such as `Pierre-Hugues`, lowercase particles such as `van`, `de`, `van de`, `del`, and `bin`, and names already supplied in `Surname F.` form.

5. Confirm your test from item 1 now passes, and report the alias lists from item 2 again so the before and after can be compared directly.

6. Check for new collisions. Generating more aliases risks two different players producing the same alias, which is worse than a miss because it resolves confidently to the wrong person. Run the generator across the full player table and report every alias that maps to more than one `player_id`. If any exist, state how the resolver handles them — it should refuse to resolve an ambiguous alias rather than pick one.

7. Re-run the resolver over the existing captured archive and report the match rate before and after. The archive now contains 228 ATP rows (36 distinct ATP players, from Chengdu and Hangzhou, captured from 2026-09-21). Report the match rate for the ATP rows only, separately from WTA. WTA is expected to stay at 0% because the feature pipeline filters for ATP. For each ATP name that still fails, give the reason: not in the player table, the alias form, or ambiguity. Several misses are likely qualifiers missing from the historical player table. Those are not resolver bugs and should be counted separately.

## Do not

Do not resolve ambiguous aliases by guessing. Do not remove the existing alias forms that already work. Do not loosen matching into fuzzy or edit-distance matching — this card is about generating the right exact candidates, not about approximate matching.

## Report

Report which items you completed and explicitly list any you did not do and why. Do not silently skip items.

## What to look for

Item 1 comes first for a reason. A test written after a fix, against code that already works, proves nothing about whether it would have caught the bug. Paste the failure.

Item 6 is the risk this fix introduces, and it is a worse failure than the one being fixed. A missed name is visible as an unresolved row you can go and inspect. A wrong confident match silently attributes one player's odds to another player's predictions, and nothing downstream will flag it.
