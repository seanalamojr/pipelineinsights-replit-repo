-- Checkpoint 4 completion:
-- 1. Odds can be captured before player resolution.
-- 2. Match rows support service-game outcomes.
-- 3. The reporting view guards unplayed outcomes and exposes normalized edge.

ALTER TABLE odds
    ALTER COLUMN player_id DROP NOT NULL;

ALTER TABLE odds
    ADD COLUMN IF NOT EXISTS provider_player_name TEXT,
    ADD COLUMN IF NOT EXISTS provider_team_name TEXT,
    ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

UPDATE odds AS market
SET provider_player_name = player.full_name,
    resolved_at = market.captured_at
FROM players AS player
WHERE market.player_id = player.player_id
  AND (market.provider_player_name IS NULL OR market.resolved_at IS NULL);

ALTER TABLE odds
    DROP CONSTRAINT IF EXISTS odds_player_fk;

ALTER TABLE odds
    ADD CONSTRAINT odds_resolution_ck
        CHECK ((player_id IS NULL) = (resolved_at IS NULL)),
    ADD CONSTRAINT odds_provenance_ck
        CHECK (provider_player_name IS NOT NULL OR player_id IS NOT NULL);

ALTER TABLE matches
    ADD COLUMN IF NOT EXISTS service_games INTEGER;

DROP VIEW IF EXISTS vw_fact_player_prop_odds;

CREATE VIEW vw_fact_player_prop_odds AS
WITH fact AS (
    SELECT
        prediction.prediction_id,
        prediction.player_id,
        player.full_name AS player,
        player.tour,
        prediction.match_id,
        match_row.event_date,
        match_row.tournament,
        match_row.surface,
        prediction.sport,
        prediction.prop_type,
        prop.display_label AS prop_label,
        prediction.prediction,
        prediction.lowerci,
        prediction.upperci,
        prediction.modelversion,
        prediction.predictiontimestamp,
        market.provider,
        market.provider_event_id,
        market.provider_market_id,
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
            ELSE (prediction.prediction - market.line)
                / NULLIF(prediction.upperci - prediction.lowerci, 0)
        END AS normalized_edge,
        CASE
            WHEN market.line IS NULL THEN NULL
            WHEN prediction.prediction >= market.line THEN 'Over'
            ELSE 'Under'
        END AS side,
        opponent.full_name AS opponent,
        player.full_name || ' vs ' ||
            COALESCE(opponent.full_name, 'TBD') AS matchup,
        injury.status,
        feature.feature_version,
        feature.rolling_mean_5 AS rolling_average,
        player.player_id LIKE 'demo_%%' AS is_demo,
        CASE
            WHEN match_row.event_date > CURRENT_DATE THEN NULL
            ELSE CASE prop.prop_key
                WHEN 'games_won' THEN match_row.games_won::numeric
                WHEN 'sets_won' THEN match_row.sets_won::numeric
                WHEN 'aces' THEN match_row.aces::numeric
                WHEN 'double_faults' THEN match_row.double_faults::numeric
                WHEN 'service_games' THEN match_row.service_games::numeric
                ELSE NULL
            END
        END AS actual_value
    FROM player_prop_predictions AS prediction
    JOIN players AS player
        ON player.player_id = prediction.player_id
    JOIN prop_types AS prop
        ON prop.prop_key = prediction.prop_type
    JOIN matches AS match_row
        ON match_row.match_id = prediction.match_id
       AND match_row.player_id = prediction.player_id
    LEFT JOIN players AS opponent
        ON opponent.player_id = match_row.opponent_id
    LEFT JOIN LATERAL (
        SELECT feature_row.feature_version, feature_row.rolling_mean_5
        FROM player_game_features AS feature_row
        WHERE feature_row.match_id = prediction.match_id
          AND feature_row.player_id = prediction.player_id
          AND feature_row.stat_target = prediction.prop_type
        ORDER BY feature_row.created_at DESC, feature_row.feature_version DESC
        LIMIT 1
    ) AS feature ON TRUE
    LEFT JOIN odds AS market
        ON market.match_id = prediction.match_id
       AND market.player_id = prediction.player_id
       AND market.prop_type = prediction.prop_type
    LEFT JOIN LATERAL (
        SELECT injury_row.status
        FROM injuries AS injury_row
        WHERE injury_row.player_id = prediction.player_id
          AND injury_row.event_date = match_row.event_date
        ORDER BY injury_row.captured_at DESC, injury_row.injury_id DESC
        LIMIT 1
    ) AS injury ON TRUE
)
SELECT
    fact.*,
    CASE
        WHEN fact.actual_value IS NULL THEN NULL
        ELSE fact.actual_value - fact.prediction
    END AS prediction_error
FROM fact;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('008_checkpoint4_resolution')
ON CONFLICT (version) DO NOTHING;