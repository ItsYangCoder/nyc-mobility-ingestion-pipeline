-- Task-level outcomes; run_id is the task run, job_run_id is its parent run.
-- Bind :workspace_id and :job_id; preserve each task run across retries.
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
  COALESCE(result_state, 'UNKNOWN_OR_IN_PROGRESS') AS result_state,
  termination_code
FROM task_runs
ORDER BY started_at DESC;
