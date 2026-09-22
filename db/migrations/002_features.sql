-- Feature rows are the only model input boundary.
-- All feature values must be computed from dates before the current event_date.

CREATE TABLE IF NOT EXISTS player_game_features (
    player_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    event_date DATE NOT NULL,
    sport TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    rolling_mean_3 NUMERIC(12, 4),
    rolling_std_3 NUMERIC(12, 4),
    rolling_mean_5 NUMERIC(12, 4),
    rolling_std_5 NUMERIC(12, 4),
    rolling_mean_10 NUMERIC(12, 4),
    rolling_std_10 NUMERIC(12, 4),
    surface_rolling_mean NUMERIC(12, 4),
    surface_rolling_std NUMERIC(12, 4),
    head_to_head_average NUMERIC(12, 4),
    rest_days NUMERIC(12, 4),
    opponent_strength NUMERIC(12, 4),
    feature_values JSONB NOT NULL DEFAULT '{}'::JSONB,
    target_values JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, match_id),
    CONSTRAINT player_game_features_match_fk
        FOREIGN KEY (match_id, player_id)
        REFERENCES matches (match_id, player_id)
);

CREATE INDEX IF NOT EXISTS player_game_features_event_date_idx
    ON player_game_features (event_date);
CREATE INDEX IF NOT EXISTS player_game_features_sport_prop_idx
    ON player_game_features (sport, feature_version);

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('002_features')
ON CONFLICT (version) DO NOTHING;