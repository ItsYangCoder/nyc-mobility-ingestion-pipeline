"""Unit tests for centralized runtime configuration."""

from types import SimpleNamespace

import pytest

from nyc_mobility.config import PipelineConfig, load_config


class FakeSparkConf:
    def __init__(self, values: dict[str, str]):
        self.values = values

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.values.get(key, default)


class UnavailableSparkConf:
    def get(self, key: str, default: str | None = None) -> str | None:
        raise RuntimeError("configuration unavailable")


def test_defaults_build_expected_paths_and_tables():
    config = PipelineConfig()

    assert config.landing_path == (
        "/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing"
    )
    assert config.table("silver", "silver_weather_hourly") == (
        "nyc_mobility.nyc_silver.silver_weather_hourly"
    )
    assert config.monthly_date_ranges() == (
        ("2026-03-01", "2026-03-31"),
        ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-31"),
    )


def test_environment_overrides_defaults():
    config = load_config(
        environ={
            "NYC_MOBILITY_CATALOG": "nyc_dev",
            "NYC_MOBILITY_LANDING_PATH": "/Volumes/custom/raw/landing",
            "NYC_MOBILITY_ANALYSIS_START_DATE": "2026-04-15",
            "NYC_MOBILITY_ANALYSIS_END_DATE": "2026-05-02",
        }
    )

    assert config.catalog == "nyc_dev"
    assert config.landing_path == "/Volumes/custom/raw/landing"
    assert config.monthly_date_ranges() == (
        ("2026-04-15", "2026-04-30"),
        ("2026-05-01", "2026-05-02"),
    )


def test_spark_configuration_has_highest_precedence():
    spark = SimpleNamespace(
        conf=FakeSparkConf(
            {
                "nyc_mobility.catalog": "nyc_spark",
                "nyc_mobility.silver_schema": "silver_spark",
            }
        )
    )

    config = load_config(
        spark=spark,
        environ={
            "NYC_MOBILITY_CATALOG": "nyc_env",
            "NYC_MOBILITY_SILVER_SCHEMA": "silver_env",
        },
    )

    assert config.catalog == "nyc_spark"
    assert config.silver_schema == "silver_spark"


def test_unavailable_spark_config_falls_back():
    spark = SimpleNamespace(conf=UnavailableSparkConf())

    config = load_config(
        spark=spark,
        environ={
            "NYC_MOBILITY_CATALOG": "nyc_env",
        },
    )

    assert config.catalog == "nyc_env"
    assert config.silver_schema == "nyc_silver"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"catalog": "bad-name"}, "valid unquoted identifier"),
        (
            {
                "analysis_start_date": "2026-06-01",
                "analysis_end_date": "2026-05-01",
            },
            "must not be after",
        ),
        ({"landing_path_override": "relative/path"}, "absolute path"),
    ],
)
def test_invalid_configuration_is_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        PipelineConfig(**kwargs)


def test_unknown_layer_and_invalid_table_are_rejected():
    config = PipelineConfig()

    with pytest.raises(ValueError, match="Unsupported layer"):
        config.table("staging", "weather")

    with pytest.raises(ValueError, match="Invalid table name"):
        config.table(
            "silver",
            "bad-table",
        )
