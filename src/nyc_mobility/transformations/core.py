"""Pure Spark DataFrame transformations shared by Lakeflow and tests."""

from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from nyc_mobility.config import CONFIG, PipelineConfig

CANDIDATE_KEY = [
    "vendor_id",
    "pickup_ts_local",
    "dropoff_ts_local",
    "pu_location_id",
    "do_location_id",
]

SOURCE_RECORD_COLS = [
    "source_file_name",
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


def build_silver_green_taxi(
    bronze: DataFrame,
    config: PipelineConfig = CONFIG,
) -> DataFrame:
    """Type taxi fields and derive deterministic keys and quality flags."""
    typed = bronze.select(
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
        F.element_at(F.split(F.col("_source_file"), "/"), -1).alias("source_file_name"),
        F.col("_source_file_modified_at").alias("source_file_modified_at"),
        F.col("_ingested_at").alias("ingested_at"),
    )

    assessed = (
        typed.withColumn("pickup_date_local", F.to_date("pickup_ts_local"))
        .withColumn("dropoff_date_local", F.to_date("dropoff_ts_local"))
        .withColumn(
            "pickup_hour_local",
            F.date_trunc("hour", "pickup_ts_local").cast("timestamp_ntz"),
        )
        .withColumn(
            "_pickup_ts_utc",
            F.to_utc_timestamp("pickup_ts_local", config.timezone),
        )
        .withColumn(
            "_dropoff_ts_utc",
            F.to_utc_timestamp("dropoff_ts_local", config.timezone),
        )
        .withColumn(
            "trip_duration_minutes",
            (F.unix_timestamp("_dropoff_ts_utc") - F.unix_timestamp("_pickup_ts_utc"))
            / 60.0,
        )
        .withColumn(
            "is_in_analysis_window",
            F.col("pickup_date_local").between(
                F.lit(config.analysis_start_date).cast("date"),
                F.lit(config.analysis_end_date).cast("date"),
            ),
        )
        .withColumn("is_valid_duration", F.col("trip_duration_minutes") >= 0)
        .withColumn("is_zero_duration", F.col("trip_duration_minutes") == 0)
        .withColumn("is_valid_distance", F.col("trip_distance") >= 0)
        .withColumn("is_valid_fare", F.col("fare_amount") >= 0)
        .withColumn("is_valid_total", F.col("total_amount") >= 0)
    )

    candidate_window = Window.partitionBy(*CANDIDATE_KEY)
    keyed = (
        assessed.withColumn("candidate_group_size", F.count("*").over(candidate_window))
        .withColumn("is_candidate_duplicate", F.col("candidate_group_size") > 1)
        .withColumn(
            "trip_key",
            F.xxhash64(
                F.to_json(
                    F.struct(*[F.col(column) for column in SOURCE_RECORD_COLS]),
                    options={"ignoreNullFields": "false"},
                )
            ),
        )
        .withColumn("silver_processed_at", F.current_timestamp())
    )

    return keyed.select(
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
        "source_file_name",
        "source_file",
        "source_file_modified_at",
        "ingested_at",
        "silver_processed_at",
    )


def build_silver_weather(
    bronze: DataFrame,
    config: PipelineConfig = CONFIG,
) -> DataFrame:
    """Flatten aligned weather arrays and keep the newest row per local hour."""
    prepared = (
        bronze.select(
            F.col("latitude").cast("double").alias("latitude"),
            F.col("longitude").cast("double").alias("longitude"),
            F.trim(F.col("timezone")).alias("timezone"),
            F.col("utc_offset_seconds").cast("long").alias("utc_offset_seconds"),
            F.col("hourly_units.temperature_2m").alias("temperature_unit"),
            F.col("hourly_units.precipitation").alias("precipitation_unit"),
            F.col("hourly_units.wind_speed_10m").alias("wind_speed_unit"),
            F.col("hourly.time").alias("weather_times"),
            F.col("hourly.temperature_2m").alias("temperatures"),
            F.col("hourly.precipitation").alias("precipitation_values"),
            F.col("hourly.wind_speed_10m").alias("wind_speed_values"),
            F.col("_source_file").alias("source_file"),
            F.col("_source_file_modified_at").alias("source_file_modified_at"),
            F.col("_ingested_at").alias("ingested_at"),
        )
        .withColumn("time_count", F.size("weather_times"))
        .withColumn("temperature_count", F.size("temperatures"))
        .withColumn("precipitation_count", F.size("precipitation_values"))
        .withColumn("wind_speed_count", F.size("wind_speed_values"))
        .withColumn(
            "array_lengths_aligned",
            F.col("time_count").isNotNull()
            & (F.col("time_count") > 0)
            & (F.col("time_count") == F.col("temperature_count"))
            & (F.col("time_count") == F.col("precipitation_count"))
            & (F.col("time_count") == F.col("wind_speed_count")),
        )
        .withColumn(
            "hourly_values",
            F.arrays_zip(
                "weather_times",
                "temperatures",
                "precipitation_values",
                "wind_speed_values",
            ),
        )
    )

    exploded = prepared.select(
        "latitude",
        "longitude",
        "timezone",
        "utc_offset_seconds",
        "temperature_unit",
        "precipitation_unit",
        "wind_speed_unit",
        "array_lengths_aligned",
        "source_file",
        "source_file_modified_at",
        "ingested_at",
        F.posexplode_outer("hourly_values").alias("source_position", "weather"),
    )

    typed = (
        exploded.select(
            F.col("weather.weather_times")
            .cast("timestamp_ntz")
            .alias("weather_hour_local"),
            F.col("weather.temperatures").cast("double").alias("temperature_2m_c"),
            F.col("weather.precipitation_values")
            .cast("double")
            .alias("precipitation_mm"),
            F.col("weather.wind_speed_values")
            .cast("double")
            .alias("wind_speed_10m_kmh"),
            "latitude",
            "longitude",
            "timezone",
            "utc_offset_seconds",
            "temperature_unit",
            "precipitation_unit",
            "wind_speed_unit",
            "array_lengths_aligned",
            F.col("source_position").cast("long").alias("source_position"),
            "source_file",
            "source_file_modified_at",
            "ingested_at",
        )
        .withColumn("weather_date_local", F.to_date("weather_hour_local"))
        .withColumn(
            "is_in_analysis_window",
            F.col("weather_date_local").between(
                F.lit(config.analysis_start_date).cast("date"),
                F.lit(config.analysis_end_date).cast("date"),
            ),
        )
    )

    newest_hour = Window.partitionBy("weather_hour_local").orderBy(
        F.col("source_file_modified_at").desc_nulls_last(),
        F.col("ingested_at").desc_nulls_last(),
        F.col("source_file").desc_nulls_last(),
        F.col("source_position").desc_nulls_last(),
    )

    return (
        typed.withColumn("_row_rank", F.row_number().over(newest_hour))
        .filter(F.col("_row_rank") == 1)
        .drop("_row_rank")
        .withColumn("silver_processed_at", F.current_timestamp())
        .select(
            "weather_hour_local",
            "weather_date_local",
            "temperature_2m_c",
            "precipitation_mm",
            "wind_speed_10m_kmh",
            "latitude",
            "longitude",
            "timezone",
            "utc_offset_seconds",
            "temperature_unit",
            "precipitation_unit",
            "wind_speed_unit",
            "is_in_analysis_window",
            "array_lengths_aligned",
            "source_position",
            "source_file",
            "source_file_modified_at",
            "ingested_at",
            "silver_processed_at",
        )
    )


def build_fact_taxi_trip(silver: DataFrame) -> DataFrame:
    """Build the retained in-window taxi fact with deterministic warehouse keys."""
    return (
        silver.filter(F.col("is_in_analysis_window"))
        .filter(
            F.col("pickup_ts_local").isNotNull()
            & F.col("dropoff_ts_local").isNotNull()
            & F.col("pu_location_id").isNotNull()
            & F.col("do_location_id").isNotNull()
        )
        .select(
            F.xxhash64("trip_key", F.lit("fact_taxi_trip_v1")).alias("trip_key"),
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
            F.col("trip_duration_minutes")
            .cast("double")
            .alias("trip_duration_minutes"),
            F.col("fare_amount").cast("decimal(12,2)").alias("fare_amount"),
            F.col("tip_amount").cast("decimal(12,2)").alias("tip_amount"),
            F.col("total_amount").cast("decimal(12,2)").alias("total_amount"),
            F.col("payment_type").cast("int").alias("payment_type"),
            "source_file",
            "source_file_modified_at",
            "ingested_at",
            "silver_processed_at",
            F.current_timestamp().alias("gold_loaded_at"),
            F.col("pickup_ts_local").alias("pickup_datetime"),
            F.col("dropoff_ts_local").alias("dropoff_datetime"),
        )
    )


def build_fact_weather_hourly(silver: DataFrame) -> DataFrame:
    """Build the in-window hourly weather fact."""
    return silver.filter(F.col("is_in_analysis_window")).select(
        F.xxhash64(F.date_format("weather_hour_local", "yyyy-MM-dd HH:mm:ss")).alias(
            "weather_hour_key"
        ),
        F.col("weather_hour_local").alias("weather_timestamp"),
        F.date_format("weather_date_local", "yyyyMMdd").cast("int").alias("date_key"),
        F.hour("weather_hour_local").cast("int").alias("hour_key"),
        F.col("temperature_2m_c").cast("double").alias("temperature_2m"),
        F.col("precipitation_mm").cast("double").alias("precipitation"),
        F.col("wind_speed_10m_kmh").cast("double").alias("wind_speed_10m"),
        (F.col("precipitation_mm") > 0).alias("precipitation_flag"),
        F.when(F.col("temperature_2m_c").isNull(), F.lit(None).cast("string"))
        .when(F.col("temperature_2m_c") < 0, F.lit("freezing"))
        .when(F.col("temperature_2m_c") < 15, F.lit("cool"))
        .when(F.col("temperature_2m_c") < 25, F.lit("mild"))
        .otherwise(F.lit("warm"))
        .alias("temperature_band"),
        "timezone",
        "source_file",
        "source_file_modified_at",
        "ingested_at",
        "silver_processed_at",
        F.current_timestamp().alias("gold_loaded_at"),
    )
