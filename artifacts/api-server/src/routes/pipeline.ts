import { Router, type IRouter, type Request } from "express";
import { pool } from "@workspace/db";
import {
  GetPipelineModelVersionsResponse,
  GetPipelineBacktestResponse,
  GetPipelineOverviewResponse,
  GetPipelinePredictionsResponse,
  GetPlayerTrendResponse,
} from "@workspace/api-zod";
import { readValueEdgeThreshold } from "../lib/tennis-config";

const router: IRouter = Router();
let supportedPropTypes = new Set<string>();
let backtestCache: { expiresAt: number; value: unknown } | null = null;

export async function initializePipelineRoutes() {
  const result = await pool.query<{ prop_key: string }>(
    `
      SELECT prop_key
      FROM prop_types
      UNION
      SELECT DISTINCT prop_type AS prop_key
      FROM player_prop_predictions
      ORDER BY prop_key
    `,
  );
  supportedPropTypes = new Set(
    result.rows.map((row) => row.prop_key.toLowerCase()),
  );
  try {
    await refreshBacktestCache();
  } catch {
    // Keep startup resilient if no scored backtest exists yet.
    backtestCache = null;
  }
}

type QueryValue = string | undefined;

function queryString(request: Request, name: string): QueryValue {
  const value = request.query[name];
  return typeof value === "string" ? value : undefined;
}

function nullableNumber(value: unknown): number | null {
  return value === null || value === undefined ? null : Number(value);
}

