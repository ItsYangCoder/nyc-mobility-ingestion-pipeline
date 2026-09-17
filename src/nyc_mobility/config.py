"""Central configuration for local code and Databricks pipelines.

Configuration precedence is:

1. Databricks/Spark configuration (``nyc_mobility.*``)
2. Environment variables (``NYC_MOBILITY_*``)
3. Version-controlled, non-secret defaults

Secrets do not belong in this object. Use Databricks secret scopes for them.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Protocol


class SparkConfLike(Protocol):
    """Small protocol that keeps this module importable without PySpark."""

    def get(self, key: str, default: str | None = None) -> str | None: ...


class SparkSessionLike(Protocol):
    conf: SparkConfLike


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Resolved names, locations, source endpoints, and business boundaries."""

    catalog: str = "nyc_mobility"
    landing_schema: str = "nyc_group_c"
    landing_volume: str = "nyc_source_files"
    landing_path_override: str | None = None
    bronze_schema: str = "nyc_bronze"
    silver_schema: str = "nyc_silver"
    gold_schema: str = "nyc_gold"
    quality_schema: str = "nyc_quality"
    timezone: str = "America/New_York"
    analysis_start_date: str = "2026-03-01"
    analysis_end_date: str = "2026-05-31"
    weather_source_url: str = "https://archive-api.open-meteo.com/v1/archive"
    green_taxi_base_url: str = "https://d37ci6vzurychx.cloudfront.net/trip-data"
    taxi_zones_source_url: str = (
        "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
    )

    def __post_init__(self) -> None:
        for field_name in (
            "catalog",
            "landing_schema",
            "landing_volume",
            "bronze_schema",
            "silver_schema",
            "gold_schema",
            "quality_schema",
        ):
            value = getattr(self, field_name)
            if not _IDENTIFIER.fullmatch(value):
                raise ValueError(
                    f"{field_name} must be a valid unquoted identifier: {value!r}"
                )

        start = date.fromisoformat(self.analysis_start_date)
        end = date.fromisoformat(self.analysis_end_date)
        if start > end:
            raise ValueError("analysis_start_date must not be after analysis_end_date")
        if self.landing_path_override and not self.landing_path_override.startswith(
            "/"
        ):
            raise ValueError("landing_path_override must be an absolute path")

    @property
    def landing_path(self) -> str:
        if self.landing_path_override:
            return self.landing_path_override.rstrip("/")
        return (
            f"/Volumes/{self.catalog}/{self.landing_schema}/"
            f"{self.landing_volume}/landing"
        )

    def table(self, layer: str, table_name: str) -> str:
        """Return a fully qualified table name for a medallion layer."""
        schema_by_layer = {
            "bronze": self.bronze_schema,
            "silver": self.silver_schema,
            "gold": self.gold_schema,
            "quality": self.quality_schema,
        }
        try:
            schema = schema_by_layer[layer]
        except KeyError as error:
            raise ValueError(f"Unsupported layer: {layer!r}") from error
        if not _IDENTIFIER.fullmatch(table_name):
            raise ValueError(f"Invalid table name: {table_name!r}")
        return f"{self.catalog}.{schema}.{table_name}"

    def monthly_date_ranges(self) -> tuple[tuple[str, str], ...]:
        """Return inclusive calendar-month ranges for the analysis window."""
        start = date.fromisoformat(self.analysis_start_date)
        end = date.fromisoformat(self.analysis_end_date)
        ranges: list[tuple[str, str]] = []
        current = start

        while current <= end:
            if current.month == 12:
                next_month = date(current.year + 1, 1, 1)
            else:
                next_month = date(current.year, current.month + 1, 1)
            month_end = min(end, date.fromordinal(next_month.toordinal() - 1))
            ranges.append((current.isoformat(), month_end.isoformat()))
            current = next_month

        return tuple(ranges)


_SETTINGS = {
    "catalog": ("nyc_mobility.catalog", "NYC_MOBILITY_CATALOG"),
    "landing_schema": (
        "nyc_mobility.landing_schema",
        "NYC_MOBILITY_LANDING_SCHEMA",
    ),
    "landing_volume": (
        "nyc_mobility.landing_volume",
        "NYC_MOBILITY_LANDING_VOLUME",
    ),
    "landing_path_override": (
        "nyc_mobility.landing_path",
        "NYC_MOBILITY_LANDING_PATH",
    ),
    "bronze_schema": ("nyc_mobility.bronze_schema", "NYC_MOBILITY_BRONZE_SCHEMA"),
    "silver_schema": ("nyc_mobility.silver_schema", "NYC_MOBILITY_SILVER_SCHEMA"),
    "gold_schema": ("nyc_mobility.gold_schema", "NYC_MOBILITY_GOLD_SCHEMA"),
    "quality_schema": (
        "nyc_mobility.quality_schema",
        "NYC_MOBILITY_QUALITY_SCHEMA",
    ),
    "timezone": ("nyc_mobility.timezone", "NYC_MOBILITY_TIMEZONE"),
    "analysis_start_date": (
        "nyc_mobility.analysis_start_date",
        "NYC_MOBILITY_ANALYSIS_START_DATE",
    ),
    "analysis_end_date": (
        "nyc_mobility.analysis_end_date",
        "NYC_MOBILITY_ANALYSIS_END_DATE",
    ),
    "weather_source_url": (
        "nyc_mobility.weather_source_url",
        "NYC_MOBILITY_WEATHER_SOURCE_URL",
    ),
    "green_taxi_base_url": (
        "nyc_mobility.green_taxi_base_url",
        "NYC_MOBILITY_GREEN_TAXI_BASE_URL",
    ),
    "taxi_zones_source_url": (
        "nyc_mobility.taxi_zones_source_url",
        "NYC_MOBILITY_TAXI_ZONES_SOURCE_URL",
    ),
}


def _spark_value(spark: SparkSessionLike | None, key: str) -> str | None:
    if spark is None:
        return None
    try:
        value = spark.conf.get(key, None)
    except (AttributeError, KeyError, TypeError):
        return None
    return value.strip() if isinstance(value, str) and value.strip() else None


def load_config(
    spark: SparkSessionLike | None = None,
    environ: dict[str, str] | None = None,
) -> PipelineConfig:
    """Resolve and validate project configuration.

    ``environ`` is injectable to make precedence and validation testable without
    mutating process-wide environment variables.
    """
    environment = os.environ if environ is None else environ
    defaults = PipelineConfig()
    resolved: dict[str, str | None] = {}

    for field_name, (spark_key, env_key) in _SETTINGS.items():
        spark_value = _spark_value(spark, spark_key)
        env_value = environment.get(env_key)
        if isinstance(env_value, str):
            env_value = env_value.strip() or None
        resolved[field_name] = (
            spark_value
            if spark_value is not None
            else env_value
            if env_value is not None
            else getattr(defaults, field_name)
        )

    return PipelineConfig(**resolved)


CONFIG = load_config()
