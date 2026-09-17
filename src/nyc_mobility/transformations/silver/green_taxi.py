"""Lakeflow definition for the Silver Green Taxi transformation."""

from pyspark import pipelines as dp

from nyc_mobility.config import load_config
from nyc_mobility.transformations.core import build_silver_green_taxi

CONFIG = load_config(spark)
BRONZE_TABLE = CONFIG.table("bronze", "bronze_green_taxi_raw")
SILVER_TABLE = CONFIG.table("silver", "silver_green_taxi_trips")


@dp.materialized_view(
    name=SILVER_TABLE,
    comment="Typed and quality-flagged NYC Green Taxi trip records.",
    table_properties={
        "quality": "silver",
        "delta.feature.timestampNtz": "supported",
    },
)
@dp.expect("trip_key_present", "trip_key IS NOT NULL")
@dp.expect("pickup_timestamp_present", "pickup_ts_local IS NOT NULL")
@dp.expect("dropoff_timestamp_present", "dropoff_ts_local IS NOT NULL")
@dp.expect("pickup_location_present", "pu_location_id IS NOT NULL")
@dp.expect("dropoff_location_present", "do_location_id IS NOT NULL")
@dp.expect(
    "source_lineage_present",
    """
    source_file IS NOT NULL
    AND source_file_modified_at IS NOT NULL
    AND ingested_at IS NOT NULL
    """,
)
def silver_green_taxi_trips():
    """Register the production transformation as a Lakeflow materialized view."""
    return build_silver_green_taxi(spark.read.table(BRONZE_TABLE), CONFIG)
