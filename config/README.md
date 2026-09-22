# Runtime configuration

`src/nyc_mobility/config.py` is the single naming and runtime configuration
source for local ingestion, Databricks notebooks, and Lakeflow transformations.
Do not duplicate operational paths or table names in notebooks or pipeline
modules.

| Purpose | Namespace |
|---|---|
| Catalog | `nyc_mobility` |
| R2-backed landing Volume | `nyc_mobility.nyc_group_c.nyc_source_files` |
| Bronze tables | `nyc_mobility.nyc_bronze` |
| Silver tables | `nyc_mobility.nyc_silver` |
| Gold tables | `nyc_mobility.nyc_gold` |
| Quality outputs | `nyc_mobility.nyc_quality` |

Configuration precedence is explicit Databricks task parameters, Spark
configuration (`nyc_mobility.*`), environment variables (`NYC_MOBILITY_*`),
then safe defaults. See `.env.example` for every supported environment
variable. Real credentials must use Databricks secret scopes and must never be
added to this configuration.

The landing schema is for the external Volume only. The Lakeflow source root is
`src/nyc_mobility/transformations/`. Promote changes through `development`,
`testing`, and `main`.

Bundle variables in `databricks.yml` are passed as notebook task parameters for
ingestion/setup and as Spark configuration for Lakeflow. Both paths resolve
through `PipelineConfig`; changing the configured date window automatically
changes the Green Taxi month list and weather date ranges.
