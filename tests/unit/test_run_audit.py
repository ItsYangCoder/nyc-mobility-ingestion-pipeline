from dataclasses import replace

import pytest

from nyc_mobility.monitoring import (
    QualityStatus,
    RunStatus,
    aggregate_quality_status,
    assess_freshness,
    failure_rate,
    normalize_job_run,
    normalize_status,
    sanitize_error_message,
)


def test_normalize_successful_job_run():
    record = normalize_job_run(
        {
            "job_id": 11,
            "run_id": 101,
            "start_time": 1_790_000_000_000,
            "end_time": 1_790_000_045_000,
            "attempt_number": 1,
            "run_page_url": "https://workspace.example/jobs/11/runs/101",
            "state": {
                "life_cycle_state": "TERMINATED",
                "result_state": "SUCCESS",
            },
            "git_source": {"git_commit": "abc123"},
        }
    )

    assert record.job_id == "11"
    assert record.run_id == "101"
    assert record.status == RunStatus.SUCCEEDED
    assert record.duration_seconds == 45
    assert record.retry_count == 1
    assert record.git_commit == "abc123"
    assert record.failed_task is None


def test_normalize_failed_run_uses_failed_task_and_sanitizes_message():
    record = normalize_job_run(
        {
            "run_id": "failed-1",
            "start_time": 1_790_000_000_000,
            "end_time": 1_790_000_010_000,
            "state": {"result_state": "FAILED", "state_message": "parent failed"},
            "tasks": [
                {
                    "task_key": "refresh_medallion_pipeline",
                    "state": {
                        "result_state": "FAILED",
                        "state_message": "password=hunter2 connection failed",
                    },
                }
            ],
        }
    )

    assert record.status == RunStatus.FAILED
    assert record.failed_task == "refresh_medallion_pipeline"
    assert record.error_message == "password=[REDACTED] connection failed"
    assert record.termination_code == "FAILED"


@pytest.mark.parametrize(
    ("result_state", "life_cycle_state", "expected"),
    [
        (None, "RUNNING", RunStatus.RUNNING),
        (None, "QUEUED", RunStatus.QUEUED),
        ("ERROR", "TERMINATED", RunStatus.FAILED),
        ("TIMEDOUT", "TERMINATED", RunStatus.TIMED_OUT),
        (None, None, RunStatus.UNKNOWN),
    ],
)
def test_normalize_status(result_state, life_cycle_state, expected):
    assert normalize_status(result_state, life_cycle_state) == expected


def test_missing_run_id_is_rejected():
    with pytest.raises(ValueError, match="run_id is required"):
        normalize_job_run({"state": {"life_cycle_state": "RUNNING"}})


def test_missing_metrics_remain_unknown():
    record = normalize_job_run({"run_id": 10, "state": {}})

    assert record.status == RunStatus.UNKNOWN
    assert record.started_at is None
    assert record.ended_at is None
    assert record.duration_seconds is None
    assert record.error_message is None


def test_historical_freshness_uses_expected_window_not_today():
    result = assess_freshness("2026-05-31", "2026-05-31")

    assert result.status == "FRESH"
    assert result.lag_days == 0


def test_freshness_supports_tolerance_and_unknown_metrics():
    tolerated = assess_freshness("2026-05-30", "2026-05-31", tolerance_days=1)
    unavailable = assess_freshness(None, "2026-05-31")

    assert tolerated.status == "FRESH"
    assert tolerated.lag_days == 1
    assert unavailable.status == "UNKNOWN"
    assert unavailable.lag_days is None


def test_invalid_freshness_input_is_rejected():
    with pytest.raises(ValueError, match="nonnegative"):
        assess_freshness("2026-05-31", "2026-05-31", tolerance_days=-1)


def test_quality_summary_preserves_failures_and_unexecuted_state():
    assert aggregate_quality_status(["PASS", "WARN", "FAIL"]) == QualityStatus.FAIL
    assert aggregate_quality_status(["PASS", "ERROR"]) == QualityStatus.ERROR
    assert aggregate_quality_status([]) == QualityStatus.NOT_EVALUATED


def test_failure_rate_counts_distinct_runs_not_retry_rows():
    success = normalize_job_run(
        {
            "run_id": "1",
            "end_time": 1_790_000_010_000,
            "state": {"result_state": "SUCCESS"},
        }
    )
    failed_attempt = normalize_job_run(
        {
            "run_id": "2",
            "end_time": 1_790_000_020_000,
            "state": {"result_state": "FAILED"},
        }
    )
    repaired = replace(
        failed_attempt,
        status=RunStatus.SUCCEEDED.value,
        ended_at="2026-09-24T00:01:00Z",
        retry_count=1,
    )
    running = normalize_job_run(
        {"run_id": "3", "state": {"life_cycle_state": "RUNNING"}}
    )

    assert failure_rate([success, failed_attempt, repaired, running]) == (0, 2, 0.0)


def test_failure_rate_reports_no_denominator_when_runs_are_incomplete():
    running = normalize_job_run(
        {"run_id": "3", "state": {"life_cycle_state": "RUNNING"}}
    )

    assert failure_rate([running]) == (0, 0, None)


def test_error_sanitization_is_bounded_and_rejects_unsafe_url():
    record = normalize_job_run(
        {"run_id": "4", "run_page_url": "http://unsafe.example", "state": {}}
    )

    assert sanitize_error_message("token=abc " + "x" * 20, max_length=18) == (
        "token=[REDACTED] x"
    )
    assert record.run_page_url is None
