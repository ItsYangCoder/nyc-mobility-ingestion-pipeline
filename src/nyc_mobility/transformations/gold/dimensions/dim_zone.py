"""Gold conformed NYC Taxi Zone dimension."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F


SILVER_TABLE = "nyc_mobility.nyc_silver.silver_taxi_zones"
GOLD_TABLE = "nyc_mobility.nyc_gold.dim_zone"


@dp.materialized_view(
    name=GOLD_TABLE,
    comment="Conformed NYC Taxi Zone dimension, including locations 264 and 265.",
    table_properties={"quality": "gold", "grain": "one row per location_id"},
)
@dp.expect_or_fail("location_id_present", "location_id IS NOT NULL")
@dp.expect_or_fail("location_id_positive", "location_id > 0")
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
        )
        .dropDuplicates(["location_id"])
    )
