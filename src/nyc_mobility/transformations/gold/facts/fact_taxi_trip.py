"""Gold taxi-trip fact at one row per retained trip."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F


SILVER_TABLE = "nyc_mobility.nyc_silver.silver_green_taxi_trips"
GOLD_TABLE = "nyc_mobility.nyc_gold.fact_taxi_trip"


@dp.materialized_view(
    name=GOLD_TABLE,
    comment="Green Taxi fact at one row per in-window retained trip.",
    table_properties={"quality": "gold", "grain": "one row per taxi trip"},
)
@dp.expect_or_fail("trip_key_present", "trip_key IS NOT NULL")
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
    silver = spark.read.table(SILVER_TABLE)

    return (
        silver
        .filter(F.col("is_in_analysis_window"))
        .filter(
            F.col("pickup_ts_local").isNotNull()
            & F.col("dropoff_ts_local").isNotNull()
            & F.col("pu_location_id").isNotNull()
            & F.col("do_location_id").isNotNull()
        )
        .select(
            F.xxhash64("trip_key", "source_file").alias("trip_key"),
            F.date_format("pickup_date_local", "yyyyMMdd")
            .cast("int")
            .alias("pickup_date_key"),
            F.date_format("dropoff_date_local", "yyyyMMdd")
            .cast("int")
            .alias("dropoff_date_key"),
            F.hour("pickup_ts_local").cast("int").alias("pickup_hour_key"),
            F.hour("dropoff_ts_local").cast("int").alias("dropoff_hour_key"),
            F.col("pu_location_id").cast("int").alias("pickup_location_id"),
            F.col("do_location_id").cast("int").alias("dropoff_location_id"),
            F.col("passenger_count").cast("int").alias("passenger_count"),
            F.col("trip_distance").cast("double").alias("trip_distance"),
            F.col("trip_duration_minutes").cast("double")
            .alias("trip_duration_minutes"),
            F.col("fare_amount").cast("decimal(12,2)").alias("fare_amount"),
            F.col("tip_amount").cast("decimal(12,2)").alias("tip_amount"),
            F.col("total_amount").cast("decimal(12,2)").alias("total_amount"),
            F.col("payment_type").cast("int").alias("payment_type"),
            "source_file",
            F.current_timestamp().alias("gold_loaded_at"),
            F.col("pickup_ts_local").alias("pickup_datetime"),
            F.col("dropoff_ts_local").alias("dropoff_datetime"),
        )
    )
