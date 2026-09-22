-- Preserve the provider's player identity separately from internal player_id.

ALTER TABLE odds
    ADD COLUMN IF NOT EXISTS provider_player_id TEXT;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('017_odds_provider_player_identity')
ON CONFLICT (version) DO NOTHING;