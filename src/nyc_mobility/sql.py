"""Controlled SQL rendering for environment-specific identifiers and dates."""

from __future__ import annotations

import argparse
from pathlib import Path

from nyc_mobility.config import PipelineConfig, load_config


def _sql_string(value: str) -> str:
    return value.replace("'", "''")


def render_sql(sql: str, config: PipelineConfig) -> str:
    """Render checked-in default SQL for a validated target configuration."""
    defaults = PipelineConfig()
    replacements = {
        f"{defaults.catalog}.{defaults.bronze_schema}": (
            f"{config.catalog}.{config.bronze_schema}"
        ),
        f"{defaults.catalog}.{defaults.silver_schema}": (
            f"{config.catalog}.{config.silver_schema}"
        ),
        f"{defaults.catalog}.{defaults.gold_schema}": (
            f"{config.catalog}.{config.gold_schema}"
        ),
        f"{defaults.catalog}.{defaults.quality_schema}": (
            f"{config.catalog}.{config.quality_schema}"
        ),
        f"CREATE CATALOG IF NOT EXISTS {defaults.catalog}": (
            f"CREATE CATALOG IF NOT EXISTS {config.catalog}"
        ),
        f"USE CATALOG {defaults.catalog}": f"USE CATALOG {config.catalog}",
        f"CREATE SCHEMA IF NOT EXISTS {defaults.bronze_schema}": (
            f"CREATE SCHEMA IF NOT EXISTS {config.bronze_schema}"
        ),
        f"CREATE SCHEMA IF NOT EXISTS {defaults.silver_schema}": (
            f"CREATE SCHEMA IF NOT EXISTS {config.silver_schema}"
        ),
        f"CREATE SCHEMA IF NOT EXISTS {defaults.gold_schema}": (
            f"CREATE SCHEMA IF NOT EXISTS {config.gold_schema}"
        ),
        f"CREATE SCHEMA IF NOT EXISTS {defaults.quality_schema}": (
            f"CREATE SCHEMA IF NOT EXISTS {config.quality_schema}"
        ),
        f"DATE '{defaults.analysis_start_date}'": (
            f"DATE '{config.analysis_start_date}'"
        ),
        f"DATE '{defaults.analysis_end_date}'": f"DATE '{config.analysis_end_date}'",
        f"'{_sql_string(defaults.timezone)}'": f"'{_sql_string(config.timezone)}'",
        "m.covered_months = 3": (f"m.covered_months = {config.analysis_month_count}"),
        "s.in_window_hours = 2208": (
            f"s.in_window_hours = {config.expected_weather_hours}"
        ),
        "SELECT 'weather', COUNT(*), 3": (
            f"SELECT 'weather', COUNT(*), {config.analysis_month_count}"
        ),
    }
    rendered = sql
    for source, target in sorted(
        replacements.items(), key=lambda item: len(item[0]), reverse=True
    ):
        rendered = rendered.replace(source, target)
    return rendered


def render_sql_file(path: Path, config: PipelineConfig) -> str:
    """Read and render a UTF-8 SQL file."""
    return render_sql(path.read_text(encoding="utf-8"), config)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render NYC Mobility SQL for the configured environment."
    )
    parser.add_argument("path", type=Path, help="SQL file to render")
    parser.add_argument("--output", type=Path, help="optional rendered output path")
    args = parser.parse_args()

    rendered = render_sql_file(args.path, load_config())
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
