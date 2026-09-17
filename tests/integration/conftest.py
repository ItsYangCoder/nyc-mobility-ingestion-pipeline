"""Synthetic Bronze inputs and transformed snapshots for integration tests."""

from __future__ import annotations

from datetime import datetime

import pytest
from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from nyc_mobility.transformations.core import (
    build_fact_taxi_trip,
    build_fact_weather_hourly,
    build_silver_green_taxi,
    build_silver_weather,
)

MONTHS = (3, 4, 5)


def _taxi_row(month: int, trip: int) -> dict[str, object]:
    day = 4 + trip
    pickup = datetime(2026, month, day, 8 + trip, 0)
    return {
        "VendorID": "2",
        "lpep_pickup_datetime": pickup,
        "lpep_dropoff_datetime": pickup.replace(minute=15 + trip),
        "store_and_fwd_flag": "N",
        "RatecodeID": "1",
        "PULocationID": str(40 + trip),
        "DOLocationID": str(70 + trip),
        "passenger_count": str(trip + 1),
        "trip_distance": str(2.5 + month / 10 + trip),
        "fare_amount": str(10 + month + trip),
        "extra": "1.0",
        "mta_tax": "0.5",
        "tip_amount": str(2 + trip),
        "tolls_amount": "0.0",
        "ehail_fee": "0.0",
        "improvement_surcharge": "1.0",
        "total_amount": str(14.5 + month + 2 * trip),
        "payment_type": "1",
        "trip_type": "1",
        "congestion_surcharge": "0.0",
        "_source_file": f"/landing/green_tripdata_2026-{month:02d}.parquet",
        "_source_file_modified_at": datetime(2026, month, 28, 12),
        "_ingested_at": datetime(2026, month, 28, 12, 5),
    }


def _weather_schema() -> StructType:
    return StructType(
        [
            StructField("latitude", DoubleType(), False),
            StructField("longitude", DoubleType(), False),
            StructField("timezone", StringType(), False),
            StructField("utc_offset_seconds", LongType(), False),
            StructField(
                "hourly_units",
                StructType(
                    [
                        StructField("temperature_2m", StringType(), False),
                        StructField("precipitation", StringType(), False),
                        StructField("wind_speed_10m", StringType(), False),
                    ]
                ),
                False,
            ),
            StructField(
                "hourly",
                StructType(
                    [
                        StructField("time", ArrayType(StringType()), False),
                        StructField("temperature_2m", ArrayType(DoubleType()), False),
                        StructField("precipitation", ArrayType(DoubleType()), False),
                        StructField("wind_speed_10m", ArrayType(DoubleType()), False),
                    ]
                ),
                False,
            ),
            StructField("_source_file", StringType(), False),
            StructField("_source_file_modified_at", TimestampType(), False),
            StructField("_ingested_at", TimestampType(), False),
        ]
    )


def _weather_row(month: int) -> Row:
    prefix = f"2026-{month:02d}-05T"
    return Row(
        latitude=40.71,
        longitude=-74.01,
        timezone="America/New_York",
        utc_offset_seconds=-18000,
        hourly_units=Row(
            temperature_2m="°C", precipitation="mm", wind_speed_10m="km/h"
        ),
        hourly=Row(
            time=[prefix + "08:00", prefix + "09:00"],
            temperature_2m=[8.0 + month, 9.0 + month],
            precipitation=[0.0, month / 10],
            wind_speed_10m=[10.0 + month, 11.0 + month],
        ),
        _source_file=f"/landing/weather_2026-{month:02d}.json",
        _source_file_modified_at=datetime(2026, month, 28, 12),
        _ingested_at=datetime(2026, month, 28, 12, 5),
    )


def snapshot(spark, months: tuple[int, ...]):
    """Run production Silver and Gold builders for a set of source months."""
    taxi = spark.createDataFrame(
        [_taxi_row(month, trip) for month in months for trip in range(2)]
    )
    weather = spark.createDataFrame(
        [_weather_row(month) for month in months], schema=_weather_schema()
    )
    taxi_silver = build_silver_green_taxi(taxi).cache()
    weather_silver = build_silver_weather(weather).cache()
    return {
        "taxi_silver": taxi_silver,
        "weather_silver": weather_silver,
        "taxi_gold": build_fact_taxi_trip(taxi_silver).cache(),
        "weather_gold": build_fact_weather_hourly(weather_silver).cache(),
    }


def month_rows(frame, date_column: str, month: int) -> list[str]:
    """Return stable JSON rows for one month, excluding load timestamps."""
    volatile = {"silver_processed_at", "gold_loaded_at"}
    columns = sorted(set(frame.columns) - volatile)
    return sorted(
        row.value
        for row in frame.filter(F.month(date_column) == month)
        .select(F.to_json(F.struct(*columns)).alias("value"))
        .collect()
    )


def measures(frame, date_column: str, month: int) -> tuple[float, float, float]:
    """Return stable taxi measure totals for one month."""
    row = (
        frame.filter(F.month(date_column) == month)
        .agg(
            F.sum("fare_amount").alias("fare"),
            F.sum("total_amount").alias("total"),
            F.sum("trip_distance").alias("distance"),
        )
        .first()
    )
    return float(row.fare), float(row.total), float(row.distance)


@pytest.fixture(scope="module")
def monthly_snapshots(spark):
    """Materialize March, March-April, and March-May test snapshots."""
    snapshots = {
        "march": snapshot(spark, (3,)),
        "april": snapshot(spark, (3, 4)),
        "may": snapshot(spark, MONTHS),
    }
    yield snapshots
    for tables in snapshots.values():
        for frame in tables.values():
            frame.unpersist()
