"""Shared pytest fixtures for local Spark integration tests."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def spark():
    """Provide a deterministic, single-process Spark session."""
    from databricks.connect import DatabricksSession

    session = DatabricksSession.builder.getOrCreate()
    session.conf.set("spark.sql.shuffle.partitions", "1")
    session.conf.set("spark.sql.session.timeZone", "UTC")
    yield session