async function refreshBacktestCache() {
  const result = await pool.query(`
    WITH latest_run AS (
      SELECT MAX(predictiontimestamp) AS run_timestamp
      FROM player_prop_predictions
      WHERE modelversion LIKE '%_backtest_%'
    ),
    scored AS (
      SELECT
        prediction.prediction_id,
        prediction.modelversion,
        prediction.sport,
        prediction.prop_type,
        COALESCE(
          prop.display_label,
          initcap(replace(prediction.prop_type, '_', ' '))
        ) AS prop_label,
        prediction.prediction,
        prediction.lowerci,
        prediction.upperci,
        prediction.fold_number,
        prediction.fold_cutoff_date,
        prediction.fold_test_end_date,
        CASE prediction.prop_type
          WHEN 'games_won' THEN match_row.games_won::numeric
          WHEN 'sets_won' THEN match_row.sets_won::numeric
          WHEN 'aces' THEN match_row.aces::numeric
          WHEN 'double_faults' THEN match_row.double_faults::numeric
          WHEN 'service_games' THEN match_row.service_games::numeric
          ELSE NULL
        END AS actual_value,
        prediction.prediction - CASE prediction.prop_type
          WHEN 'games_won' THEN match_row.games_won::numeric
          WHEN 'sets_won' THEN match_row.sets_won::numeric
          WHEN 'aces' THEN match_row.aces::numeric
          WHEN 'double_faults' THEN match_row.double_faults::numeric
          WHEN 'service_games' THEN match_row.service_games::numeric
          ELSE NULL
        END AS signed_error
      FROM player_prop_predictions AS prediction
      JOIN matches AS match_row
        ON match_row.match_id = prediction.match_id
       AND match_row.player_id = prediction.player_id
      LEFT JOIN prop_types AS prop
        ON prop.prop_key = prediction.prop_type
      WHERE prediction.predictiontimestamp = (SELECT run_timestamp FROM latest_run)
        AND prediction.modelversion LIKE '%_backtest_%'
        AND LEFT(prediction.player_id, 5) <> 'demo_'
    ),
    model_metrics AS (
      SELECT
        modelversion,
        sport,
        prop_type,
        MAX(prop_label) AS prop_label,
        COUNT(*)::integer AS scored_rows,
        COUNT(*) FILTER (
          WHERE lowerci IS NOT NULL AND upperci IS NOT NULL
        )::integer AS interval_scored_rows,
        COUNT(DISTINCT fold_number) FILTER (
          WHERE fold_number > 0
        )::integer AS fold_count,
        MIN(fold_cutoff_date) FILTER (
          WHERE fold_number > 0
        ) AS first_cutoff,
        MAX(fold_test_end_date) FILTER (
          WHERE fold_number > 0
        ) AS last_test_end,
        AVG(ABS(signed_error)) AS mae,
        SQRT(AVG(signed_error * signed_error)) AS rmse,
        AVG(signed_error) AS mean_bias,
        AVG(
          CASE
            WHEN lowerci IS NOT NULL
              AND upperci IS NOT NULL
              AND actual_value BETWEEN lowerci AND upperci THEN 1.0
            WHEN lowerci IS NOT NULL AND upperci IS NOT NULL THEN 0.0
            ELSE 0.0
          END
        ) FILTER (WHERE lowerci IS NOT NULL AND upperci IS NOT NULL) AS interval_coverage
      FROM scored
      WHERE actual_value IS NOT NULL
      GROUP BY modelversion, sport, prop_type
    ),
    family_metrics AS (
      SELECT
        model_metrics.*,
        CASE
          WHEN modelversion LIKE 'baseline_v1_%' THEN 'baseline'
          WHEN modelversion LIKE 'gbm_v1_%' THEN 'GBM'
          WHEN modelversion LIKE 'ensemble_v1_%' THEN 'ensemble'
          ELSE modelversion
        END AS model_family
      FROM model_metrics
    ),
    baseline_metrics AS (
      SELECT sport, prop_type, mae AS baseline_mae
      FROM family_metrics
      WHERE model_family = 'baseline'
    ),
    diagnostic_metrics AS (
      SELECT
        modelversion,
        sport,
        stat_target,
        MAX(metric_value) FILTER (
          WHERE fold_number = 0 AND metric = 'interval_crossing_count'
        ) AS interval_crossing_count,
        MAX(metric_value) FILTER (
          WHERE fold_number = 0 AND metric = 'interval_repair_count'
        ) AS interval_repair_count
      FROM model_backtest_results
      WHERE run_timestamp = (SELECT run_timestamp FROM latest_run)
      GROUP BY modelversion, sport, stat_target
    )
    SELECT
      family_metrics.modelversion,
      family_metrics.sport,
      family_metrics.prop_type,
      family_metrics.prop_label,
      family_metrics.scored_rows,
      family_metrics.interval_scored_rows,
      family_metrics.mae,
      family_metrics.rmse,
      family_metrics.mean_bias,
      family_metrics.interval_coverage,
      CASE
        WHEN family_metrics.model_family = 'baseline' THEN 0.0
        ELSE (
          (baseline_metrics.baseline_mae - family_metrics.mae)
          / NULLIF(baseline_metrics.baseline_mae, 0)
        ) * 100.0
      END AS mae_improvement_over_baseline,
      family_metrics.model_family,
      latest_run.run_timestamp,
      family_metrics.fold_count,
      family_metrics.first_cutoff,
      family_metrics.last_test_end,
      diagnostic_metrics.interval_crossing_count,
      diagnostic_metrics.interval_repair_count
    FROM family_metrics
    CROSS JOIN latest_run
    LEFT JOIN baseline_metrics
      ON baseline_metrics.sport = family_metrics.sport
     AND baseline_metrics.prop_type = family_metrics.prop_type
    LEFT JOIN diagnostic_metrics
      ON diagnostic_metrics.modelversion =
        split_part(family_metrics.modelversion, '_backtest_', 1)
     AND diagnostic_metrics.sport = family_metrics.sport
     AND diagnostic_metrics.stat_target = family_metrics.prop_type
    ORDER BY family_metrics.prop_type, family_metrics.model_family, family_metrics.modelversion;
  `);

  const payload = GetPipelineBacktestResponse.parse({
    available: result.rows.length > 0,
    runTimestamp: result.rows[0]?.run_timestamp ?? null,
    models: result.rows.map((row) => ({
      modelVersion: String(row.modelversion),
      modelFamily: String(row.model_family),
      sport: String(row.sport),
      statTarget: String(row.prop_type),
      propLabel: String(row.prop_label ?? row.prop_type),
      scoredRows: Number(row.scored_rows ?? 0),
      intervalScoredRows: Number(row.interval_scored_rows ?? 0),
      foldCount: Number(row.fold_count ?? 0),
      mae: nullableNumber(row.mae),
      rmse: nullableNumber(row.rmse),
      meanBias: nullableNumber(row.mean_bias),
      intervalCoverage: nullableNumber(row.interval_coverage),
      maeImprovementOverBaseline: nullableNumber(
        row.mae_improvement_over_baseline,
      ),
      intervalCrossingCount: nullableNumber(row.interval_crossing_count),
      intervalRepairCount: nullableNumber(row.interval_repair_count),
      firstCutoff: row.first_cutoff,
      lastTestEnd: row.last_test_end,
    })),
  });
  backtestCache = {
    expiresAt: Date.now() + 300_000,
    value: payload,
  };
  return payload;
}

