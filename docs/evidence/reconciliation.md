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

All four reconciliation SQL files use the same output contract:
`source`, `expected_rows`, `actual_rows`, `row_difference`, `fare_difference`,
`total_difference`, `distance_difference`, and `status`. Row-only checks return
NULL for the three measure-difference fields. This lets Issue #6 execute the
rules and Issue #8 consume their status without query-specific parsing.

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

The four live reconciliation SQL checks were run successfully in the
development Databricks workspace on the `feat-reconciliation` bundle using a
Serverless Starter 2XS warehouse. The captured results were:

- Bronze → Silver row reconciliation: `green_taxi` 133,367 / 133,367,
  `taxi_zones` 265 / 265, and `weather` 2,208 / 2,208 expected/actual rows;
  every row difference was 0 and every status was `PASS`.
- Bronze → Silver taxi measures: 133,367 / 133,367 rows; fare, total, and
  distance differences were all `0.0000`; status `PASS`.
- Silver → Gold row reconciliation: 133,356 eligible taxi rows / 133,356 Gold
  rows and 2,208 eligible weather rows / 2,208 Gold rows; every row difference
  was 0 and every status was `PASS`.
- Silver → Gold taxi measures: 133,356 / 133,356 rows; fare, total, and
  distance differences were all `0.0000`; status `PASS`.

The attached Databricks result captures are the execution evidence. The SQL
files now expose the shared result contract described above; their comparison
logic is unchanged from the captured run. Keep the production schedule paused
until review is complete.
