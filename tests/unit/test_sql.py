from pathlib import Path

import pytest

from nyc_mobility.config import PipelineConfig
from nyc_mobility.sql import render_sql, render_sql_file


def test_render_sql_uses_validated_environment_and_window():
    config = PipelineConfig(
        catalog="mobility_dev",
        bronze_schema="bronze_dev",
        silver_schema="silver_dev",
        gold_schema="gold_dev",
        analysis_start_date="2027-11-01",
        analysis_end_date="2027-12-31",
        timezone="UTC",
    )
    sql = """
    SELECT * FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
    WHERE event_date BETWEEN DATE '2026-03-01' AND DATE '2026-05-31'
      AND timezone = 'America/New_York';
    SELECT * FROM nyc_mobility.nyc_gold.fact_taxi_trip;
    SELECT CASE WHEN m.covered_months = 3 THEN 'PASS' END;
    """

    rendered = render_sql(sql, config)

    assert "mobility_dev.bronze_dev.bronze_green_taxi_raw" in rendered
    assert "mobility_dev.gold_dev.fact_taxi_trip" in rendered
    assert "DATE '2027-11-01'" in rendered
    assert "DATE '2027-12-31'" in rendered
    assert "timezone = 'UTC'" in rendered
    assert "m.covered_months = 2" in rendered


def test_render_sql_file_reads_utf8(tmp_path: Path):
    path = tmp_path / "check.sql"
    path.write_text(
        "SELECT * FROM nyc_mobility.nyc_silver.silver_weather_hourly;",
        encoding="utf-8",
    )

    rendered = render_sql_file(
        path,
        PipelineConfig(catalog="configured", silver_schema="silver_target"),
    )

    assert "configured.silver_target.silver_weather_hourly" in rendered


def test_setup_sql_uses_configured_catalog_and_schemas():
    path = Path("src/sql/00_setup/00_setup.sql")
    config = PipelineConfig(
        catalog="configured",
        bronze_schema="bronze_target",
        silver_schema="silver_target",
        gold_schema="gold_target",
        quality_schema="quality_target",
    )

    rendered = render_sql_file(path, config)

    assert "CREATE CATALOG IF NOT EXISTS configured" in rendered
    assert "CREATE SCHEMA IF NOT EXISTS bronze_target" in rendered
    assert "CREATE SCHEMA IF NOT EXISTS silver_target" in rendered
    assert "CREATE SCHEMA IF NOT EXISTS gold_target" in rendered
    assert "CREATE SCHEMA IF NOT EXISTS quality_target" in rendered


def test_invalid_identifier_cannot_enter_rendered_sql():
    with pytest.raises(ValueError, match="valid unquoted identifier"):
        PipelineConfig(catalog="unsafe; DROP CATALOG")


def test_every_checked_in_sql_file_renders_non_default_configuration():
    defaults = PipelineConfig()
    config = PipelineConfig(
        catalog="mobility_test",
        bronze_schema="bronze_test",
        silver_schema="silver_test",
        gold_schema="gold_test",
        quality_schema="quality_test",
        analysis_start_date="2027-11-01",
        analysis_end_date="2027-12-31",
        timezone="UTC",
    )
    default_tokens = (
        f"{defaults.catalog}.{defaults.bronze_schema}",
        f"{defaults.catalog}.{defaults.silver_schema}",
        f"{defaults.catalog}.{defaults.gold_schema}",
        f"{defaults.catalog}.{defaults.quality_schema}",
        f"CREATE CATALOG IF NOT EXISTS {defaults.catalog}",
        f"USE CATALOG {defaults.catalog}",
        f"CREATE SCHEMA IF NOT EXISTS {defaults.bronze_schema}",
        f"CREATE SCHEMA IF NOT EXISTS {defaults.silver_schema}",
        f"CREATE SCHEMA IF NOT EXISTS {defaults.gold_schema}",
        f"CREATE SCHEMA IF NOT EXISTS {defaults.quality_schema}",
        f"DATE '{defaults.analysis_start_date}'",
        f"DATE '{defaults.analysis_end_date}'",
        f"'{defaults.timezone}'",
        "m.covered_months = 3",
        "s.in_window_hours = 2208",
        "SELECT 'weather', COUNT(*), 3",
    )
    sql_paths = sorted(Path("src/sql").rglob("*.sql")) + sorted(
        Path("tests/sql").rglob("*.sql")
    )

    assert sql_paths
    for path in sql_paths:
        source = path.read_text(encoding="utf-8")
        rendered = render_sql(source, config)
        for token in default_tokens:
            if token in source:
                assert token not in rendered, f"{path} retained default token {token!r}"
