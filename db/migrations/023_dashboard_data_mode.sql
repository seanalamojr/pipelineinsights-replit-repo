-- Add a stable real/demo selector to the reporting view without changing
-- existing columns or the LEFT JOIN that preserves predictions without odds.
CREATE OR REPLACE VIEW vw_fact_player_prop_odds AS
WITH latest_features AS (
    SELECT DISTINCT ON (match_id, player_id, stat_target)
        match_id,
        player_id,
        stat_target,
        feature_version,
        rolling_mean_5 AS rolling_average
    FROM player_game_features
    ORDER BY
        match_id,
        player_id,
        stat_target,
        created_at DESC,
        feature_version DESC
),
latest_injuries AS (
    SELECT DISTINCT ON (player_id, event_date)
        player_id,
        event_date,
        status
    FROM injuries
    ORDER BY
        player_id,
        event_date,
        captured_at DESC,
        injury_id DESC
),
fact AS (
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
        feature.rolling_average,
        LEFT(player.player_id, 5) = 'demo_' AS is_demo,
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
    LEFT JOIN latest_features AS feature
        ON feature.match_id = prediction.match_id
       AND feature.player_id = prediction.player_id
       AND feature.stat_target = prediction.prop_type
    LEFT JOIN odds AS market
        ON market.match_id = prediction.match_id
       AND market.player_id = prediction.player_id
       AND market.prop_type = prediction.prop_type
    LEFT JOIN latest_injuries AS injury
        ON injury.player_id = prediction.player_id
       AND injury.event_date = match_row.event_date
)
SELECT
    fact.*,
    CASE
        WHEN fact.actual_value IS NULL THEN NULL
        ELSE fact.actual_value - fact.prediction
    END AS prediction_error,
    CASE
        WHEN fact.actual_value IS NULL THEN NULL
        ELSE fact.prediction - fact.actual_value
    END AS signed_error,
    CASE
        WHEN fact.is_demo THEN 'demo'
        ELSE 'real'
    END AS data_mode
FROM fact;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('023_dashboard_data_mode')
ON CONFLICT (version) DO NOTHING;