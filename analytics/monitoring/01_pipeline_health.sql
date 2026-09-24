-- authoritative job execution history from Databricks system tables.
-- bind :workspace_id, :job_id, and :workspace_url in the SQL editor/dashboard.
-- timeline rows can be hourly slices; collapse them to one row per job run.
WITH runs AS (
  SELECT
    workspace_id,
    job_id,
    run_id,
    MIN(period_start_time) AS started_at,
    MAX(period_end_time) AS latest_period_end_at,
    MAX_BY(result_state, period_end_time) FILTER (
      WHERE result_state IS NOT NULL
    ) AS result_state,
    MAX_BY(termination_code, period_end_time) FILTER (
      WHERE termination_code IS NOT NULL
    ) AS termination_code
  FROM system.lakeflow.job_run_timeline
  WHERE workspace_id = :workspace_id
    AND job_id = :job_id
    AND period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 30 DAYS
  GROUP BY workspace_id, job_id, run_id
)
SELECT
  workspace_id,
  job_id,
  run_id,
  started_at,
  CASE WHEN result_state IS NOT NULL THEN latest_period_end_at END AS ended_at,
  CASE WHEN result_state IS NOT NULL
    THEN TIMESTAMPDIFF(SECOND, started_at, latest_period_end_at)
  END AS duration_seconds,
  CASE
    WHEN result_state IS NOT NULL THEN result_state
    WHEN latest_period_end_at >= CURRENT_TIMESTAMP() - INTERVAL 2 HOURS
      THEN 'RUNNING'
    ELSE 'UNKNOWN'
  END AS result_state,
  latest_period_end_at AS last_observed_at,
  termination_code,
  MAX(CASE WHEN result_state = 'SUCCEEDED' THEN latest_period_end_at END)
    OVER () AS last_successful_run_at,
  COUNT_IF(result_state IN ('FAILED', 'ERROR', 'TIMED_OUT'))
    OVER () AS failed_run_count_30d,
  COUNT_IF(result_state IS NOT NULL)
    OVER () AS completed_run_count_30d,
  COUNT_IF(result_state IN ('FAILED', 'ERROR', 'TIMED_OUT')) OVER ()
    / NULLIF(COUNT_IF(result_state IS NOT NULL) OVER (), 0)
    AS failure_rate_30d,
  CONCAT(RTRIM(:workspace_url, '/'), '/jobs/', job_id, '/runs/', run_id)
    AS run_url
FROM runs
ORDER BY started_at DESC;
