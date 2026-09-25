Prepare the odds pipeline for the first ATP pairing

## Context

Prop odds capture began 2026-09-17. The first four nights were WTA only because the ATP tour did not play between the US Open final on 2026-09-13 and the Asian swing. ATP rows began on 2026-09-21. As of 2026-09-23, `odds_snapshots/tennis_props_2026-09.csv` holds 228 ATP rows from Chengdu and Hangzhou: 25 fixtures and 36 players.

The feature pipeline filters `WHERE player.tour = 'ATP'` and the model targets are `aces`, `double_faults`, and `service_games`. ATP markets seen so far: Sets Won, Games Won, Break Points Won, and **Player Aces (12 rows, FanDuel only, 6 players)**. Aces is the first market the model can actually be compared against. No Player Double Faults rows from any book so far. Service games is not offered as a prop at all.

This card was first written as preparation for ATP returning. ATP has now returned, so the end-to-end test here now runs on real rows as well as synthetic ones.

This card makes sure that when ATP resumes, the first pairing works and is noticed, rather than failing quietly.

## Tasks

1. Report the current state of the odds ingestion path end to end: which script or function reads the captured archive, how it resolves a provider player name to a `player_id`, how it resolves a provider fixture to a `match_id`, and where unresolved rows are recorded. Name the actual files.

2. Confirm unresolved rows are retained rather than dropped. Migration 008 made `odds.player_id` nullable with a CHECK requiring `provider_player_name` when `player_id` is absent, and there is an `odds_unresolved_names` table. Verify both are actually used by the ingestion path, and report what happens today to a row whose name does not resolve.

3. Write an end-to-end test using a small fixed sample of real ATP names and a synthetic prop row per target market — aces, double faults, service games. Assert the row resolves to a `player_id`, attaches to a `match_id`, and becomes visible through `vw_fact_player_prop_odds` with a non-NULL `line` and `edge`. Then run the same path over the real ATP rows in the archive. Report how many Player Aces rows end up paired with a `gbm_v1_aces` prediction in the view, and list every Player Aces row that did not pair along with the reason.

4. Report the fixture-to-match resolution risk explicitly. Event dates in `ROUND_OFFSETS` are estimated from the tournament start date rather than known per round, so a fixture's true date can differ from the stored `event_date`. State how much date tolerance the match resolution allows and what happens when two candidate matches fall inside that window.

5. Add a coverage summary the ingestion run prints every time: rows ingested, rows resolved to a player, rows unresolved, and a breakdown by league and by market. This is the readout that answers whether ATP markets exist, so it needs to be visible on every run rather than reconstructed later.

6. Verify the capture configuration needs no change. Confirm the nightly capture already requests the `atp` league alongside `wta` and `atp_challenger`, and already requests the Player Aces and Player Double Faults markets. Report the actual configured lists. If both are already present, say so and change nothing.

## Do not

Do not widen or narrow the capture's league, market, or sportsbook lists. Do not fabricate ATP odds rows outside the synthetic test in item 3, and label those clearly as synthetic so they cannot be mistaken for captured data. Do not attempt to backfill historical prop odds — they do not exist and cannot be purchased.

## Report

Report which items you completed and explicitly list any you did not do and why. Do not silently skip items.

## What to look for

Item 3 is the substance. Every stage of this path has been written but the whole chain has never completed once, because there has never been an ATP prop row to send through it. Proving it on synthetic data now is far cheaper than discovering a resolution bug on the first real night and losing that night's pairing.

Item 4 is the quiet risk. Estimated event dates mean fixture-to-match resolution is doing approximate date matching, and approximate matching that silently picks a winner will attach odds to the wrong match. The correct behavior when two matches are plausible is to refuse and record the row as unresolved.

Item 6 should end in "no changes needed." It is included so that conclusion is verified against the configuration rather than assumed.
