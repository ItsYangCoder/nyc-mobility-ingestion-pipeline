"""Silver transformation for NYC Green Taxi trips."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql import Window


BRONZE_TABLE = "nyc_mobility.nyc_bronze.bronze_green_taxi_raw"

CANDIDATE_KEY = [
    "vendor_id",
    "pickup_ts_local",
    "dropoff_ts_local",
    "pu_location_id",
    "do_location_id",
]

SOURCE_RECORD_COLS = [
    "vendor_id",
    "pickup_ts_local",
    "dropoff_ts_local",
    "store_and_fwd_flag",
    "ratecode_id",
    "pu_location_id",
    "do_location_id",
    "passenger_count",
    "trip_distance",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "ehail_fee",
    "improvement_surcharge",
    "total_amount",
    "payment_type",
    "trip_type",
    "congestion_surcharge",
]


@dp.materialized_view(
    name="nyc_mobility.nyc_silver.silver_green_taxi_trips",
    comment="Typed and quality-flagged NYC Green Taxi trip records.",
    table_properties={"quality": "silver"},
)
@dp.expect("trip_key_present", "trip_key IS NOT NULL")
@dp.expect("pickup_timestamp_present", "pickup_ts_local IS NOT NULL")
@dp.expect("dropoff_timestamp_present", "dropoff_ts_local IS NOT NULL")
@dp.expect("pickup_location_present", "pu_location_id IS NOT NULL")
@dp.expect("dropoff_location_present", "do_location_id IS NOT NULL")
@dp.expect("source_lineage_present", "source_file IS NOT NULL AND ingested_at IS NOT NULL")
def silver_green_taxi_trips():
    df = spark.read.table(BRONZE_TABLE)

    df = df.select(
        F.col("VendorID").cast("long").alias("vendor_id"),
        F.col("lpep_pickup_datetime").cast("timestamp_ntz").alias("pickup_ts_local"),
        F.col("lpep_dropoff_datetime").cast("timestamp_ntz").alias("dropoff_ts_local"),
        F.trim(F.col("store_and_fwd_flag")).alias("store_and_fwd_flag"),
        F.col("RatecodeID").cast("long").alias("ratecode_id"),
        F.col("PULocationID").cast("long").alias("pu_location_id"),
        F.col("DOLocationID").cast("long").alias("do_location_id"),
        F.col("passenger_count").cast("long").alias("passenger_count"),
        F.col("trip_distance").cast("double").alias("trip_distance"),
        F.col("fare_amount").cast("double").alias("fare_amount"),
        F.col("extra").cast("double").alias("extra"),
        F.col("mta_tax").cast("double").alias("mta_tax"),
        F.col("tip_amount").cast("double").alias("tip_amount"),
        F.col("tolls_amount").cast("double").alias("tolls_amount"),
        F.col("ehail_fee").cast("double").alias("ehail_fee"),
        F.col("improvement_surcharge").cast("double").alias("improvement_surcharge"),
        F.col("total_amount").cast("double").alias("total_amount"),
        F.col("payment_type").cast("long").alias("payment_type"),
        F.col("trip_type").cast("long").alias("trip_type"),
        F.col("congestion_surcharge").cast("double").alias("congestion_surcharge"),
        F.col("_source_file").alias("source_file"),
        F.col("_ingested_at").alias("ingested_at"),
    )

    df = (
        df
        .withColumn("pickup_date_local", F.to_date("pickup_ts_local"))
        .withColumn("dropoff_date_local", F.to_date("dropoff_ts_local"))
        .withColumn("pickup_hour_local", F.date_trunc("hour", "pickup_ts_local"))
        .withColumn("_pickup_ts_utc", F.to_utc_timestamp("pickup_ts_local", "America/New_York"))
        .withColumn("_dropoff_ts_utc", F.to_utc_timestamp("dropoff_ts_local", "America/New_York"))
        .withColumn("trip_duration_minutes", (F.unix_timestamp("_dropoff_ts_utc") - F.unix_timestamp("_pickup_ts_utc")) / 60.0)
        .withColumn(
            "is_in_analysis_window",
            (F.col("pickup_date_local") >= F.lit("2026-03-01").cast("date")) &
            (F.col("pickup_date_local") <= F.lit("2026-05-31").cast("date")),
        )
        .withColumn("is_valid_duration", F.col("trip_duration_minutes") >= 0)
        .withColumn("is_zero_duration", F.col("trip_duration_minutes") == 0)
        .withColumn("is_valid_distance", F.col("trip_distance") >= 0)
        .withColumn("is_valid_fare", F.col("fare_amount") >= 0)
        .withColumn("is_valid_total", F.col("total_amount") >= 0)
    )

    candidate_window = Window.partitionBy(*CANDIDATE_KEY)

    df = (
        df
        .withColumn("candidate_group_size", F.count("*").over(candidate_window))
        .withColumn("is_candidate_duplicate", F.col("candidate_group_size") > 1)
        .withColumn(
            "trip_key",
            F.sha2(
                F.to_json(F.struct(*[F.col(c) for c in SOURCE_RECORD_COLS]), options={"ignoreNullFields": "false"}),
                256,
            ),
        )
    )

    return df.select(
        "trip_key",
        "vendor_id",
        "pickup_ts_local",
        "dropoff_ts_local",
        "pickup_date_local",
        "dropoff_date_local",
        "pickup_hour_local",
        "store_and_fwd_flag",
        "ratecode_id",
        "pu_location_id",
        "do_location_id",
        "passenger_count",
        "trip_distance",
        "trip_duration_minutes",
        "fare_amount",
        "extra",
        "mta_tax",
        "tip_amount",
        "tolls_amount",
        "ehail_fee",
        "improvement_surcharge",
        "total_amount",
        "payment_type",
        "trip_type",
        "congestion_surcharge",
        "candidate_group_size",
        "is_candidate_duplicate",
        "is_in_analysis_window",
        "is_valid_duration",
        "is_zero_duration",
        "is_valid_distance",
        "is_valid_fare",
        "is_valid_total",
        "source_file",
        "ingested_at",
    )
