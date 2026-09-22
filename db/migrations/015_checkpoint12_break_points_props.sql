-- Checkpoint 12: register the real tennis Break Points Won market.

INSERT INTO prop_types (prop_key, sport, display_label)
VALUES ('break_points_won', 'tennis', 'Break Points Won')
ON CONFLICT (prop_key) DO UPDATE SET
    sport = EXCLUDED.sport,
    display_label = EXCLUDED.display_label;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('015_checkpoint12_break_points_props')
ON CONFLICT (version) DO NOTHING;