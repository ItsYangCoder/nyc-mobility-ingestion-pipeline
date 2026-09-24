# Monitoring dashboard evidence

## Repository implementation available

- System-table queries cover parent runs and task runs, including live,
  terminal, and unknown status presentation.
- The quality query emits `NOT_EVALUATED` for expected rules without persisted
  results.
- The freshness query separates source event coverage from processing time for
  Silver and Gold datasets.
- Unit tests protect run normalization, missing metrics, retry handling,
  historical freshness, and the dashboard SQL contracts.

## Development workspace evidence still required

- Databricks workflow run link or screenshot showing task status and duration.
- Latest successful run timestamp and process date.
- One controlled failure showing the failed task and useful error details.
- Dashboard/query result showing freshness, row counts, and DQ status.
- Alert evidence for a critical failure, without exposing recipients or secrets.

Do not record credentials, tokens, raw source data, or sensitive notification
details in this repository.
