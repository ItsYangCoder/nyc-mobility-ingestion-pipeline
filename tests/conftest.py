"""Shared pytest fixtures for local Spark integration tests."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def spark():
    """Provide a deterministic, single-process Spark session."""
    from pyspark.sql import SparkSession

    session = (
        SparkSession.builder.master("local[1]")
        .appName("nyc-mobility-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()
