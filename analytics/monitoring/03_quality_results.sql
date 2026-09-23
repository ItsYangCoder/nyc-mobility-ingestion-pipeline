-- Latest runtime data-quality results from Issue #6.
-- Bind :quality_results_table to catalog.schema.quality_results.
WITH ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY run_id, attempt_id, rule_id
      ORDER BY checked_at DESC
    ) AS result_rank
  FROM IDENTIFIER(:quality_results_table)
  WHERE checked_at >= CURRENT_TIMESTAMP() - INTERVAL 30 DAYS
)
SELECT
  run_id,
  attempt_id,
  checked_at,
  layer,
  dataset,
  rule_id,
  severity,
  outcome,
  actual_value,
  expected_value,
  failed_record_count,
  error_message,
  action
FROM ranked
WHERE result_rank = 1
ORDER BY checked_at DESC, layer, dataset, rule_id;

-- Freshness and configured coverage panel.
WITH ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY dataset, rule_id
      ORDER BY checked_at DESC, attempt_id DESC
    ) AS result_rank
  FROM IDENTIFIER(:quality_results_table)
  WHERE rule_id LIKE '%date_coverage%'
    OR rule_id LIKE '%freshness%'
    OR rule_id LIKE '%expected_source_counts%'
)
SELECT
  dataset,
  rule_id,
  checked_at AS last_evaluated_at,
  actual_value,
  expected_value,
  failed_record_count,
  CASE
    WHEN outcome IS NULL THEN 'NOT_EVALUATED'
    ELSE outcome
  END AS freshness_status,
  error_message
FROM ranked
WHERE result_rank = 1
ORDER BY dataset, rule_id;
