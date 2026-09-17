"""Silver cleaning transformation for NYC Taxi Zones."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

from nyc_mobility.config import load_config

CONFIG = load_config(spark)
BRONZE_TAXI_ZONES = CONFIG.table("bronze", "bronze_taxi_zones_raw")
SILVER_TAXI_ZONES = CONFIG.table("silver", "silver_taxi_zones")


def clean_text(column_name):
    """Normalize harmless whitespace while preserving punctuation."""
    return F.trim(
        F.regexp_replace(
            F.col(column_name),
            r"\s+",
            " ",
        )
    )


def has_control_chars(column_name):
    """Flag hidden/control characters in source text."""
    return F.coalesce(
        F.col(column_name).rlike(r"[\x00-\x1F\x7F]"),
        F.lit(False),
    )


@dp.materialized_view(
    name=SILVER_TAXI_ZONES,
    comment=(
        "Cleaned and standardized NYC Taxi Zones "
        "from the latest source ingestion snapshot."
    ),
    table_properties={"quality": "silver"},
)
def silver_taxi_zones():

    # 1. Clean and standardize Bronze values.
    standardized = spark.read.table(BRONZE_TAXI_ZONES).select(
        F.col("LocationID").cast("int").alias("location_id"),
        clean_text("Borough").alias("borough"),
        clean_text("Zone").alias("zone"),
        clean_text("service_zone").alias("service_zone"),
        (
            has_control_chars("Borough")
            | has_control_chars("Zone")
            | has_control_chars("service_zone")
        ).alias("had_control_char"),
        F.col("_source_file"),
        F.col("_source_file_modified_at"),
        F.col("_ingested_at"),
    )

    # 2. Identify the latest Taxi Zones ingestion snapshot.
    latest_snapshot = standardized.agg(
        F.max("_ingested_at").alias("_latest_ingested_at")
    )

    # The right side has exactly one aggregate row,
    # so this does not cause row explosion.
    latest_rows = (
        standardized.crossJoin(latest_snapshot)
        .filter(F.col("_ingested_at").eqNullSafe(F.col("_latest_ingested_at")))
        .drop("_latest_ingested_at")
    )

    # 3. Detect exact duplicates and conflicting business values.
    assessed = (
        latest_rows.groupBy("location_id")
        .agg(
            F.sort_array(
                F.collect_set(
                    F.struct(
                        "borough",
                        "zone",
                        "service_zone",
                    )
                )
            ).alias("_business_variants"),
            F.count("*").alias("source_row_count"),
            F.max("_source_file").alias("_source_file"),
            F.max("_source_file_modified_at").alias("_source_file_modified_at"),
            F.max("_ingested_at").alias("_ingested_at"),
            F.max(F.col("had_control_char").cast("int")).alias("_had_control_char"),
        )
        .withColumn(
            "variant_count",
            F.size("_business_variants"),
        )
        .withColumn(
            "duplicate_row_count",
            F.col("source_row_count") - F.col("variant_count"),
        )
    )

    # 4. Produce one canonical row per LocationID.
    # Conflicting values are flagged instead of silently choosing one.
    result = (
        assessed.select(
            "location_id",
            F.when(
                F.col("variant_count") == 1,
                F.element_at(
                    "_business_variants",
                    1,
                ).getField("borough"),
            )
            .otherwise(F.lit(None).cast("string"))
            .alias("borough"),
            F.when(
                F.col("variant_count") == 1,
                F.element_at(
                    "_business_variants",
                    1,
                ).getField("zone"),
            )
            .otherwise(F.lit(None).cast("string"))
            .alias("zone"),
            F.when(
                F.col("variant_count") == 1,
                F.element_at(
                    "_business_variants",
                    1,
                ).getField("service_zone"),
            )
            .otherwise(F.lit(None).cast("string"))
            .alias("service_zone"),
            F.col("_business_variants").alias("business_variants"),
            "_source_file",
            "_source_file_modified_at",
            "_ingested_at",
            "source_row_count",
            "duplicate_row_count",
            "variant_count",
            F.col("_had_control_char").cast("boolean").alias("had_control_char"),
        )
        .withColumn(
            "has_invalid_location_id",
            F.col("location_id").isNull() | (F.col("location_id") <= 0),
        )
        .withColumn(
            "has_duplicate_key",
            F.col("source_row_count") > 1,
        )
        .withColumn(
            "has_conflicting_values",
            F.col("variant_count") > 1,
        )
        .withColumn(
            "has_missing_required",
            F.col("borough").isNull()
            | (F.length("borough") == 0)
            | F.col("zone").isNull()
            | (F.length("zone") == 0)
            | F.col("service_zone").isNull()
            | (F.length("service_zone") == 0),
        )
        .withColumn(
            "silver_processed_at",
            F.current_timestamp(),
        )
        .withColumn(
            "quality_status",
            F.when(
                F.col("has_invalid_location_id")
                | F.col("has_conflicting_values")
                | F.col("has_missing_required")
                | F.col("had_control_char"),
                F.lit("REVIEW"),
            )
            .when(
                F.col("has_duplicate_key"),
                F.lit("DUPLICATE"),
            )
            .otherwise(F.lit("OK")),
        )
    )

    return result
