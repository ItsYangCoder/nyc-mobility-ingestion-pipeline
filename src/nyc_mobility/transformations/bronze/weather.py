"""Bronze streaming table for Open-Meteo JSON response files."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
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
                    StructField("temperature_2m", ArrayType(DoubleType())),
                    StructField("precipitation", ArrayType(DoubleType())),
                    StructField("wind_speed_10m", ArrayType(DoubleType())),
                ]
            ),
        ),
    ]
)


@dp.table(
    name="bronze_weather_raw",
    comment="Raw Open-Meteo responses incrementally loaded from landed JSON.",
    table_properties={"quality": "bronze"},
)
@dp.expect("source_file_present", "_source_file IS NOT NULL")
def bronze_weather_raw():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("multiLine", "true")
        .option(
            "pathGlobFilter",
            "weather_????-??-??_????-??-??.json",
        )
        .schema(WEATHER_SCHEMA)
        .load(f"{LANDING_PATH}/weather")
        .select(
            "*",
            F.col("_metadata.file_path").alias("_source_file"),
            F.col("_metadata.file_modification_time").alias(
                "_source_file_modified_at"
            ),
            F.current_timestamp().alias("_ingested_at"),
        )
    )
