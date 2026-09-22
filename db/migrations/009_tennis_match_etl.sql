-- Checkpoint 4: real Sackmann match facts.
--
-- The existing matches table already stores one player per match. These
-- additions preserve the source context and the derived per-player service
-- statistics needed by the first real ETL pass.

ALTER TABLE players
    ADD COLUMN IF NOT EXISTS height_cm INTEGER,
    ADD COLUMN IF NOT EXISTS rank_position INTEGER,
    ADD COLUMN IF NOT EXISTS rank_points INTEGER,
    ADD COLUMN IF NOT EXISTS profile_as_of DATE;

ALTER TABLE matches
    ADD COLUMN IF NOT EXISTS tourney_date DATE,
    ADD COLUMN IF NOT EXISTS draw_size INTEGER,
    ADD COLUMN IF NOT EXISTS tourney_level TEXT,
    ADD COLUMN IF NOT EXISTS match_num INTEGER,
    ADD COLUMN IF NOT EXISTS best_of INTEGER,
    ADD COLUMN IF NOT EXISTS score TEXT,
    ADD COLUMN IF NOT EXISTS match_completed BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS player_seed INTEGER,
    ADD COLUMN IF NOT EXISTS player_entry TEXT,
    ADD COLUMN IF NOT EXISTS opponent_seed INTEGER,
    ADD COLUMN IF NOT EXISTS opponent_entry TEXT,
    ADD COLUMN IF NOT EXISTS player_rank INTEGER,
    ADD COLUMN IF NOT EXISTS opponent_rank INTEGER,
    ADD COLUMN IF NOT EXISTS player_rank_points INTEGER,
    ADD COLUMN IF NOT EXISTS opponent_rank_points INTEGER,
    ADD COLUMN IF NOT EXISTS player_age NUMERIC(8, 4),
    ADD COLUMN IF NOT EXISTS serve_points INTEGER,
    ADD COLUMN IF NOT EXISTS first_serves_in INTEGER,
    ADD COLUMN IF NOT EXISTS first_serves_won INTEGER,
    ADD COLUMN IF NOT EXISTS second_serves_won INTEGER,
    ADD COLUMN IF NOT EXISTS bp_saved INTEGER,
    ADD COLUMN IF NOT EXISTS bp_faced INTEGER,
    ADD COLUMN IF NOT EXISTS break_points_won INTEGER;

UPDATE matches
SET tourney_date = event_date
WHERE tourney_date IS NULL;

ALTER TABLE matches
    ALTER COLUMN tourney_date SET NOT NULL;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('009_tennis_match_etl')
ON CONFLICT (version) DO NOTHING;