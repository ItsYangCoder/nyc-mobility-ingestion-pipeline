from pyspark import pipelines as dp
from pyspark.sql import functions as F


BRONZE_WEATHER_TABLE = (
    "nyc_mobility.nyc_bronze.bronze_weather_raw"
)


@dp.table(
    name="silver_weather_hourly",
    comment="Validated hourly NYC weather observations.",
)
def silver_weather_hourly():
    weather_bronze = spark.read.table(
        BRONZE_WEATHER_TABLE
    )

    weather_arrays = weather_bronze.select(
        "*",
        F.col("hourly.time").alias("_time"),
        F.col("hourly.temperature_2m").alias("_temperature"),
        F.col("hourly.precipitation").alias("_precipitation"),
        F.col("hourly.wind_speed_10m").alias("_wind_speed"),
    )

    weather_zipped = weather_arrays.withColumn(
        "_hourly_zipped",
        F.arrays_zip(
            "_time",
            "_temperature",
            "_precipitation",
            "_wind_speed",
        ),
    )

    weather_exploded = weather_zipped.select(
        "*",
        F.posexplode("_hourly_zipped").alias(
            "hour_index",
            "weather_hour",
        ),
    )

    return weather_exploded.select(
        F.to_timestamp(
            F.col("weather_hour._time"),
            "yyyy-MM-dd'T'HH:mm",
        ).alias("weather_hour_local"),

        F.to_date(
            F.col("weather_hour._time")
        ).alias("weather_date_local"),

        F.col("weather_hour._temperature")
        .cast("double")
        .alias("temperature_2m_c"),

        F.col("weather_hour._precipitation")
        .cast("double")
        .alias("precipitation_mm"),

        F.col("weather_hour._wind_speed")
        .cast("double")
        .alias("wind_speed_10m_kmh"),

        F.col("timezone").alias("timezone"),

        F.col("_source_file").alias("source_file"),

        F.col("_ingested_at").alias("ingested_at"),
    )