-- Checkpoint 3 support: expose matchup context through the dashboard view and
-- prevent duplicate demo market rows when the seed script is re-run.

CREATE UNIQUE INDEX IF NOT EXISTS odds_market_dedupe_idx
    ON odds (match_id, player_id, book, prop_type, line);

CREATE OR REPLACE VIEW vw_fact_player_prop_odds AS
SELECT
    prediction.prediction_id,
    prediction.player_id,
    player.full_name AS player,
    player.tour,
    prediction.match_id,
    match.event_date,
    match.tournament,
    match.surface,
    prediction.sport,
    prediction.prop_type,
    prediction.prediction,
    prediction.lowerci,
    prediction.upperci,
    prediction.modelversion,
    prediction.predictiontimestamp,
    market.book,
    market.line,
    market.over_price,
    market.under_price,
    market.captured_at,
    CASE
        WHEN market.line IS NULL THEN NULL
        ELSE prediction.prediction - market.line
    END AS edge,
    CASE
        WHEN market.line IS NULL THEN NULL
        WHEN prediction.prediction >= market.line THEN 'Over'
        ELSE 'Under'
    END AS side,
    opponent.full_name AS opponent,
    player.full_name || ' vs ' || COALESCE(opponent.full_name, 'TBD') AS matchup,
    injury.status
FROM player_prop_predictions AS prediction
JOIN players AS player
    ON player.player_id = prediction.player_id
JOIN matches AS match
    ON match.match_id = prediction.match_id
   AND match.player_id = prediction.player_id
LEFT JOIN players AS opponent
    ON opponent.player_id = match.opponent_id
LEFT JOIN odds AS market
    ON market.match_id = prediction.match_id
   AND market.player_id = prediction.player_id
   AND market.prop_type = prediction.prop_type
LEFT JOIN injuries AS injury
    ON injury.player_id = prediction.player_id
   AND injury.event_date = match.event_date;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('005_demo_context')
ON CONFLICT (version) DO NOTHING;