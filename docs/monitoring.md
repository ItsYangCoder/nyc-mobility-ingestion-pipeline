# Production monitoring and lineage

This document defines the operational monitoring contract for the NYC Mobility
workflow. Repository implementation is complete where identified below, but a
saved Databricks dashboard and its runtime evidence still require development
workspace access.

## Monitoring questions

The dashboard must answer four questions:

1. Did the workflow and each task run successfully?
2. What failed, and where can an operator inspect the original run?
3. Is each dataset available through the configured analysis window?
4. Did every required data-quality rule run and pass?

## Data sources

| Area | Authoritative source | Repository query or adapter | Availability |
|---|---|---|---|
| Execution | `system.lakeflow.job_run_timeline` | `analytics/monitoring/01_pipeline_health.sql` | typically delayed; verify in the target region |
| Task failures | `system.lakeflow.job_task_run_timeline` | `analytics/monitoring/02_task_run_history.sql` | typically delayed; verify in the target region |
| Immediate run context | Databricks Jobs API or supplied task parameters | `nyc_mobility.monitoring.run_audit` and `notebooks/03_record_run_metrics.py` | immediate when invoked with authoritative inputs |
| Quality and coverage | `<catalog>.<quality_schema>.quality_results` from #6 | `analytics/monitoring/03_quality_results.sql` | available after the DQ task persists its results |
| Dataset freshness | Silver and Gold event and processing timestamps | `analytics/monitoring/04_dataset_freshness.sql` | available after the medallion refresh |

The project does not copy Databricks job and task history into another audit
table. System tables remain authoritative for historical execution. The
monitoring notebook normalizes immediate metadata for structured logs and a
task value only. This avoids duplicated records and conflicting run statuses.

## Execution metrics

The execution panel shows `job_id`, `run_id`, start and end timestamps,
duration, result state, termination code, last successful run, last observation,
and the original run URL. A nonterminal row observed within the last two hours
is displayed as `RUNNING`; an older nonterminal row is `UNKNOWN`. This threshold
is a dashboard presentation rule, not proof that the job is still active.
Because system tables are delayed, the Jobs UI or API remains authoritative for
immediate confirmation.

The 30-day failure rate is:

`distinct failed completed parent runs / distinct completed parent runs`

Task retries do not increase the denominator. Failed, error, and timed-out
parent runs count as failures. Running or unknown runs are excluded. Canceled
runs remain visible but are not classified as system failures by the SQL query.

## Failures and retries

The task panel shows the parent run, task run, task key, status, timestamps,
duration, termination code, and parent run URL. Detailed error messages remain
in the protected Jobs run output. The Python adapter sanitizes common inline
credential patterns and limits error context before logging it.

Issue #5 owns the final Job dependency and `run_if` behavior. A monitoring task
must not replace or hide the original upstream failure. Automatic retries must
remain bounded, and a repaired attempt must remain distinguishable from the
original attempt.

## Freshness and expected coverage

Freshness measures source event coverage, not processing time. For this
historical workload, expected coverage ends at the configured
`analysis_end_date`, currently 2026-05-31. Data is:

- `FRESH` when actual coverage reaches the expected date within its tolerance;
- `STALE` when it falls short by more than the tolerance;
- `UNKNOWN` when the check did not run or the actual value is unavailable.

A paused production schedule is not a missed-run incident. The dashboard must
show the schedule state separately from dataset coverage. The freshness query
reports `actual_through` from source event dates and `last_processed_at` from
pipeline timestamps as separate fields. Taxi, weather, and their Gold facts are
compared with the configured historical analysis end date. Taxi Zones is a
static reference dataset and is fresh when a nonempty snapshot is available;
its cadence is an approved source revision rather than a daily schedule.

## Quality status

The quality panel shows run and attempt IDs, dataset and layer, rule, severity,
outcome, timestamp, actual and expected values, failed-record count, sanitized
error, and response action. Outcome precedence for a summary is `ERROR`,
`FAIL`, `WARN`, then `PASS`. The dashboard parameter `expected_rule_ids` must
contain the comma-separated rules selected for the DQ task. The query left
joins that catalogue to persisted results, so an expected rule without a result
is displayed as `NOT_EVALUATED`, never `PASS`. Observed rules not present in the
parameter are retained so configuration drift remains visible.

## Lineage and impact

```text
NYC TLC Parquet ─┐
Open-Meteo JSON ─┼─> landing volume ─> Bronze ─> Silver ─> Gold ─> analytics
Taxi Zones CSV ──┘                         │          │        │
                                           └──────────┴────────┴─> DQ results
                                                                     │
Jobs and task system tables ─────────────────────────────────────────┼─> dashboard
                                                                     │
DQ results ──────────────────────────────────────────────────────────┘
```

Source or landing failures block downstream refresh. Bronze defects can affect
all transformed datasets. Silver filtering, key, or reconciliation defects can
affect Gold facts and dimensions. Gold defects affect analytics consumers. The
post-refresh DQ task reports the completed refresh; it does not prevent Gold
tables from being created. Operators should use Databricks Catalog Explorer
lineage and the linked Job run for object-level and task-level investigation.

## Dashboard construction

Create a Lakeview dashboard with these datasets:

- Execution from `01_pipeline_health.sql`, filtered by workspace, job, and time;
- Failures from `02_task_run_history.sql`, filtered to failed or timed-out tasks;
- Quality from `03_quality_results.sql`, filtered by run and attempt;
- Freshness from `04_dataset_freshness.sql`, using configured table names,
  analysis end date, and tolerance.

The bundle syncs `analytics/**`, so these checked-in queries are available in
the deployed workspace for dashboard construction.

Recommended visualizations are a latest-run status tile, last-success tile,
30-day failure-rate tile, task history table, freshness table, and DQ results
table. Record the saved dashboard URL only after access and execution are
verified. Do not commit workspace credentials or recipient addresses.

Required dashboard parameters are `workspace_id`, `job_id`, `workspace_url`,
`quality_results_table`, `run_id`, `attempt_id`, `expected_rule_ids`, the five
Silver/Gold table identifiers used by the freshness query,
`analysis_end_date`, and `tolerance_days`.

## Permissions and latency

An account administrator must enable `system.lakeflow` and grant the dashboard
identity the required catalog and schema usage plus table `SELECT`. The identity
also needs `SELECT` on the #6 quality result table and access to the SQL
warehouse used by the dashboard. System-table delivery is commonly delayed,
so validate actual regional availability and latency in development before
setting operational expectations.

## Notifications and response

Use native Databricks Job notifications for failed parent runs and critical DQ
failures. Do not alert on successful transient retries or warning-only DQ
results. The recipient or destination remains unconfigured until the team
approves it. Issue #5 owns notification wiring; the monitoring owner maintains
the dashboard and triage definitions. Recovery actions are documented in
`docs/runbooks/recovery.md`.

## Workspace verification still required

- confirm `system.lakeflow` access and query compatibility in development;
- save the dashboard and record its URL;
- capture one successful run and one controlled upstream failure;
- verify `NOT_EVALUATED` and missing metrics remain explicit;
- verify native notification delivery to an approved destination;
- record screenshots or run links in `docs/evidence/monitoring_dashboard.md`.

References: [Jobs system tables](https://docs.databricks.com/aws/en/admin/system-tables/jobs),
[Job dependency conditions](https://docs.databricks.com/aws/en/jobs/run-if).
