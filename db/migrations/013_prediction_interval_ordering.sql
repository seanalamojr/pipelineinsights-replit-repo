-- Checkpoint 9 hardening: repair legacy negative lower bounds before adding
-- invariants that prevent invalid intervals from reaching the reporting view.

UPDATE player_prop_predictions
SET lowerci = 0
WHERE lowerci < 0;

ALTER TABLE player_prop_predictions
    ADD CONSTRAINT prediction_interval_ordered
    CHECK (
        (lowerci IS NULL OR lowerci >= 0)
        AND (
            lowerci IS NULL
            OR upperci IS NULL
            OR (
                lowerci <= upperci
                AND (prediction IS NULL OR lowerci <= prediction)
                AND (prediction IS NULL OR prediction <= upperci)
            )
        )
    );

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('013_prediction_interval_ordering')
ON CONFLICT (version) DO NOTHING;