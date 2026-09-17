"""Gold date dimension for the approved March-May 2026 analysis window."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F


GOLD_TABLE = "nyc_mobility.nyc_gold.dim_date"
START_DATE = "2026-03-01"
END_DATE = "2026-05-31"


@dp.materialized_view(
    name=GOLD_TABLE,
    comment="Conformed calendar date dimension for NYC Mobility analytics.",
    table_properties={"quality": "gold", "grain": "one row per calendar date"},
)
@dp.expect_or_fail("date_key_present", "date_key IS NOT NULL")
@dp.expect_or_fail("full_date_present", "full_date IS NOT NULL")
def dim_date():
    return (
        spark.sql(
            f"""
            SELECT explode(
                sequence(
                    DATE '{START_DATE}',
                    DATE '{END_DATE}',
                    INTERVAL 1 DAY
                )
            ) AS full_date
            """
        )
        .select(
            F.date_format("full_date", "yyyyMMdd").cast("int").alias("date_key"),
            "full_date",
            F.year("full_date").alias("year"),
            F.quarter("full_date").alias("quarter"),
            F.month("full_date").alias("month"),
            F.date_format("full_date", "MMMM").alias("month_name"),
            F.dayofmonth("full_date").alias("day_of_month"),
            F.dayofweek("full_date").alias("day_of_week"),
            F.date_format("full_date", "EEEE").alias("day_name"),
            (F.dayofweek("full_date").isin(1, 7)).alias("weekend_flag"),
        )
    )