function toPropRow(row: Record<string, unknown>) {
  return {
    player: String(row.player),
    playerId: row.player_id ? String(row.player_id) : undefined,
    tour: String(row.tour ?? "—"),
    sport: String(row.sport),
    eventDate: row.event_date,
    matchup: String(row.matchup ?? "Matchup pending"),
    propType: String(row.prop_type),
    propLabel: String(row.prop_label ?? row.prop_type),
    line: nullableNumber(row.line),
    projection: Number(row.projection),
    lowerCi: Number(row.lowerci),
    upperCi: Number(row.upperci),
    edge: nullableNumber(row.edge),
    normalizedEdge: nullableNumber(row.normalized_edge),
    side:
      row.side === null || row.side === undefined
        ? null
        : row.side === "Under"
          ? "Under"
          : "Over",
    book: row.book === null || row.book === undefined ? null : String(row.book),
    modelVersion: String(row.modelversion),
    predictionTimestamp: row.predictiontimestamp,
    status: row.status ? String(row.status) : null,
    tournament: row.tournament ? String(row.tournament) : undefined,
    surface: row.surface ? String(row.surface) : undefined,
    overPrice: row.over_price ? Number(row.over_price) : undefined,
    underPrice: row.under_price ? Number(row.under_price) : undefined,
    actualValue: nullableNumber(row.actual_value),
    predictionError: nullableNumber(row.prediction_error),
    featureVersion:
      row.feature_version === null || row.feature_version === undefined
        ? null
        : String(row.feature_version),
    isDemo: Boolean(row.is_demo),
  };
}

const reportingProjection = `
  SELECT
    player,
    player_id,
    tour,
    sport,
    event_date,
    matchup,
    prop_type,
    prop_label,
    line,
    prediction AS projection,
    lowerci,
    upperci,
    edge,
    normalized_edge,
    side,
    book,
    modelversion,
    predictiontimestamp,
    status,
    tournament,
    surface,
    over_price,
    under_price
    ,actual_value
    ,prediction_error
    ,feature_version
    ,is_demo
  FROM reporting
`;

