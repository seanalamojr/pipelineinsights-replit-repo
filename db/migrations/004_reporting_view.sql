-- This is the only database object the dashboard should query.
-- A prediction is repeated per available sportsbook line so line shopping
-- remains visible without putting market logic in the frontend.

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
    END AS side
FROM player_prop_predictions AS prediction
JOIN players AS player
    ON player.player_id = prediction.player_id
JOIN matches AS match
    ON match.match_id = prediction.match_id
   AND match.player_id = prediction.player_id
LEFT JOIN odds AS market
    ON market.match_id = prediction.match_id
   AND market.player_id = prediction.player_id
   AND market.prop_type = prediction.prop_type;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('004_reporting_view')
ON CONFLICT (version) DO NOTHING;