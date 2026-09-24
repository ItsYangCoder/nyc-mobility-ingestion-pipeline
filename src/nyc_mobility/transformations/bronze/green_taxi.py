"""Bronze streaming table for NYC Green Taxi Parquet files."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

from nyc_mobility.config import load_config

CONFIG = load_config(spark)
LANDING_PATH = CONFIG.landing_path


@dp.table(
    name="bronze_green_taxi_raw",
    comment="Raw NYC Green Taxi trips incrementally loaded from landed Parquet.",
    table_properties={
        "quality": "bronze",
        "delta.feature.timestampNtz": "supported",
    },
)
@dp.expect("source_file_present", "_source_file IS NOT NULL")
def bronze_green_taxi_raw():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .option("pathGlobFilter", "*.parquet")
        .load(f"{LANDING_PATH}/green_taxi")
        .select(
            "*",
            F.col("_metadata.file_path").alias("_source_file"),
            F.col("_metadata.file_modification_time").alias("_source_file_modified_at"),
            F.current_timestamp().alias("_ingested_at"),
        )
    )
