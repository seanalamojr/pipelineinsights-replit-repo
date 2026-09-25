-- Preserve the provider's scheduled event time even when the player or fixture
-- cannot yet be resolved to an internal match.
ALTER TABLE odds
    ADD COLUMN IF NOT EXISTS provider_event_start_at TIMESTAMPTZ;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('024_odds_provider_event_start')
ON CONFLICT (version) DO NOTHING;