const reportingCtes = `
  WITH latest_features AS (
    SELECT DISTINCT ON (match_id, player_id, stat_target)
      match_id,
      player_id,
      stat_target,
      feature_version,
      rolling_mean_5 AS rolling_average
    FROM player_game_features
    ORDER BY
      match_id,
      player_id,
      stat_target,
      created_at DESC,
      feature_version DESC
  ),
  latest_injuries AS (
    SELECT DISTINCT ON (player_id, event_date)
      player_id,
      event_date,
      status
    FROM injuries
    ORDER BY
      player_id,
      event_date,
      captured_at DESC,
      injury_id DESC
  ),
  reporting_base AS (
    SELECT
      prediction.prediction_id,
      prediction.player_id,
      player.full_name AS player,
      player.tour,
      prediction.match_id,
      match_row.event_date,
      match_row.tournament,
      match_row.surface,
      prediction.sport,
      prediction.prop_type,
      COALESCE(
        prop.display_label,
        initcap(replace(prediction.prop_type, '_', ' '))
      ) AS prop_label,
      prediction.prediction,
      prediction.lowerci,
      prediction.upperci,
      prediction.modelversion,
      prediction.predictiontimestamp,
      market.provider,
      market.provider_event_id,
      market.provider_market_id,
      market.book,
      market.line,
      market.over_price,
      market.under_price,
      market.captured_at,
      CASE
        WHEN market.line IS NULL THEN NULL
        ELSE prediction.prediction - market.line
      END AS edge,
      CASE
        WHEN market.line IS NULL THEN NULL
        ELSE (prediction.prediction - market.line)
          / NULLIF(prediction.upperci - prediction.lowerci, 0)
      END AS normalized_edge,
      CASE
        WHEN market.line IS NULL THEN NULL
        WHEN prediction.prediction >= market.line THEN 'Over'
        ELSE 'Under'
      END AS side,
      opponent.full_name AS opponent,
      player.full_name || ' vs ' ||
        COALESCE(opponent.full_name, 'TBD') AS matchup,
      injury.status,
      feature.feature_version,
      feature.rolling_average,
      LEFT(player.player_id, 5) = 'demo_' AS is_demo,
      CASE
        WHEN match_row.event_date > CURRENT_DATE THEN NULL
        ELSE CASE prediction.prop_type
          WHEN 'games_won' THEN match_row.games_won::numeric
          WHEN 'sets_won' THEN match_row.sets_won::numeric
          WHEN 'aces' THEN match_row.aces::numeric
          WHEN 'double_faults' THEN match_row.double_faults::numeric
          WHEN 'service_games' THEN match_row.service_games::numeric
          ELSE NULL
        END
      END AS actual_value
    FROM player_prop_predictions AS prediction
    JOIN players AS player
      ON player.player_id = prediction.player_id
    JOIN matches AS match_row
      ON match_row.match_id = prediction.match_id
     AND match_row.player_id = prediction.player_id
    LEFT JOIN prop_types AS prop
      ON prop.prop_key = prediction.prop_type
    LEFT JOIN players AS opponent
      ON opponent.player_id = match_row.opponent_id
    LEFT JOIN latest_features AS feature
      ON feature.match_id = prediction.match_id
     AND feature.player_id = prediction.player_id
     AND feature.stat_target = prediction.prop_type
    LEFT JOIN odds AS market
      ON market.match_id = prediction.match_id
     AND market.player_id = prediction.player_id
     AND market.prop_type = prediction.prop_type
    LEFT JOIN latest_injuries AS injury
      ON injury.player_id = prediction.player_id
     AND injury.event_date = match_row.event_date
  ),
  reporting AS (
    SELECT
      reporting_base.*,
      CASE
        WHEN actual_value IS NULL THEN NULL
        ELSE actual_value - prediction
      END AS prediction_error,
      CASE
        WHEN actual_value IS NULL THEN NULL
        ELSE prediction - actual_value
      END AS signed_error
    FROM reporting_base
  )
`;

