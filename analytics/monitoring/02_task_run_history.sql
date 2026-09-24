-- task-level outcomes; run_id is the task run, job_run_id is its parent run.
-- bind :workspace_id, :job_id, and :workspace_url.
WITH task_runs AS (
  SELECT
    workspace_id,
    job_id,
    job_run_id,
    run_id AS task_run_id,
    task_key,
    MIN(period_start_time) AS started_at,
    MAX(period_end_time) AS latest_period_end_at,
    MAX_BY(result_state, period_end_time) FILTER (
      WHERE result_state IS NOT NULL
    ) AS result_state,
    MAX_BY(termination_code, period_end_time) FILTER (
      WHERE termination_code IS NOT NULL
    ) AS termination_code
  FROM system.lakeflow.job_task_run_timeline
  WHERE workspace_id = :workspace_id
    AND job_id = :job_id
    AND period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 30 DAYS
  GROUP BY workspace_id, job_id, job_run_id, run_id, task_key
)
SELECT
  workspace_id,
  job_id,
  job_run_id,
  task_run_id,
  task_key,
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
  CONCAT(RTRIM(:workspace_url, '/'), '/jobs/', job_id, '/runs/', job_run_id)
    AS parent_run_url
FROM task_runs
ORDER BY started_at DESC;
