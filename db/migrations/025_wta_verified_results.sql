-- Official WTA result provenance and an odds-anchored report. The existing
-- prediction-anchored reporting view cannot expose odds without predictions.
CREATE TABLE IF NOT EXISTS wta_match_sources (
    match_id TEXT PRIMARY KEY,
    source_url TEXT NOT NULL,
    final_score TEXT NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE VIEW vw_wta_odds_results AS
SELECT
    o.odds_id, o.provider, o.provider_event_id, o.provider_event_start_at,
    o.provider_player_id, o.provider_player_name, o.captured_at,
    o.book, o.prop_type, o.line, o.over_price, o.under_price,
    o.match_id, o.player_id, p.full_name AS player, m.event_date,
    opponent.full_name AS opponent, m.tournament, m.is_winner,
    source.final_score, source.source_url,
    CASE o.prop_type
        WHEN 'aces' THEN m.aces
        WHEN 'double_faults' THEN m.double_faults
        WHEN 'games_won' THEN m.games_won
        WHEN 'sets_won' THEN m.sets_won
        WHEN 'service_games' THEN m.service_games
        WHEN 'break_points_won' THEN m.break_points_won
        ELSE NULL
    END AS actual_value
FROM odds o
JOIN matches m ON m.match_id = o.match_id AND m.player_id = o.player_id
JOIN players p ON p.player_id = o.player_id AND p.tour = 'WTA'
JOIN players opponent ON opponent.player_id = m.opponent_id
JOIN wta_match_sources source ON source.match_id = m.match_id;

INSERT INTO pipelineinsights_schema_migrations (version)
VALUES ('025_wta_verified_results')
ON CONFLICT (version) DO NOTHING;