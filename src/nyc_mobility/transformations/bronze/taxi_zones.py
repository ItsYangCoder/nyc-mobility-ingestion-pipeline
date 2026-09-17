"""Bronze streaming table for the NYC Taxi Zone lookup CSV."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)


LANDING_PATH = spark.conf.get(
    "nyc_mobility.landing_path",
    "/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing",
)

TAXI_ZONES_SCHEMA = StructType(
    [
        StructField("LocationID", IntegerType()),
        StructField("Borough", StringType()),
        StructField("Zone", StringType()),
        StructField("service_zone", StringType()),
    ]
)


@dp.table(
    name="bronze_taxi_zones_raw",
    comment="Raw NYC Taxi Zones incrementally loaded from the landed CSV.",
    table_properties={"quality": "bronze"},
)
@dp.expect("source_file_present", "_source_file IS NOT NULL")
def bronze_taxi_zones_raw():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("pathGlobFilter", "taxi_zone_lookup.csv")
        .schema(TAXI_ZONES_SCHEMA)
        .load(f"{LANDING_PATH}/taxi_zones")
        .select(
            "*",
            F.col("_metadata.file_path").alias("_source_file"),
            F.col("_metadata.file_modification_time").alias(
                "_source_file_modified_at"
            ),
            F.current_timestamp().alias("_ingested_at"),
        )
    )
