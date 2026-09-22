"""Execute SQL data-quality rules and persist their outcomes."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol
from uuid import NAMESPACE_URL, uuid5

from nyc_mobility.config import PipelineConfig
from nyc_mobility.sql import render_sql_file


class Severity(StrEnum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Outcome(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ERROR = "ERROR"


class Evaluation(StrEnum):
    ALL_STATUS_PASS = "all_status_pass"
    NO_ROWS = "no_rows"


class DataFrameLike(Protocol):
    def collect(self) -> Sequence[Any]: ...


class SparkLike(Protocol):
    def sql(self, query: str) -> DataFrameLike: ...


@dataclass(frozen=True, slots=True)
class QualityRule:
    rule_id: str
    layer: str
    dataset: str
    sql_path: Path
    severity: Severity
    evaluation: Evaluation = Evaluation.ALL_STATUS_PASS
    status_column: str = "status"
    actual_field: str | None = None
    expected_field: str | None = None
    expected_value: str | None = None
    failed_records_field: str | None = None


@dataclass(frozen=True, slots=True)
class QualityResult:
    result_id: str
    run_id: str
    attempt_id: str
    layer: str
    dataset: str
    rule_id: str
    severity: str
    outcome: str
    checked_at: str
    actual_value: str | None
    expected_value: str | None
    failed_record_count: int | None
    metrics_json: str | None
    error_message: str | None
    action: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class QualityGateFailed(RuntimeError):
    """Raised after critical quality results have been persisted."""

    def __init__(self, results: Sequence[QualityResult]) -> None:
        self.results = tuple(results)
        failed = [result.rule_id for result in results if _stops_pipeline(result)]
        super().__init__(f"Critical data-quality checks failed: {', '.join(failed)}")


def default_rules(sql_root: Path) -> tuple[QualityRule, ...]:
    """Return the production rule catalogue backed by checked-in SQL."""
    return (
        QualityRule(
            "bronze.expected_source_counts",
            "bronze",
            "all_sources",
            sql_root / "bronze" / "03_expected_source_counts.sql",
            Severity.WARNING,
            evaluation=Evaluation.NO_ROWS,
            actual_field="actual_count",
            expected_field="expected_count",
        ),
        QualityRule(
            "bronze.lineage",
            "bronze",
            "all_sources",
            sql_root / "bronze" / "02_bronze_lineage_checks.sql",
            Severity.CRITICAL,
        ),
        QualityRule(
            "silver.weather_structure",
            "silver",
            "silver_weather_hourly",
            sql_root / "silver" / "03_weather_validation.sql",
            Severity.CRITICAL,
            actual_field="actual_hourly_rows",
            expected_field="expected_hourly_rows",
        ),
        QualityRule(
            "silver.key_uniqueness",
            "silver",
            "all_silver_tables",
            sql_root / "silver" / "silver_key_uniqueness.sql",
            Severity.CRITICAL,
        ),
        QualityRule(
            "silver.date_coverage",
            "silver",
            "taxi_and_weather",
            sql_root / "silver" / "silver_date_coverage.sql",
            Severity.CRITICAL,
            actual_field="failures",
            expected_value="0",
            failed_records_field="failures",
        ),
        QualityRule(
            "silver.referential_integrity",
            "silver",
            "silver_green_taxi_trips",
            sql_root / "silver" / "silver_referential_integrity.sql",
            Severity.CRITICAL,
            actual_field="orphan_keys",
            expected_value="0",
            failed_records_field="orphan_keys",
        ),
        QualityRule(
            "silver.row_reconciliation",
            "silver",
            "all_silver_tables",
            sql_root / "silver" / "bronze_silver_reconciliation.sql",
            Severity.CRITICAL,
            actual_field="actual_rows",
            expected_field="expected_rows",
        ),
        QualityRule(
            "silver.measure_reconciliation",
            "silver",
            "silver_green_taxi_trips",
            sql_root / "silver" / "silver_measure_reconciliation.sql",
            Severity.CRITICAL,
            actual_field="silver_rows",
            expected_field="bronze_rows",
        ),
        QualityRule(
            "gold.key_uniqueness",
            "gold",
            "all_gold_tables",
            sql_root / "gold" / "gold_key_uniqueness.sql",
            Severity.CRITICAL,
        ),
        QualityRule(
            "gold.referential_integrity",
            "gold",
            "all_gold_tables",
            sql_root / "gold" / "gold_referential_integrity.sql",
            Severity.CRITICAL,
        ),
        QualityRule(
            "gold.row_reconciliation",
            "gold",
            "fact_tables",
            sql_root / "gold" / "silver_gold_reconciliation.sql",
            Severity.CRITICAL,
            actual_field="gold_rows",
            expected_field="eligible_silver_rows",
        ),
        QualityRule(
            "gold.measure_reconciliation",
            "gold",
            "fact_taxi_trip",
            sql_root / "gold" / "gold_measure_reconciliation.sql",
            Severity.CRITICAL,
            actual_field="gold_rows",
            expected_field="eligible_silver_rows",
        ),
        QualityRule(
            "gold.taxi_weather_cardinality",
            "gold",
            "fact_taxi_trip",
            sql_root / "gold" / "taxi_weather_join_cardinality.sql",
            Severity.CRITICAL,
            actual_field="rows_after_join",
            expected_field="rows_before_join",
        ),
    )


def execute_rule(
    spark: SparkLike,
    rule: QualityRule,
    config: PipelineConfig,
    run_id: str,
    attempt_id: str,
    checked_at: datetime | None = None,
) -> QualityResult:
    """Run one rule and convert its query output into one result record."""
    timestamp = checked_at or datetime.now(UTC)
    try:
        sql = render_sql_file(rule.sql_path, config)
        rows = [_row_dict(row) for row in spark.sql(sql).collect()]
    except Exception as error:
        return _result(
            rule,
            run_id,
            attempt_id,
            timestamp,
            Outcome.ERROR,
            error_message=f"{type(error).__name__}: {error}",
        )

    if rule.evaluation == Evaluation.NO_ROWS:
        passed = not rows
        failing_rows = rows
    else:
        if not rows:
            return _result(
                rule,
                run_id,
                attempt_id,
                timestamp,
                Outcome.ERROR,
                error_message="Query returned no result rows.",
            )
        missing_status = [row for row in rows if rule.status_column not in row]
        if missing_status:
            return _result(
                rule,
                run_id,
                attempt_id,
                timestamp,
                Outcome.ERROR,
                metrics=rows,
                error_message=f"Query result is missing {rule.status_column!r}.",
            )
        failing_rows = [
            row
            for row in rows
            if str(row[rule.status_column]).strip().upper() != Outcome.PASS
        ]
        passed = not failing_rows

    outcome = Outcome.PASS if passed else _violation_outcome(rule.severity)
    return _result(
        rule,
        run_id,
        attempt_id,
        timestamp,
        outcome,
        metrics=rows,
        actual_value=_field_values(rows, rule.actual_field),
        expected_value=(
            _field_values(rows, rule.expected_field) or rule.expected_value
        ),
        failed_record_count=_failed_record_count(
            failing_rows, rule.failed_records_field
        ),
    )


def run_quality_checks(
    spark: SparkLike,
    rules: Iterable[QualityRule],
    config: PipelineConfig,
    run_id: str,
    attempt_id: str,
    checked_at: datetime | None = None,
) -> list[QualityResult]:
    """Execute every selected rule without hiding later results after a failure."""
    return [
        execute_rule(spark, rule, config, run_id, attempt_id, checked_at)
        for rule in rules
    ]


def run_source_checks(
    config: PipelineConfig,
    run_id: str,
    attempt_id: str,
    checked_at: datetime | None = None,
) -> list[QualityResult]:
    """Validate configured landing files through the ingestion validators."""
    from nyc_mobility.ingestion.download_taxi_zones import profile_csv
    from nyc_mobility.ingestion.green_taxi import inspect_parquet
    from nyc_mobility.ingestion.weather import validate_weather

    timestamp = checked_at or datetime.now(UTC)
    landing = Path(config.landing_path)
    results: list[QualityResult] = []

    for month in config.analysis_months():
        path = landing / "green_taxi" / f"green_tripdata_{month}.parquet"
        rule = _source_rule(f"source.green_taxi.{month}", "green_taxi")
        try:
            row_count, columns = inspect_parquet(path)
            results.append(
                _result(
                    rule,
                    run_id,
                    attempt_id,
                    timestamp,
                    Outcome.PASS,
                    metrics=[
                        {
                            "path": str(path),
                            "row_count": row_count,
                            "columns": columns,
                        }
                    ],
                    actual_value=str(row_count),
                    expected_value=">0 with required columns",
                    failed_record_count=0,
                )
            )
        except Exception as error:
            results.append(
                _source_failure(rule, run_id, attempt_id, timestamp, path, error)
            )

    for start, end in config.monthly_date_ranges():
        path = landing / "weather" / f"weather_{start}_{end}.json"
        rule = _source_rule(f"source.weather.{start}_{end}", "weather")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            hourly = validate_weather(data)
            timestamps = hourly["time"]
            expected_hours = (
                date.fromisoformat(end) - date.fromisoformat(start) + timedelta(days=1)
            ).days * 24
            actual_dates = {
                datetime.fromisoformat(value.replace("Z", "+00:00")).date()
                for value in timestamps
            }
            if (
                len(timestamps) != expected_hours
                or min(actual_dates) != date.fromisoformat(start)
                or max(actual_dates) != date.fromisoformat(end)
            ):
                raise ValueError(
                    f"Expected {expected_hours} hourly positions covering "
                    f"{start} through {end}; received {len(timestamps)}."
                )
            results.append(
                _result(
                    rule,
                    run_id,
                    attempt_id,
                    timestamp,
                    Outcome.PASS,
                    metrics=[
                        {
                            "path": str(path),
                            "start_date": start,
                            "end_date": end,
                            "hourly_positions": len(timestamps),
                        }
                    ],
                    actual_value=str(len(timestamps)),
                    expected_value=str(expected_hours),
                    failed_record_count=0,
                )
            )
        except Exception as error:
            results.append(
                _source_failure(rule, run_id, attempt_id, timestamp, path, error)
            )

    path = landing / "taxi_zones" / "taxi_zone_lookup.csv"
    rule = _source_rule("source.taxi_zones", "taxi_zones")
    try:
        profile = profile_csv(path)
        results.append(
            _result(
                rule,
                run_id,
                attempt_id,
                timestamp,
                Outcome.PASS,
                metrics=[{"path": str(path), **profile}],
                actual_value=str(profile["row_count"]),
                expected_value=">0 with required columns and unique LocationID",
                failed_record_count=0,
            )
        )
    except Exception as error:
        results.append(
            _source_failure(rule, run_id, attempt_id, timestamp, path, error)
        )

    return results


def persist_results(
    spark: SparkLike,
    results: Iterable[QualityResult],
    config: PipelineConfig,
    table_name: str = "quality_results",
) -> None:
    """Create the result table and merge retry-safe rule records into it."""
    table = config.table("quality", table_name)
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.catalog}.{config.quality_schema}")
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            result_id STRING NOT NULL,
            run_id STRING NOT NULL,
            attempt_id STRING NOT NULL,
            layer STRING NOT NULL,
            dataset STRING NOT NULL,
            rule_id STRING NOT NULL,
            severity STRING NOT NULL,
            outcome STRING NOT NULL,
            checked_at TIMESTAMP NOT NULL,
            actual_value STRING,
            expected_value STRING,
            failed_record_count BIGINT,
            metrics_json STRING,
            error_message STRING,
            action STRING NOT NULL
        ) USING DELTA
        TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
        """
    )
    for result in results:
        spark.sql(_merge_sql(table, result))


