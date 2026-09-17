"""Gold taxi-trip fact at one row per retained trip."""

from pyspark import pipelines as dp

from nyc_mobility.config import load_config
from nyc_mobility.transformations.core import build_fact_taxi_trip

CONFIG = load_config(spark)
SILVER_TABLE = CONFIG.table("silver", "silver_green_taxi_trips")
GOLD_TABLE = CONFIG.table("gold", "fact_taxi_trip")


@dp.materialized_view(
    name=GOLD_TABLE,
    comment="Green Taxi fact at one row per in-window retained trip.",
    table_properties={"quality": "gold", "grain": "one row per taxi trip"},
)
@dp.expect_or_fail("trip_key_present", "trip_key IS NOT NULL")
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
    "dimension_keys_present",
    """
    pickup_date_key IS NOT NULL
    AND dropoff_date_key IS NOT NULL
    AND pickup_hour_key IS NOT NULL
    AND dropoff_hour_key IS NOT NULL
    AND pickup_location_id IS NOT NULL
    AND dropoff_location_id IS NOT NULL
    """,
)
def fact_taxi_trip():
    """Register the production transformation as a Lakeflow materialized view."""
    return build_fact_taxi_trip(spark.read.table(SILVER_TABLE))
