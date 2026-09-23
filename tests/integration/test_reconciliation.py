"""Focused reconciliation tests for the production transformation rules."""

from __future__ import annotations

from datetime import datetime

import pytest
from pyspark.sql import Row
from pyspark.sql import functions as F

from nyc_mobility.transformations.core import (
    build_fact_taxi_trip,
    build_silver_green_taxi,
    build_silver_weather,
)
from tests.integration.conftest import _taxi_row, _weather_row, _weather_schema


def _taxi_summary(frame):
    """Return count and source-equivalent taxi measures for reconciliation."""
    row = frame.agg(
        F.count("*").alias("rows"),
        F.sum(F.col("fare_amount").cast("decimal(20, 4)")).alias("fare"),
        F.sum(F.col("total_amount").cast("decimal(20, 4)")).alias("total"),
        F.sum(F.col("trip_distance").cast("decimal(20, 4)")).alias("distance"),
    ).first()
    return row.rows, row.fare, row.total, row.distance


def _taxi_grain(frame, *, is_bronze: bool):
    """Normalize the retained taxi grain on either side of Silver."""
    if is_bronze:
        return frame.select(
            F.col("VendorID").cast("long").alias("vendor_id"),
            F.col("lpep_pickup_datetime")
            .cast("timestamp_ntz")
            .alias("pickup_ts_local"),
            F.col("lpep_dropoff_datetime")
            .cast("timestamp_ntz")
            .alias("dropoff_ts_local"),
            F.col("PULocationID").cast("long").alias("pu_location_id"),
            F.col("DOLocationID").cast("long").alias("do_location_id"),
        )
    return frame.select(
        "vendor_id",
        "pickup_ts_local",
        "dropoff_ts_local",
        "pu_location_id",
        "do_location_id",
    )


def _assert_taxi_reconciles(bronze, silver) -> None:
    """Fail on missing, duplicated, or measure-changed retained taxi rows."""
    assert _taxi_summary(bronze) == _taxi_summary(silver)
    bronze_grain = _taxi_grain(bronze, is_bronze=True)
    silver_grain = _taxi_grain(silver, is_bronze=False)
    assert bronze_grain.exceptAll(silver_grain).limit(1).count() == 0
    assert silver_grain.exceptAll(bronze_grain).limit(1).count() == 0


def test_bronze_to_silver_taxi_preserves_rows_and_measures(spark):
    """Silver retains all taxi records, including rows later excluded from Gold."""
    in_window = _taxi_row(3, 0)
    outside_window = _taxi_row(6, 1)
    missing_zone = _taxi_row(4, 0)
    missing_zone["PULocationID"] = None
    bronze = spark.createDataFrame([in_window, outside_window, missing_zone])

    silver = build_silver_green_taxi(bronze)
    _assert_taxi_reconciles(bronze, silver)

    gold = build_fact_taxi_trip(silver)
    assert gold.count() == 1
    assert gold.select("trip_key").distinct().count() == 1
    assert gold.first().pickup_datetime.month == 3


def test_taxi_reconciliation_detects_missing_duplicate_and_changed_measures(spark):
    """Deliberately bad Silver outputs prove the reconciliation rule is strict."""
    bronze = spark.createDataFrame([_taxi_row(3, 0), _taxi_row(3, 1)])
    silver = build_silver_green_taxi(bronze)

    with pytest.raises(AssertionError):
        _assert_taxi_reconciles(bronze, silver.limit(1))
    with pytest.raises(AssertionError):
        _assert_taxi_reconciles(bronze, silver.unionByName(silver.limit(1)))
    with pytest.raises(AssertionError):
        _assert_taxi_reconciles(
            bronze,
            silver.withColumn("fare_amount", F.col("fare_amount") + F.lit(1.0)),
        )

    equal_measures = [_taxi_row(3, 0), _taxi_row(3, 1)]
    for measure in ("trip_distance", "fare_amount", "total_amount"):
        equal_measures[1][measure] = equal_measures[0][measure]
    bronze_with_equal_measures = spark.createDataFrame(equal_measures)
    silver_with_equal_measures = build_silver_green_taxi(bronze_with_equal_measures)
    first_key = silver_with_equal_measures.first().trip_key
    offsetting_bad_silver = silver_with_equal_measures.filter(
        F.col("trip_key") != first_key
    ).unionByName(silver_with_equal_measures.filter(F.col("trip_key") != first_key))
    with pytest.raises(AssertionError):
        _assert_taxi_reconciles(bronze_with_equal_measures, offsetting_bad_silver)


def test_weather_reconciliation_uses_latest_hourly_snapshot_not_response_count(spark):
    """Overlapping API snapshots collapse to one latest row for each local hour."""
    earlier = _weather_row(3)
    later = earlier.asDict(recursive=True)
    later["_source_file"] = "/landing/weather_2026-03-retry.json"
    later["_source_file_modified_at"] = datetime(2026, 3, 29, 12)
    later["_ingested_at"] = datetime(2026, 3, 29, 12, 5)
    later["hourly"]["temperature_2m"] = [99.0, 100.0]
    bronze = spark.createDataFrame([earlier, Row(**later)], schema=_weather_schema())

    silver = build_silver_weather(bronze)
    assert bronze.count() == 2
    assert silver.count() == 2
    assert silver.select("weather_hour_local").distinct().count() == 2
    assert {
        row.weather_hour_local for row in silver.select("weather_hour_local").collect()
    } == {
        datetime(2026, 3, 5, 8),
        datetime(2026, 3, 5, 9),
    }
    assert {row.temperature_2m_c for row in silver.collect()} == {99.0, 100.0}
    assert {row.source_file for row in silver.select("source_file").collect()} == {
        "/landing/weather_2026-03-retry.json"
    }
