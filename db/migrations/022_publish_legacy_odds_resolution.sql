-- Legacy production odds rows already have player_id populated, but the
-- newly introduced resolved_at column will be NULL when Publish adds it.
-- Avoid adding a check that rejects those existing rows.

ALTER TABLE odds
    DROP CONSTRAINT IF EXISTS odds_resolution_ck;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('022_publish_legacy_odds_resolution')
ON CONFLICT (version) DO NOTHING;