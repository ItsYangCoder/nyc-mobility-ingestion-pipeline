# Databricks bundle deployment

## Prerequisites

- Databricks CLI 0.294.0 or newer.
- An authenticated Databricks CLI profile for the selected workspace.
- Permission to create jobs, pipelines, the target catalog, and schemas.
- Read/write access to the existing landing path configured by
  `BUNDLE_VAR_landing_path`.
- A production service principal with the required Unity Catalog and workspace
  permissions.

The bundle does not create an external location, storage credential, or R2
volume. Those infrastructure objects are security-sensitive prerequisites and
must be provisioned by the platform administrator.

## Development

```bash
export DATABRICKS_HOST="https://<development-workspace>"

databricks bundle validate -t development
databricks bundle deploy -t development
databricks bundle run -t development mobility_workflow
```

The development target uses the `nyc_mobility_dev` catalog by default and runs
the pipeline in development mode. Override any declared bundle variable with a
`BUNDLE_VAR_<name>` environment variable.

## Production

```bash
export DATABRICKS_HOST="https://<production-workspace>"
export BUNDLE_VAR_service_principal_name="<application-id>"

databricks bundle validate -t production
databricks bundle deploy -t production
databricks bundle run -t production mobility_workflow
```

The production schedule is initially `PAUSED`. Complete a reviewed manual run,
inspect pipeline expectations and output reconciliation, then unpause the
schedule through a reviewed configuration change.

## Task order

1. `setup_environment` creates the catalog/schemas idempotently and verifies
   landing-volume access.
2. `land_raw_sources` acquires and validates all required source files.
3. `refresh_medallion_pipeline` refreshes the Bronze, Silver, and Gold graph.

Jobs are queued and limited to one concurrent run. Task retries cover transient
job failures; source-specific HTTP retry behavior is implemented separately in
the ingestion utilities.

## Rollback

Redeploy the last known-good Git commit to the same target. The bundle retains
pipeline-managed datasets when destroyed (`cascade_on_destroy: false`), so code
rollback does not implicitly delete accepted tables.
