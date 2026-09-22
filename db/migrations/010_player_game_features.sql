-- Checkpoint 5: typed, leakage-safe model inputs.
--
-- Dynamic feature selection remains config-driven. These columns make the
-- approved tennis_v1 inputs directly queryable while feature_values retains an
-- auditable copy of the exact configured feature vector.

ALTER TABLE player_game_features
    ADD COLUMN IF NOT EXISTS rolling_mean_20 NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS rolling_std_20 NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS surface_rolling_n_observations INTEGER,
    ADD COLUMN IF NOT EXISTS rolling_aces_per_service_game NUMERIC(12, 6),
    ADD COLUMN IF NOT EXISTS rolling_first_serve_in_pct NUMERIC(12, 6),
    ADD COLUMN IF NOT EXISTS career_to_date_mean NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS history_observations INTEGER,
    ADD COLUMN IF NOT EXISTS head_to_head_matches INTEGER,
    ADD COLUMN IF NOT EXISTS head_to_head_win_rate NUMERIC(12, 6),
    ADD COLUMN IF NOT EXISTS opponent_aces_conceded_rate NUMERIC(12, 6),
    ADD COLUMN IF NOT EXISTS best_of INTEGER,
    ADD COLUMN IF NOT EXISTS surface TEXT,
    ADD COLUMN IF NOT EXISTS tourney_level TEXT,
    ADD COLUMN IF NOT EXISTS player_rank INTEGER,
    ADD COLUMN IF NOT EXISTS opponent_rank INTEGER,
    ADD COLUMN IF NOT EXISTS rank_difference INTEGER,
    ADD COLUMN IF NOT EXISTS player_height_cm INTEGER,
    ADD COLUMN IF NOT EXISTS target_value NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS has_sufficient_history BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_training_eligible BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS player_game_features_training_idx
    ON player_game_features (
        sport,
        stat_target,
        feature_version,
        is_training_eligible,
        event_date
    );

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('010_player_game_features')
ON CONFLICT (version) DO NOTHING;