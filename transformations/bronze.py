"""Bronze streaming tables for the three required NYC Mobility sources."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)


LANDING_PATH = spark.conf.get(
    "nyc_mobility.landing_path",
    "/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing",
)

WEATHER_SCHEMA = StructType(
    [
        StructField("latitude", DoubleType()),
        StructField("longitude", DoubleType()),
        StructField("generationtime_ms", DoubleType()),
        StructField("utc_offset_seconds", LongType()),
        StructField("timezone", StringType()),
        StructField("timezone_abbreviation", StringType()),
        StructField("elevation", DoubleType()),
        StructField(
            "hourly_units",
            StructType(
                [
                    StructField("time", StringType()),
                    StructField("temperature_2m", StringType()),
                    StructField("precipitation", StringType()),
                    StructField("wind_speed_10m", StringType()),
                ]
            ),
        ),
        StructField(
            "hourly",
            StructType(
                [
                    StructField("time", ArrayType(StringType())),
                    StructField(
                        "temperature_2m",
                        ArrayType(DoubleType()),
                    ),
                    StructField(
                        "precipitation",
                        ArrayType(DoubleType()),
                    ),
                    StructField(
                        "wind_speed_10m",
                        ArrayType(DoubleType()),
                    ),
                ]
            ),
        ),
    ]
)

TAXI_ZONES_SCHEMA = StructType(
    [
        StructField("LocationID", IntegerType()),
        StructField("Borough", StringType()),
        StructField("Zone", StringType()),
        StructField("service_zone", StringType()),
    ]
)


def with_audit_columns(dataframe):
    """Add ingestion lineage without changing source fields."""
    return dataframe.select(
        "*",
        F.col("_metadata.file_path").alias("_source_file"),
        F.current_timestamp().alias("_ingested_at"),
    )


@dp.table(
    name="bronze_green_taxi_raw",
    comment="Raw NYC Green Taxi trips incrementally loaded from landed Parquet.",
    table_properties={"quality": "bronze"},
)
@dp.expect("source_file_present", "_source_file IS NOT NULL")
def bronze_green_taxi_raw():
    return with_audit_columns(
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .option("pathGlobFilter", "*.parquet")
        .load(f"{LANDING_PATH}/green_taxi")
    )


@dp.table(
    name="bronze_weather_raw",
    comment="Raw Open-Meteo responses incrementally loaded from landed JSON.",
    table_properties={"quality": "bronze"},
)
@dp.expect("source_file_present", "_source_file IS NOT NULL")
def bronze_weather_raw():
    return with_audit_columns(
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("multiLine", "true")
        .option(
            "pathGlobFilter",
            "weather_????-??-??_????-??-??.json",
        )
        .schema(WEATHER_SCHEMA)
        .load(f"{LANDING_PATH}/weather")
    )


@dp.table(
    name="bronze_taxi_zones_raw",
    comment="Raw NYC Taxi Zones incrementally loaded from the landed CSV.",
    table_properties={"quality": "bronze"},
)
@dp.expect("source_file_present", "_source_file IS NOT NULL")
def bronze_taxi_zones_raw():
    return with_audit_columns(
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("pathGlobFilter", "taxi_zone_lookup.csv")
        .schema(TAXI_ZONES_SCHEMA)
        .load(f"{LANDING_PATH}/taxi_zones")
    )
