from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from nyc_mobility.config import PipelineConfig
from nyc_mobility.quality.runner import (
    Evaluation,
    Outcome,
    QualityGateFailed,
    QualityRule,
    Severity,
    default_rules,
    execute_rule,
    run_and_persist,
    run_source_checks,
)


class FakeFrame:
    def __init__(self, rows=None):
        self.rows = rows or []

    def collect(self):
        return self.rows


class FakeSpark:
    def __init__(self, rows=None, query_error=None):
        self.rows = rows or []
        self.query_error = query_error
        self.queries = []

    def sql(self, query):
        self.queries.append(query)
        if query.lstrip().upper().startswith(("CREATE", "MERGE")):
            return FakeFrame()
        if self.query_error:
            raise self.query_error
        return FakeFrame(self.rows)


def make_rule(
    *,
    severity=Severity.CRITICAL,
    evaluation=Evaluation.ALL_STATUS_PASS,
    actual_field=None,
    expected_field=None,
    expected_value=None,
    failed_records_field=None,
):
    return QualityRule(
        rule_id="silver.example",
        layer="silver",
        dataset="example_table",
        sql_path=Path("tests/sql/silver/silver_key_uniqueness.sql"),
        severity=severity,
        evaluation=evaluation,
        actual_field=actual_field,
        expected_field=expected_field,
        expected_value=expected_value,
        failed_records_field=failed_records_field,
    )


def run_rule(spark, rule):
    return execute_rule(
        spark,
        rule,
        PipelineConfig(),
        run_id="run-10",
        attempt_id="0",
        checked_at=datetime(2026, 9, 22, 12, 0, tzinfo=UTC),
    )


def test_all_status_rows_pass():
    result = run_rule(
        FakeSpark([{"check_name": "key", "status": "PASS"}]),
        make_rule(),
    )

    assert result.outcome == Outcome.PASS
    assert result.failed_record_count == 0
    assert result.action == "CONTINUE"


def test_warning_violation_warns_without_stopping():
    result = run_rule(
        FakeSpark([{"actual_count": 8, "expected_count": 10}]),
        make_rule(
            severity=Severity.WARNING,
            evaluation=Evaluation.NO_ROWS,
            actual_field="actual_count",
            expected_field="expected_count",
        ),
    )

    assert result.outcome == Outcome.WARN
    assert result.actual_value == "8"
    assert result.expected_value == "10"
    assert result.failed_record_count == 1
    assert result.action == "WARN_AND_INVESTIGATE"


def test_critical_violation_fails_and_counts_failed_records():
    rows = [
        {"check_name": "pickup", "failures": 2, "status": "FAIL"},
        {"check_name": "dropoff", "failures": 3, "status": "FAIL"},
    ]
    result = run_rule(
        FakeSpark(rows),
        make_rule(
            actual_field="failures",
            expected_value="0",
            failed_records_field="failures",
        ),
    )

    assert result.outcome == Outcome.FAIL
    assert result.actual_value == "[2,3]"
    assert result.expected_value == "0"
    assert result.failed_record_count == 5
    assert result.action == "STOP_AND_INVESTIGATE"


def test_query_error_is_not_reported_as_pass():
    result = run_rule(
        FakeSpark(query_error=RuntimeError("table unavailable")), make_rule()
    )

    assert result.outcome == Outcome.ERROR
    assert result.error_message == "RuntimeError: table unavailable"
    assert result.action == "STOP_AND_INVESTIGATE"


def test_missing_rows_or_status_are_errors():
    empty = run_rule(FakeSpark(), make_rule())
    missing_status = run_rule(FakeSpark([{"count": 1}]), make_rule())

    assert empty.outcome == Outcome.ERROR
    assert empty.error_message == "Query returned no result rows."
    assert missing_status.outcome == Outcome.ERROR
    assert "missing 'status'" in missing_status.error_message


def test_configured_identifiers_are_rendered_before_execution():
    spark = FakeSpark([{"status": "PASS"}])
    config = PipelineConfig(catalog="configured", silver_schema="silver_target")
    rule = make_rule()

    execute_rule(spark, rule, config, "run", "0")

    assert "configured.silver_target.silver_green_taxi_trips" in spark.queries[0]
    assert "nyc_mobility.nyc_silver" not in spark.queries[0]


def test_result_identity_is_retry_safe_and_preserves_attempts():
    spark = FakeSpark([{"status": "PASS"}])
    rule = make_rule()

    first = execute_rule(spark, rule, PipelineConfig(), "run", "0")
    repeated = execute_rule(spark, rule, PipelineConfig(), "run", "0")
    repair = execute_rule(spark, rule, PipelineConfig(), "run", "1")

    assert first.result_id == repeated.result_id
    assert repair.result_id != first.result_id


def test_critical_results_are_persisted_before_gate_is_raised():
    spark = FakeSpark([{"status": "FAIL"}])
    rule = make_rule()

    with pytest.raises(QualityGateFailed) as error:
        run_and_persist(spark, [rule], PipelineConfig(), "run", "0")

    assert error.value.results[0].outcome == Outcome.FAIL
    merge = next(query for query in spark.queries if query.lstrip().startswith("MERGE"))
    assert "'FAIL'" in merge
    assert "nyc_mobility.nyc_quality.quality_results" in merge


def test_default_rule_catalogue_has_unique_existing_queries():
    rules = default_rules(Path("tests/sql"))

    assert len(rules) == len({rule.rule_id for rule in rules})
    assert all(rule.sql_path.is_file() for rule in rules)
    assert {rule.severity for rule in rules} == {
        Severity.WARNING,
        Severity.CRITICAL,
    }


def test_source_checks_reuse_ingestion_validators():
    start = datetime(2026, 3, 1)
    timestamps = [
        (start + timedelta(hours=offset)).isoformat() for offset in range(24)
    ]
    config = PipelineConfig(
        landing_path_override="/landing",
        analysis_start_date="2026-03-01",
        analysis_end_date="2026-03-01",
    )

    with (
        patch(
            "nyc_mobility.ingestion.green_taxi.inspect_parquet",
            return_value=(12, ["VendorID"]),
        ),
        patch(
            "nyc_mobility.ingestion.weather.validate_weather",
            return_value={"time": timestamps},
        ),
        patch(
            "nyc_mobility.ingestion.download_taxi_zones.profile_csv",
            return_value={"row_count": 265, "columns": ["LocationID"]},
        ),
        patch.object(Path, "read_text", return_value="{}"),
    ):
        results = run_source_checks(config, "run", "0")

    assert len(results) == 3
    assert all(result.outcome == Outcome.PASS for result in results)
    assert {result.dataset for result in results} == {
        "green_taxi",
        "weather",
        "taxi_zones",
    }


def test_invalid_source_is_a_visible_failure():
    config = PipelineConfig(
        landing_path_override="/landing",
        analysis_start_date="2026-03-01",
        analysis_end_date="2026-03-01",
    )

    with (
        patch(
            "nyc_mobility.ingestion.green_taxi.inspect_parquet",
            side_effect=ValueError("missing columns"),
        ),
        patch(
            "nyc_mobility.ingestion.weather.validate_weather",
            side_effect=ValueError("invalid weather"),
        ),
        patch(
            "nyc_mobility.ingestion.download_taxi_zones.profile_csv",
            side_effect=ValueError("duplicate LocationID"),
        ),
        patch.object(Path, "read_text", return_value="{}"),
    ):
        results = run_source_checks(config, "run", "0")

    assert all(result.outcome == Outcome.FAIL for result in results)
    assert all(result.action == "STOP_AND_INVESTIGATE" for result in results)
    assert all(result.error_message for result in results)
