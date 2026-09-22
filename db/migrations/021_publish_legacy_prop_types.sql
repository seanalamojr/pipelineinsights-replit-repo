-- Legacy production snapshots store human-readable prop_type values such as
-- "Aces" and "Games Won", while the normalized reference table uses keys such
-- as "aces" and "games_won". Do not add foreign keys that reject those
-- existing production rows during Publish.

ALTER TABLE odds
    DROP CONSTRAINT IF EXISTS odds_prop_type_fk;

ALTER TABLE player_prop_predictions
    DROP CONSTRAINT IF EXISTS player_prop_predictions_prop_type_fk;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('021_publish_legacy_prop_types')
ON CONFLICT (version) DO NOTHING;