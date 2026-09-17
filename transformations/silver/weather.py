# Databricks notebook source

from pyspark.sql import functions as F


# COMMAND ----------
# Cell 1 - Define reusable Silver transformation

def build_silver_weather(weather_bronze):
    weather_arrays = weather_bronze.select(
        "*",
        F.col("hourly.time").alias("_time"),
        F.col("hourly.temperature_2m").alias("_temperature"),
        F.col("hourly.precipitation").alias("_precipitation"),
        F.col("hourly.wind_speed_10m").alias("_wind_speed"),
    )

    array_checks = weather_arrays.select(
        "_source_file",
        F.size("_time").alias("time_count"),
        F.size("_temperature").alias("temperature_count"),
        F.size("_precipitation").alias("precipitation_count"),
        F.size("_wind_speed").alias("wind_speed_count"),
    )

    bad_arrays = array_checks.filter(
        (F.col("time_count") != F.col("temperature_count"))
        | (F.col("time_count") != F.col("precipitation_count"))
        | (F.col("time_count") != F.col("wind_speed_count"))
    )

    if bad_arrays.limit(1).count() > 0:
        display(bad_arrays)

        raise ValueError(
            "Weather hourly arrays are misaligned."
        )

    print("PASS: all weather hourly arrays are aligned.")

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

    silver_weather = weather_exploded.select(
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

    return silver_weather


# COMMAND ----------
# Cell 2 - Table configuration

BRONZE_WEATHER_TABLE = (
    "nyc_mobility.nyc_bronze.bronze_weather_raw"
)

SILVER_WEATHER_TABLE = (
    "nyc_mobility.nyc_silver.silver_weather_hourly"
)


# COMMAND ----------
# Cell 3 - Read Bronze weather table

weather_bronze = spark.table(
    BRONZE_WEATHER_TABLE
)

print(
    "Bronze weather rows:",
    weather_bronze.count()
)

weather_bronze.printSchema()


# COMMAND ----------
# Cell 4 - Transform Bronze to Silver

silver_weather = build_silver_weather(
    weather_bronze
)

print(
    "Silver transformation completed."
)


# COMMAND ----------
# Cell 5 - Inspect transformed Silver output

silver_weather.printSchema()

display(
    silver_weather
    .orderBy("weather_hour_local")
    .limit(20)
)


# COMMAND ----------
# Cell 6 - Validate duplicate weather hours

duplicate_hours = (
    silver_weather
    .groupBy("weather_hour_local")
    .count()
    .filter(F.col("count") > 1)
)

duplicate_count = duplicate_hours.count()

print(
    "Duplicate weather hours:",
    duplicate_count
)

if duplicate_count > 0:
    display(duplicate_hours)

    raise ValueError(
        "Duplicate weather hours detected."
    )

print(
    "PASS: weather_hour_local is unique."
)


# COMMAND ----------
# Cell 7 - Validate required fields

required_nulls = silver_weather.agg(
    F.sum(
        F.col("weather_hour_local")
        .isNull()
        .cast("int")
    ).alias("weather_hour_nulls"),

    F.sum(
        F.col("timezone")
        .isNull()
        .cast("int")
    ).alias("timezone_nulls"),

    F.sum(
        F.col("source_file")
        .isNull()
        .cast("int")
    ).alias("source_file_nulls"),

    F.sum(
        F.col("ingested_at")
        .isNull()
        .cast("int")
    ).alias("ingested_at_nulls"),
)

display(required_nulls)

null_result = required_nulls.first()

required_null_count = (
    null_result["weather_hour_nulls"]
    + null_result["timezone_nulls"]
    + null_result["source_file_nulls"]
    + null_result["ingested_at_nulls"]
)

if required_null_count > 0:
    raise ValueError(
        "Required Weather Silver fields contain null values."
    )

print(
    "PASS: required Weather Silver fields contain no nulls."
)


# COMMAND ----------
# Cell 8 - Validate date coverage and total row count

coverage = silver_weather.agg(
    F.min(
        "weather_hour_local"
    ).alias("first_hour"),

    F.max(
        "weather_hour_local"
    ).alias("last_hour"),

    F.count("*").alias("row_count"),
)

display(coverage)

coverage_result = coverage.first()

print(
    "First weather hour:",
    coverage_result["first_hour"]
)

print(
    "Last weather hour:",
    coverage_result["last_hour"]
)

print(
    "Total Silver weather rows:",
    coverage_result["row_count"]
)


# COMMAND ----------
# Cell 9 - Validate monthly coverage

monthly_counts = (
    silver_weather
    .withColumn(
        "month",
        F.date_format(
            "weather_hour_local",
            "yyyy-MM",
        ),
    )
    .groupBy("month")
    .count()
    .orderBy("month")
)

display(monthly_counts)


# COMMAND ----------
# Cell 10 - Write validated Silver table

(
    silver_weather.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(
        SILVER_WEATHER_TABLE
    )
)

print(
    "PASS: Weather Silver table written successfully."
)

print(
    f"Output table: {SILVER_WEATHER_TABLE}"
)


# COMMAND ----------
# Post-write verification

saved_weather = spark.table(
    SILVER_WEATHER_TABLE
)

saved_row_count = saved_weather.count()

print(
    "Saved Silver rows:",
    saved_row_count
)

saved_duplicates = (
    saved_weather
    .groupBy("weather_hour_local")
    .count()
    .filter(F.col("count") > 1)
)

saved_duplicate_count = (
    saved_duplicates.count()
)

print(
    "Saved duplicate weather hours:",
    saved_duplicate_count
)

if saved_duplicate_count > 0:
    display(saved_duplicates)

    raise ValueError(
        "Persisted Silver table contains duplicate weather hours."
    )

if saved_row_count != silver_weather.count():
    raise ValueError(
        "Persisted Silver row count does not match transformed row count."
    )

print(
    "PASS: persisted Weather Silver table validated successfully."
)

display(
    saved_weather
    .orderBy("weather_hour_local")
    .limit(20)
)