router.get("/pipeline/overview", async (request, response) => {
  try {
    const valueEdgeThreshold = readValueEdgeThreshold();
    const [summary, edges, matches, featureCount] = await Promise.all([
      pool.query<{
        active_prop_markets: string;
        predictions_generated: string;
        value_edges_found: string;
        view_rows: string;
        demo_rows: string;
        match_rows: string;
        market_rows: string;
        latest_prediction_timestamp: string | null;
      }>(`
        ${reportingCtes}
        SELECT
          COUNT(DISTINCT (match_id, player_id, prop_type))::text AS active_prop_markets,
          COUNT(DISTINCT prediction_id)::text AS predictions_generated,
          COUNT(DISTINCT prediction_id) FILTER (WHERE ABS(normalized_edge) >= $1)::text AS value_edges_found,
          COUNT(*)::text AS view_rows,
          COUNT(*) FILTER (WHERE player_id LIKE 'demo_%')::text AS demo_rows,
          COUNT(DISTINCT match_id)::text AS match_rows,
          COUNT(DISTINCT (match_id, player_id, book, prop_type))::text AS market_rows,
          MAX(predictiontimestamp)::text AS latest_prediction_timestamp
        FROM reporting
      `, [valueEdgeThreshold]),
      pool.query(
        `${reportingCtes}
         ${reportingProjection}
         ORDER BY ABS(normalized_edge) DESC NULLS LAST
         LIMIT 8`,
      ),
      pool.query<{
        matchup: string;
        event_date: string;
        tournament: string;
        surface: string;
      }>(`
        ${reportingCtes}
        SELECT DISTINCT matchup, event_date, tournament, surface
        FROM reporting
        WHERE event_date = CURRENT_DATE
        ORDER BY matchup
      `),
      pool.query<{ feature_rows: string }>(
        "SELECT COUNT(*)::text AS feature_rows FROM player_game_features",
      ),
    ]);

    const summaryRow = summary.rows[0];
    const featureRows = featureCount.rows[0];
    const generatedAt = new Date().toISOString();
    const viewRows = Number(summaryRow?.view_rows ?? 0);
    const demoRows = Number(summaryRow?.demo_rows ?? 0);
    const demoData =
      process.env["DEMO_DATA"] === "true" ||
      demoRows > 0;
    const latestDataTimestamp =
      summaryRow?.latest_prediction_timestamp ?? generatedAt;
    const result = GetPipelineOverviewResponse.parse({
      demoData,
      generatedAt,
      activePropMarkets: {
        value: Number(summaryRow?.active_prop_markets ?? 0),
        delta: null,
      },
      predictionsGenerated: {
        value: Number(summaryRow?.predictions_generated ?? 0),
        delta: null,
      },
      avgRmse: {
        value: null,
        delta: null,
      },
      valueEdgesFound: {
        value: Number(summaryRow?.value_edges_found ?? 0),
        delta: null,
      },
      modelAgreement: {
        value: null,
        delta: null,
      },
      topEdges: edges.rows.map(toPropRow),
      todaysMatches: matches.rows.map((row) => ({
        matchup: row.matchup,
        eventDate: row.event_date,
        tournament: row.tournament,
        surface: row.surface,
      })),
      sources: [
        {
          name: "Match data",
          lastRun: latestDataTimestamp,
          recordCount: Number(summaryRow?.match_rows ?? 0),
          freshness: demoData ? "Demo snapshot" : "Reporting view",
          status: "ready",
        },
        {
          name: "Market odds",
          lastRun: latestDataTimestamp,
          recordCount: Number(summaryRow?.market_rows ?? 0),
          freshness: demoData ? "Demo snapshot" : "Reporting view",
          status: "ready",
        },
        {
          name: "Feature builder",
          lastRun: latestDataTimestamp,
          recordCount: Number(featureRows?.feature_rows ?? 0),
          freshness: demoData ? "Demo snapshot" : "Reporting view",
          status: "ready",
        },
      ],
    });
    response.json(result);
  } catch (error) {
    request.log.error({ err: error }, "Pipeline overview request failed");
    response.status(500).json({ message: "Unable to load pipeline overview." });
  }
});

router.get("/pipeline/predictions", async (request, response) => {
  try {
    const modelVersion = queryString(request, "modelVersion") ?? null;
    const propType = queryString(request, "propType")?.toLowerCase() ?? null;
    const result = await pool.query(
      `${reportingCtes}
       ${reportingProjection}
       WHERE ($1::text IS NULL OR modelversion = $1)
         AND ($2::text IS NULL OR LOWER(prop_type) = LOWER($2))
        ORDER BY event_date DESC, ABS(normalized_edge) DESC NULLS LAST, player
       LIMIT 200`,
      [modelVersion, propType],
    );
    response.json(
      GetPipelinePredictionsResponse.parse(result.rows.map(toPropRow)),
    );
  } catch (error) {
    request.log.error({ err: error }, "Pipeline predictions request failed");
    response.status(500).json({ message: "Unable to load predictions." });
  }
});

