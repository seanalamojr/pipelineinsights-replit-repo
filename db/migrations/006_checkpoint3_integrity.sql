-- Checkpoint 3 corrections:
-- 1. Keep one row per captured sportsbook snapshot so historical line movement
--    is not silently overwritten.
-- 2. Expose actual outcomes and stored rolling values through the reporting
--    view so trends never substitute a prediction for an observed result.
-- 3. Pick the latest injury record for a player/date to avoid multiplying rows.

DROP INDEX IF EXISTS odds_market_dedupe_idx;

CREATE UNIQUE INDEX IF NOT EXISTS odds_snapshot_dedupe_idx
    ON odds (match_id, player_id, book, prop_type, line, captured_at);

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
    injury.status,
    CASE lower(prediction.prop_type)
        WHEN 'games won' THEN match.games_won::numeric
        WHEN 'aces' THEN match.aces::numeric
        WHEN 'double faults' THEN match.double_faults::numeric
        WHEN 'minutes' THEN match.minutes::numeric
        ELSE NULL
    END AS actual_value,
    COALESCE(
        NULLIF(
            feature.feature_values -> 'rolling_mean_5' ->> prediction.prop_type,
            ''
        )::numeric,
        feature.rolling_mean_5
    ) AS rolling_average
FROM player_prop_predictions AS prediction
JOIN players AS player
    ON player.player_id = prediction.player_id
JOIN matches AS match
    ON match.match_id = prediction.match_id
   AND match.player_id = prediction.player_id
LEFT JOIN players AS opponent
    ON opponent.player_id = match.opponent_id
LEFT JOIN player_game_features AS feature
    ON feature.match_id = prediction.match_id
   AND feature.player_id = prediction.player_id
LEFT JOIN odds AS market
    ON market.match_id = prediction.match_id
   AND market.player_id = prediction.player_id
   AND market.prop_type = prediction.prop_type
LEFT JOIN LATERAL (
    SELECT injury_row.status
    FROM injuries AS injury_row
    WHERE injury_row.player_id = prediction.player_id
      AND injury_row.event_date = match.event_date
    ORDER BY injury_row.captured_at DESC, injury_row.injury_id DESC
    LIMIT 1
) AS injury ON TRUE;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('006_checkpoint3_integrity')
ON CONFLICT (version) DO NOTHING;