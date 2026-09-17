"""Gold conformed NYC Taxi Zone dimension."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

from nyc_mobility.config import load_config

CONFIG = load_config(spark)
SILVER_TABLE = CONFIG.table("silver", "silver_taxi_zones")
GOLD_TABLE = CONFIG.table("gold", "dim_zone")


@dp.materialized_view(
    name=GOLD_TABLE,
    comment="Conformed NYC Taxi Zone dimension, including locations 264 and 265.",
    table_properties={"quality": "gold", "grain": "one row per location_id"},
)
@dp.expect_or_fail("location_id_present", "location_id IS NOT NULL")
@dp.expect_or_fail("location_id_positive", "location_id > 0")
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
def dim_zone():
    return (
        spark.read.table(SILVER_TABLE)
        .filter(
            ~F.col("has_invalid_location_id")
            & ~F.col("has_conflicting_values")
            & ~F.col("has_missing_required")
        )
        .select(
            F.col("location_id").cast("int").alias("location_id"),
            "borough",
            "zone",
            "service_zone",
            F.col("_source_file").alias("source_file"),
            F.col("_source_file_modified_at").alias("source_file_modified_at"),
            F.col("_ingested_at").alias("ingested_at"),
            "silver_processed_at",
            F.current_timestamp().alias("gold_loaded_at"),
        )
        .dropDuplicates(["location_id"])
    )
