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

The planned audit code and dashboard query are scaffolds only. They must not be
wired into the workflow until the audit-table schema and DQ severity contract
are approved.
