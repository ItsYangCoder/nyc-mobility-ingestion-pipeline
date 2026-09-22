# Monitoring and failure alerts

This document is the monitoring contract for the NYC Mobility workflow.

## TODO(mafelisilda): monitoring scope

- Define the Databricks Job/Workflow status, task, duration, retry, and error
  fields the team will inspect after every run.
- Define freshness and process-date expectations for each source and layer.
- Align data-quality status with the agreed `PASS`, `WARN`, and `FAIL` rules.
- Define alert rules: critical job/DQ failures alert; harmless warnings are
  visible in logs/dashboard but do not notify the team.
- Choose and document the notification channel (start with Databricks job email
  notification unless the team approves another destination).
- Link failure responses to `docs/runbooks/recovery.md` after it is created.

## Implementation dependency

## Job and task run audit source

Use Databricks' native `system.lakeflow.job_run_timeline` and
`system.lakeflow.job_task_run_timeline` as the authoritative record of job and
task outcomes. The read-only example queries are in
`analytics/monitoring/01_pipeline_health.sql` and
`analytics/monitoring/02_task_run_history.sql`. Bind `:workspace_id` and
`:job_id` to the actual deployment values. Run them in the Databricks SQL
editor first, then add the validated queries to Angela's monitoring dashboard.

The job timeline reports a parent job `run_id`; the task timeline reports its
own `run_id` and links to the parent via `job_run_id`. Both timelines can contain
hourly slices of a run, so the queries group by the real run keys before
reporting status. A NULL outcome is reported as `UNKNOWN_OR_IN_PROGRESS`:
system-table delivery is delayed, so NULL alone does not establish a live run.
For immediate alerts and live state, use Databricks Jobs UI/API and native Job
failure notifications, not these delayed queries.

An account administrator must enable the `system.lakeflow` schema and grant
the dashboard identity `USE` and `SELECT` access to the relevant system schema.
Validate access and regional coverage in the development workspace. Databricks
documents approximately one-hour typical record availability and 365-day
retention for these tables; new workspaces can take longer.

The existing `run_audit.py` and `03_record_run_metrics.py` remain scaffolds. Do
not create a second table copying job status or have a notebook guess whether
an upstream task passed. Persist only domain-specific values that the platform
does not provide, such as #6's DQ results, once the result contract is agreed.
Shiena (#5) owns Job failure-path integration; Angela (#8) owns the dashboard.
The queries do not assert that Databricks system-table access or dashboard
execution has already been verified.

References: [Jobs system tables](https://docs.databricks.com/aws/en/admin/system-tables/jobs),
[Job dependency conditions](https://docs.databricks.com/aws/en/jobs/run-if).
