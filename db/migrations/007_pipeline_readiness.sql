-- Checkpoint 4 readiness:
-- 1. Odds may arrive before the completed-match feed.
-- 2. Features are keyed by stat target and feature version.
-- 3. Prop types are stable snake_case keys with display labels.
-- 4. The reporting view exposes observed outcomes without dashboard logic.

CREATE TABLE IF NOT EXISTS prop_types (
    prop_key TEXT PRIMARY KEY,
    sport TEXT NOT NULL,
    display_label TEXT NOT NULL,
    CONSTRAINT prop_types_key_format_ck
        CHECK (prop_key ~ '^[a-z][a-z0-9_]*$')
);

INSERT INTO prop_types (prop_key, sport, display_label)
VALUES
    ('aces', 'tennis', 'Aces'),
    ('double_faults', 'tennis', 'Double Faults'),
    ('sets_won', 'tennis', 'Sets Won'),
    ('service_games', 'tennis', 'Service Games'),
    ('games_won', 'tennis', 'Games Won')
ON CONFLICT (prop_key) DO UPDATE SET
    sport = EXCLUDED.sport,
    display_label = EXCLUDED.display_label;

ALTER TABLE odds
    ADD COLUMN IF NOT EXISTS provider TEXT NOT NULL DEFAULT 'demo',
    ADD COLUMN IF NOT EXISTS provider_event_id TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS provider_market_id TEXT;

ALTER TABLE odds
    ALTER COLUMN match_id DROP NOT NULL;

ALTER TABLE matches
    ALTER COLUMN is_winner DROP NOT NULL;

UPDATE odds
SET prop_type = CASE lower(prop_type)
    WHEN 'games won' THEN 'games_won'
    WHEN 'aces' THEN 'aces'
    WHEN 'double faults' THEN 'double_faults'
    WHEN 'sets won' THEN 'sets_won'
    WHEN 'service games' THEN 'service_games'
    ELSE prop_type
END;

UPDATE player_prop_predictions
SET prop_type = CASE lower(prop_type)
    WHEN 'games won' THEN 'games_won'
    WHEN 'aces' THEN 'aces'
    WHEN 'double faults' THEN 'double_faults'
    WHEN 'sets won' THEN 'sets_won'
    WHEN 'service games' THEN 'service_games'
    ELSE prop_type
END;

UPDATE odds
SET provider_event_id = match_id
WHERE provider = 'demo'
  AND provider_event_id = '';

UPDATE player_prop_predictions
SET modelversion = regexp_replace(modelversion, '_games$', '_games_won')
WHERE prop_type = 'games_won'
  AND modelversion ~ '_games$';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'odds_player_fk'
    ) THEN
        ALTER TABLE odds
            ADD CONSTRAINT odds_player_fk
            FOREIGN KEY (player_id) REFERENCES players (player_id);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'odds_prop_type_fk'
    ) THEN
        ALTER TABLE odds
            ADD CONSTRAINT odds_prop_type_fk
            FOREIGN KEY (prop_type) REFERENCES prop_types (prop_key);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'player_prop_predictions_prop_type_fk'
    ) THEN
        ALTER TABLE player_prop_predictions
            ADD CONSTRAINT player_prop_predictions_prop_type_fk
            FOREIGN KEY (prop_type) REFERENCES prop_types (prop_key);
    END IF;
END $$;

DROP INDEX IF EXISTS odds_snapshot_dedupe_idx;

CREATE UNIQUE INDEX IF NOT EXISTS odds_snapshot_dedupe_idx
    ON odds (
        provider,
        provider_event_id,
        player_id,
        book,
        prop_type,
        line,
        captured_at
    );

ALTER TABLE player_game_features
    ADD COLUMN IF NOT EXISTS stat_target TEXT;

UPDATE player_game_features
SET stat_target = 'aces'
WHERE stat_target IS NULL;

ALTER TABLE player_game_features
    ALTER COLUMN stat_target SET NOT NULL;

ALTER TABLE player_game_features
    DROP CONSTRAINT IF EXISTS player_game_features_pkey;

ALTER TABLE player_game_features
    ADD CONSTRAINT player_game_features_pkey
    PRIMARY KEY (player_id, match_id, stat_target, feature_version);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'player_game_features_stat_target_fk'
    ) THEN
        ALTER TABLE player_game_features
            ADD CONSTRAINT player_game_features_stat_target_fk
            FOREIGN KEY (stat_target) REFERENCES prop_types (prop_key);
    END IF;
END $$;

-- Preserve the existing demo's secondary Games Won feature without relying on
-- JSONB as the model input boundary. Real feature jobs write typed rows directly.
INSERT INTO player_game_features (
    player_id,
    match_id,
    event_date,
    sport,
    feature_version,
    stat_target,
    rolling_mean_3,
    rolling_std_3,
    rolling_mean_5,
    rolling_std_5,
    rolling_mean_10,
    rolling_std_10,
    surface_rolling_mean,
    surface_rolling_std,
    head_to_head_average,
    rest_days,
    opponent_strength,
    feature_values,
    target_values
)
SELECT
    player_id,
    match_id,
    event_date,
    sport,
    feature_version,
    'games_won',
    COALESCE(
        NULLIF(feature_values -> 'rolling_mean_5' ->> 'Games Won', '')::numeric,
        rolling_mean_5
    ),
    rolling_std_3,
    COALESCE(
        NULLIF(feature_values -> 'rolling_mean_5' ->> 'Games Won', '')::numeric,
        rolling_mean_5
    ),
    rolling_std_5,
    COALESCE(
        NULLIF(feature_values -> 'rolling_mean_5' ->> 'Games Won', '')::numeric,
        rolling_mean_5
    ),
    rolling_std_10,
    COALESCE(
        NULLIF(feature_values -> 'rolling_mean_5' ->> 'Games Won', '')::numeric,
        surface_rolling_mean
    ),
    surface_rolling_std,
    head_to_head_average,
    rest_days,
    opponent_strength,
    '{}'::JSONB,
    target_values
FROM player_game_features
WHERE stat_target = 'aces'
  AND (
      feature_values -> 'rolling_mean_5' ? 'Games Won'
      OR target_values ? 'Games Won'
  )
ON CONFLICT (player_id, match_id, stat_target, feature_version)
DO NOTHING;

CREATE INDEX IF NOT EXISTS player_game_features_stat_lookup_idx
    ON player_game_features (sport, stat_target, feature_version, event_date);

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
        CASE prop.prop_key
            WHEN 'games_won' THEN match_row.games_won::numeric
            WHEN 'sets_won' THEN match_row.sets_won::numeric
            WHEN 'aces' THEN match_row.aces::numeric
            WHEN 'double_faults' THEN match_row.double_faults::numeric
            WHEN 'minutes' THEN match_row.minutes::numeric
            ELSE NULL
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
VALUES ('007_pipeline_readiness')
ON CONFLICT (version) DO NOTHING;