"""Lakeflow definition for the Silver hourly weather transformation."""

from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from nyc_mobility.config import load_config
from nyc_mobility.transformations.core import build_silver_weather

CONFIG = load_config(spark)
BRONZE_TABLE = CONFIG.table("bronze", "bronze_weather_raw")
SILVER_TABLE = CONFIG.table("silver", "silver_weather_hourly")


@dp.materialized_view(
    name=SILVER_TABLE,
    comment=(
        "Typed, positionally aligned, and deduplicated hourly NYC weather "
        "observations from Open-Meteo."
    ),
    table_properties={
        "quality": "silver",
        "grain": "one row per local weather hour",
        "delta.feature.timestampNtz": "supported",
    },
)
@dp.expect_or_fail("hour_present", "weather_hour_local IS NOT NULL")
@dp.expect_or_fail("arrays_aligned", "array_lengths_aligned")
@dp.expect_or_fail("timezone_present", "timezone IS NOT NULL")
@dp.expect_or_fail("expected_timezone", f"timezone = '{CONFIG.timezone}'")
@dp.expect_or_fail(
    "source_lineage_present",
    """
    source_file IS NOT NULL
    AND source_file_modified_at IS NOT NULL
    AND ingested_at IS NOT NULL
    """,
)
@dp.expect("precipitation_nonnegative", "precipitation_mm >= 0")
@dp.expect("wind_speed_nonnegative", "wind_speed_10m_kmh >= 0")
def silver_weather_hourly() -> DataFrame:
    """Register the production transformation as a Lakeflow materialized view."""
    return build_silver_weather(spark.read.table(BRONZE_TABLE), CONFIG)