def run_and_persist(
    spark: SparkLike,
    rules: Iterable[QualityRule],
    config: PipelineConfig,
    run_id: str,
    attempt_id: str,
) -> list[QualityResult]:
    """Run all checks, persist every result, then enforce the critical gate."""
    results = run_quality_checks(spark, rules, config, run_id, attempt_id)
    persist_results(spark, results, config)
    enforce_quality_gate(results)
    return results


def enforce_quality_gate(results: Sequence[QualityResult]) -> None:
    """Raise when a persisted result contains a critical failure or error."""
    if any(_stops_pipeline(result) for result in results):
        raise QualityGateFailed(results)


def _source_rule(rule_id: str, dataset: str) -> QualityRule:
    return QualityRule(
        rule_id=rule_id,
        layer="source",
        dataset=dataset,
        sql_path=Path(),
        severity=Severity.CRITICAL,
    )


def _source_failure(
    rule: QualityRule,
    run_id: str,
    attempt_id: str,
    checked_at: datetime,
    path: Path,
    error: Exception,
) -> QualityResult:
    expected_failures = (FileNotFoundError, ValueError, json.JSONDecodeError)
    outcome = Outcome.FAIL if isinstance(error, expected_failures) else Outcome.ERROR
    return _result(
        rule,
        run_id,
        attempt_id,
        checked_at,
        outcome,
        metrics=[{"path": str(path)}],
        failed_record_count=1,
        error_message=f"{type(error).__name__}: {error}",
    )


