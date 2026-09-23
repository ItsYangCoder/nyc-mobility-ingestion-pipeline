# Cross-layer reconciliation evidence

## Scope and rule contract

Issue #9 reconciles the transformation grains rather than assuming every layer
has the same row count:

- Green Taxi Bronze to Silver retains each source record. Invalid or
  out-of-window rows remain in Silver and are only excluded by the documented
  Gold eligibility filters.
- Weather Bronze API responses are expanded to aligned hourly positions, then
  reduced to the latest row per `weather_hour_local`. Repeated or overlapping
  responses therefore do not increase the Silver weather count.
- Taxi Zones uses only the latest ingestion snapshot and reduces it to one
  canonical row per `location_id`.
- Taxi Gold uses in-window Silver rows with non-null pickup/drop-off timestamps
  and location IDs. Fare and total comparisons round Silver values to
  `DECIMAL(12,2)`, matching Gold storage; nulls are not treated as zero.

Taxi exclusion output assigns exactly one reason per row, in this order:
outside analysis window, missing timestamp, missing pickup location, then
missing drop-off location. This makes excluded-row totals additive rather than
double-counting rows that have multiple defects.

The SQL outputs use `source`, expected/actual row counts, row difference, and
`PASS`/`FAIL`, so Issue #6 can execute the rules and Issue #8 can consume their
status without inferring a result from a query parse.

## Local automated evidence

`tests/integration/test_reconciliation.py` covers the production pure Spark
builders with synthetic inputs:

| Scenario | Expected result |
|---|---|
| Taxi Bronze → Silver | Source rows and fare, total, and distance totals match exactly. |
| Taxi Silver → Gold | A June row and a row missing a pickup zone remain in Silver but are legitimately excluded from Gold. |
| Deliberate taxi discrepancy | Missing row, duplicate row, and changed fare each fail reconciliation. |
| Repeated weather snapshot | Two overlapping response rows produce two, not four, Silver hourly rows; the later snapshot wins. |

The reusable March–May fixture separately produces 6 Silver taxi rows, 6 Silver
weather rows, 6 Gold taxi rows, and 6 Gold weather rows. Those are synthetic
test values, not a claim about development workspace tables.

## Development workspace evidence status

The real-data SQL checks must be run against the development catalog before
this evidence can contain observed counts, totals, and final PASS/FAIL values.
That workspace run was not available in this local checkout, so no production
or development result is fabricated here. When access is available, run:

1. `tests/sql/silver/bronze_silver_reconciliation.sql`
2. `tests/sql/silver/silver_measure_reconciliation.sql`
3. `tests/sql/gold/silver_gold_reconciliation.sql`
4. `tests/sql/gold/gold_measure_reconciliation.sql`

Record the execution timestamp, configured catalog/schemas and analysis window,
the returned expected/actual counts and measure differences, and each status.
Keep the production schedule paused until that evidence and review are complete.