router.get("/pipeline/model-versions", async (request, response) => {
  try {
    const result = await pool.query(`
      ${reportingCtes}
      SELECT
        modelversion,
        sport,
        prop_type,
        prop_label,
        COUNT(DISTINCT prediction_id)::text AS prediction_count,
        MIN(predictiontimestamp)::text AS first_seen,
        MAX(predictiontimestamp)::text AS last_seen
      FROM reporting
      GROUP BY modelversion, sport, prop_type, prop_label
      ORDER BY MAX(predictiontimestamp) DESC, modelversion, prop_type
    `);
    response.json(
      GetPipelineModelVersionsResponse.parse(
        result.rows.map((row) => ({
          modelVersion: String(row.modelversion),
          sport: String(row.sport),
          propType: String(row.prop_type),
          propLabel: String(row.prop_label),
          predictionCount: Number(row.prediction_count),
          firstSeen: row.first_seen,
          lastSeen: row.last_seen,
        })),
      ),
    );
  } catch (error) {
    request.log.error({ err: error }, "Pipeline model versions request failed");
    response.status(500).json({ message: "Unable to load model versions." });
  }
});

router.get("/pipeline/backtest", async (request, response) => {
  try {
    if (backtestCache && backtestCache.expiresAt > Date.now()) {
      response.json(backtestCache.value);
      return;
    }

    const payload = await refreshBacktestCache();
    response.json(payload);
    return;

  } catch (error) {
    request.log.error({ err: error }, "Pipeline backtest request failed");
    response.status(500).json({ message: "Unable to load backtest accuracy." });
  }
});

router.get("/pipeline/trends", async (request, response) => {
  try {
    const playerId = queryString(request, "playerId");
    const stat = (queryString(request, "stat") ?? "aces").toLowerCase();
    const modelVersion = queryString(request, "modelVersion") ?? null;
    if (!playerId) {
      response.status(400).json({ message: "playerId is required." });
      return;
    }

    if (!supportedPropTypes.has(stat)) {
      response.status(400).json({ message: "stat must be a supported prop key." });
      return;
    }
    const result = await pool.query(
      `
        ${reportingCtes}
        , selected_model AS (
          SELECT modelversion
          FROM reporting
          WHERE player_id = $1
            AND LOWER(prop_type) = LOWER($2)
            AND ($3::text IS NULL OR modelversion = $3)
          GROUP BY modelversion
          ORDER BY MAX(predictiontimestamp) DESC, modelversion DESC
          LIMIT 1
        )
        SELECT *
        FROM (
          SELECT DISTINCT ON (match_id)
            event_date,
            opponent,
            actual_value AS value,
            rolling_average,
            line AS posted_line
          FROM reporting
          WHERE player_id = $1
            AND LOWER(prop_type) = LOWER($2)
            AND modelversion = (SELECT modelversion FROM selected_model)
          ORDER BY match_id, captured_at DESC NULLS LAST, book ASC NULLS LAST
        ) AS trend
        ORDER BY event_date ASC
      `,
      [playerId, stat, modelVersion],
    );
    response.json(
      GetPlayerTrendResponse.parse(
        result.rows.map((row) => ({
          eventDate: row.event_date,
          opponent: String(row.opponent ?? "Opponent"),
          value: nullableNumber(row.value),
          rollingAverage: nullableNumber(row.rolling_average),
          postedLine: nullableNumber(row.posted_line),
        })),
      ),
    );
  } catch (error) {
    request.log.error({ err: error }, "Player trend request failed");
    response.status(500).json({ message: "Unable to load player trend." });
  }
});

export default router;