def _result(
    rule: QualityRule,
    run_id: str,
    attempt_id: str,
    checked_at: datetime,
    outcome: Outcome,
    *,
    metrics: Sequence[Mapping[str, Any]] | None = None,
    actual_value: str | None = None,
    expected_value: str | None = None,
    failed_record_count: int | None = None,
    error_message: str | None = None,
) -> QualityResult:
    result_id = str(
        uuid5(NAMESPACE_URL, f"nyc-mobility:{run_id}:{attempt_id}:{rule.rule_id}")
    )
    return QualityResult(
        result_id=result_id,
        run_id=run_id,
        attempt_id=attempt_id,
        layer=rule.layer,
        dataset=rule.dataset,
        rule_id=rule.rule_id,
        severity=rule.severity,
        outcome=outcome,
        checked_at=checked_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        actual_value=actual_value,
        expected_value=expected_value,
        failed_record_count=failed_record_count,
        metrics_json=(
            json.dumps(metrics, default=_json_default, sort_keys=True)
            if metrics
            else None
        ),
        error_message=error_message,
        action=_action(rule.severity, outcome),
    )


def _row_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    if hasattr(row, "asDict"):
        return dict(row.asDict(recursive=True))
    raise TypeError(f"Unsupported query row type: {type(row).__name__}")


