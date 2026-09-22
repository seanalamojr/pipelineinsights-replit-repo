-- Checkpoint 11: preserve provider odds identity and make snapshot loads safe.

ALTER TABLE odds
    ADD COLUMN IF NOT EXISTS provider_odds_id TEXT;

DROP INDEX IF EXISTS odds_market_dedupe_idx;
DROP INDEX IF EXISTS odds_snapshot_dedupe_idx;

ALTER TABLE odds
    DROP CONSTRAINT IF EXISTS odds_snapshot_uq,
    ADD CONSTRAINT odds_snapshot_uq
        UNIQUE (match_id, player_id, book, prop_type, line, captured_at);

CREATE UNIQUE INDEX IF NOT EXISTS odds_provider_snapshot_uq
    ON odds (provider, provider_event_id, provider_odds_id)
    WHERE provider_odds_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS odds_unresolved_names (
    provider TEXT NOT NULL,
    provider_player_name TEXT NOT NULL,
    league TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count > 0),
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (provider, provider_player_name, league)
);

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('014_checkpoint11_odds_identity')
ON CONFLICT (version) DO NOTHING;