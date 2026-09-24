-- quality results for one selected run and attempt.
-- bind :quality_results_table, :run_id, :attempt_id, and :expected_rule_ids.
-- expected_rule_ids is a comma-separated list supplied by the selected DQ task.
WITH selected_attempt AS (
  SELECT CAST(:run_id AS STRING) AS run_id,
         CAST(:attempt_id AS STRING) AS attempt_id
),
expected_rules AS (
  SELECT TRIM(rule_id) AS rule_id
  FROM (SELECT EXPLODE(SPLIT(:expected_rule_ids, ',')) AS rule_id)
  WHERE TRIM(rule_id) != ''
),
ranked_results AS (
  SELECT
    q.*,
    ROW_NUMBER() OVER (
      PARTITION BY q.run_id, q.attempt_id, q.rule_id
      ORDER BY q.checked_at DESC
    ) AS result_rank
  FROM IDENTIFIER(:quality_results_table) q
  CROSS JOIN selected_attempt s
  WHERE q.run_id = s.run_id AND q.attempt_id = s.attempt_id
),
observed_results AS (
  SELECT * FROM ranked_results WHERE result_rank = 1
),
rule_catalog AS (
  SELECT rule_id FROM expected_rules
  UNION
  SELECT rule_id FROM observed_results
)
SELECT
  s.run_id,
  s.attempt_id,
  q.checked_at,
  q.layer,
  q.dataset,
  r.rule_id,
  q.severity,
  COALESCE(q.outcome, 'NOT_EVALUATED') AS outcome,
  q.actual_value,
  q.expected_value,
  q.failed_record_count,
  q.error_message,
  q.action
FROM selected_attempt s
CROSS JOIN rule_catalog r
LEFT JOIN observed_results q ON r.rule_id = q.rule_id
ORDER BY q.checked_at DESC, q.layer, q.dataset, r.rule_id;
