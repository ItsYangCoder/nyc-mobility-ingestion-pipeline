"""Gold hour dimension with one row for every local hour of day."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F


GOLD_TABLE = "nyc_mobility.nyc_gold.dim_hour"


@dp.materialized_view(
    name=GOLD_TABLE,
    comment="Conformed hour-of-day dimension for NYC Mobility analytics.",
    table_properties={"quality": "gold", "grain": "one row per hour of day"},
)
@dp.expect_or_fail("hour_key_valid", "hour_key BETWEEN 0 AND 23")
def dim_hour():
    hours = spark.range(24).select(F.col("id").cast("int").alias("hour_key"))

    return (
        hours
        .withColumn("hour", F.col("hour_key"))
        .withColumn(
            "time_of_day",
            F.when(F.col("hour") < 6, F.lit("overnight"))
            .when(F.col("hour") < 12, F.lit("morning"))
            .when(F.col("hour") < 18, F.lit("afternoon"))
            .otherwise(F.lit("evening")),
        )
        .withColumn(
            "peak_hour_flag",
            F.col("hour").between(7, 9) | F.col("hour").between(16, 19),
        )
    )
