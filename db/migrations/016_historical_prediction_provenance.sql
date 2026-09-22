-- Checkpoint 14: provenance for persisted walk-forward predictions.
--
-- Live predictions keep these fields NULL. Historical rows must carry the
-- complete fold boundary so they can be audited without changing live keys.
ALTER TABLE player_prop_predictions
    ADD COLUMN IF NOT EXISTS fold_number INTEGER,
    ADD COLUMN IF NOT EXISTS fold_cutoff_date DATE,
    ADD COLUMN IF NOT EXISTS fold_test_end_date DATE;

ALTER TABLE player_prop_predictions
    DROP CONSTRAINT IF EXISTS player_prop_predictions_fold_provenance_ck;

ALTER TABLE player_prop_predictions
    ADD CONSTRAINT player_prop_predictions_fold_provenance_ck
    CHECK (
        (
            fold_number IS NULL
            AND fold_cutoff_date IS NULL
            AND fold_test_end_date IS NULL
        )
        OR (
            fold_number > 0
            AND fold_cutoff_date IS NOT NULL
            AND fold_test_end_date IS NOT NULL
            AND fold_cutoff_date < fold_test_end_date
        )
    );

CREATE INDEX IF NOT EXISTS player_prop_predictions_fold_lookup_idx
    ON player_prop_predictions (
        sport,
        prop_type,
        modelversion,
        fold_number,
        fold_cutoff_date
    );

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('016_historical_prediction_provenance')
ON CONFLICT (version) DO NOTHING;