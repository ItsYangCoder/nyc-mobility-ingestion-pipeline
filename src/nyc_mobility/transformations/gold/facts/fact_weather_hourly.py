"""Gold hourly-weather fact at one row per local observation hour."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F


SILVER_TABLE = "nyc_mobility.nyc_silver.silver_weather_hourly"
GOLD_TABLE = "nyc_mobility.nyc_gold.fact_weather_hourly"


@dp.materialized_view(
    name=GOLD_TABLE,
    comment="Hourly NYC weather fact aligned to conformed date and hour dimensions.",
    table_properties={"quality": "gold", "grain": "one row per local weather hour"},
)
@dp.expect_or_fail("weather_hour_key_present", "weather_hour_key IS NOT NULL")
@dp.expect_or_fail(
    "weather_dimension_keys_present",
    "date_key IS NOT NULL AND hour_key IS NOT NULL",
)
def fact_weather_hourly():
    silver = spark.read.table(SILVER_TABLE)

    return silver.select(
        F.xxhash64(
            F.date_format("weather_hour_local", "yyyy-MM-dd HH:mm:ss")
        ).alias("weather_hour_key"),
        F.col("weather_hour_local").alias("weather_timestamp"),
        F.date_format("weather_date_local", "yyyyMMdd")
        .cast("int")
        .alias("date_key"),
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
        F.current_timestamp().alias("gold_loaded_at"),
    )