def _field_values(rows: Sequence[Mapping[str, Any]], field: str | None) -> str | None:
    if not field or not rows or any(field not in row for row in rows):
        return None
    values = [row[field] for row in rows]
    value: Any = values[0] if len(values) == 1 else values
    return json.dumps(value, default=_json_default, separators=(",", ":"))


def _failed_record_count(
    rows: Sequence[Mapping[str, Any]], field: str | None
) -> int | None:
    if not rows:
        return 0
    if field and all(isinstance(row.get(field), int) for row in rows):
        return sum(abs(row[field]) for row in rows)
    return len(rows)


def _violation_outcome(severity: Severity) -> Outcome:
    return Outcome.WARN if severity == Severity.WARNING else Outcome.FAIL


def _action(severity: Severity, outcome: Outcome) -> str:
    if outcome == Outcome.PASS:
        return "CONTINUE"
    if severity == Severity.WARNING:
        return "WARN_AND_INVESTIGATE"
    return "STOP_AND_INVESTIGATE"


def _stops_pipeline(result: QualityResult) -> bool:
    return result.severity == Severity.CRITICAL and result.outcome in {
        Outcome.FAIL,
        Outcome.ERROR,
    }


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime, Decimal)):
        return str(value)
    return str(value)


def _sql_string(value: str | None) -> str:
    if value is None:
        return "CAST(NULL AS STRING)"
    return "'" + value.replace("'", "''") + "'"


def _sql_integer(value: int | None) -> str:
    return "CAST(NULL AS BIGINT)" if value is None else str(value)


def _merge_sql(table: str, result: QualityResult) -> str:
    values = [
        _sql_string(result.result_id),
        _sql_string(result.run_id),
        _sql_string(result.attempt_id),
        _sql_string(result.layer),
        _sql_string(result.dataset),
        _sql_string(result.rule_id),
        _sql_string(result.severity),
        _sql_string(result.outcome),
        f"CAST({_sql_string(result.checked_at)} AS TIMESTAMP)",
        _sql_string(result.actual_value),
        _sql_string(result.expected_value),
        _sql_integer(result.failed_record_count),
        _sql_string(result.metrics_json),
        _sql_string(result.error_message),
        _sql_string(result.action),
    ]
    columns = (
        "result_id, run_id, attempt_id, layer, dataset, rule_id, severity, "
        "outcome, checked_at, actual_value, expected_value, failed_record_count, "
        "metrics_json, error_message, action"
    )
    return f"""
        MERGE INTO {table} AS target
        USING (SELECT * FROM VALUES ({', '.join(values)}) AS source ({columns}))
        ON target.result_id = source.result_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """
