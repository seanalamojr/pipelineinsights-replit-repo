-- Keep the development schema compatible with the legacy production snapshot.
--
-- Publish applies the development-to-production schema diff, not these
-- historical migration files. These changes make that diff additive and
-- non-destructive for the existing production rows:
--   * legacy matches may not have tourney_date yet;
--   * legacy feature rows may not have stat_target yet;
--   * feature targets require a unique key, but not a primary key that would
--     force stat_target to be NOT NULL before legacy rows are backfilled;
--   * production already uses this odds unique index name.

ALTER TABLE matches
    ALTER COLUMN tourney_date DROP NOT NULL;

ALTER TABLE player_game_features
    DROP CONSTRAINT IF EXISTS player_game_features_pkey;

ALTER TABLE player_game_features
    ALTER COLUMN stat_target DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS player_game_features_key_uq
    ON player_game_features (player_id, match_id, stat_target, feature_version);

ALTER TABLE odds
    DROP CONSTRAINT IF EXISTS odds_snapshot_uq;

CREATE UNIQUE INDEX IF NOT EXISTS odds_snapshot_dedupe_idx
    ON odds (match_id, player_id, book, prop_type, line, captured_at);

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('020_publish_schema_compatibility')
ON CONFLICT (version) DO NOTHING;