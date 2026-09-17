"""Gold hourly-weather fact at one row per local observation hour."""

from pyspark import pipelines as dp

from nyc_mobility.config import load_config
from nyc_mobility.transformations.core import build_fact_weather_hourly

CONFIG = load_config(spark)
SILVER_TABLE = CONFIG.table("silver", "silver_weather_hourly")
GOLD_TABLE = CONFIG.table("gold", "fact_weather_hourly")


@dp.materialized_view(
    name=GOLD_TABLE,
    comment="Hourly NYC weather fact aligned to conformed date and hour dimensions.",
    table_properties={"quality": "gold", "grain": "one row per local weather hour"},
)
@dp.expect_or_fail("weather_hour_key_present", "weather_hour_key IS NOT NULL")
@dp.expect_or_fail(
    "source_lineage_present",
    """
    source_file IS NOT NULL
    AND source_file_modified_at IS NOT NULL
    AND ingested_at IS NOT NULL
    AND silver_processed_at IS NOT NULL
    AND gold_loaded_at IS NOT NULL
    """,
)
@dp.expect_or_fail(
    "weather_dimension_keys_present",
    "date_key IS NOT NULL AND hour_key IS NOT NULL",
)
def fact_weather_hourly():
    """Register the production transformation as a Lakeflow materialized view."""
    return build_fact_weather_hourly(spark.read.table(SILVER_TABLE))
