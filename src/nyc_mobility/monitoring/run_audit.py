"""Normalize Databricks workflow metadata for operational monitoring."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELED = "CANCELED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"


class FreshnessStatus(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class QualityStatus(StrEnum):
    PASS = "PASS"  # nosec B105
    WARN = "WARN"
    FAIL = "FAIL"
    ERROR = "ERROR"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True, slots=True)
class RunAuditRecord:
    job_id: str | None
    run_id: str
    task_key: str | None
    status: str
    started_at: str | None
    ended_at: str | None
    duration_seconds: int | None
    retry_count: int
    failed_task: str | None
    termination_code: str | None
    error_message: str | None
    run_page_url: str | None
    git_commit: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FreshnessResult:
    expected_through: str
    actual_through: str | None
    tolerance_days: int
    status: str
    lag_days: int | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


_STATUS_MAP = {
    "BLOCKED": RunStatus.QUEUED,
    "PENDING": RunStatus.QUEUED,
    "QUEUED": RunStatus.QUEUED,
    "RUNNING": RunStatus.RUNNING,
    "TERMINATING": RunStatus.RUNNING,
    "SUCCESS": RunStatus.SUCCEEDED,
    "SUCCEEDED": RunStatus.SUCCEEDED,
    "ERROR": RunStatus.FAILED,
    "FAILED": RunStatus.FAILED,
    "INTERNAL_ERROR": RunStatus.FAILED,
    "TIMEDOUT": RunStatus.TIMED_OUT,
    "TIMED_OUT": RunStatus.TIMED_OUT,
    "CANCELED": RunStatus.CANCELED,
    "CANCELLED": RunStatus.CANCELED,
    "SKIPPED": RunStatus.SKIPPED,
    "UPSTREAM_FAILED": RunStatus.SKIPPED,
}
_SECRET = re.compile(
    r"(?i)\b(token|password|secret|authorization|api[_-]?key)\b\s*[:=]\s*([^\s,;]+)"
)


def normalize_status(result_state: Any, life_cycle_state: Any = None) -> RunStatus:
    """Map Databricks result and lifecycle states to dashboard statuses."""
    for value in (result_state, life_cycle_state):
        normalized = str(value or "").strip().upper().replace(" ", "_")
        if normalized in _STATUS_MAP:
            return _STATUS_MAP[normalized]
    return RunStatus.UNKNOWN


def sanitize_error_message(message: Any, max_length: int = 1000) -> str | None:
    """Remove common inline credentials and bound stored error context."""
    if message is None:
        return None
    sanitized = _SECRET.sub(lambda match: f"{match.group(1)}=[REDACTED]", str(message))
    sanitized = " ".join(sanitized.split())
    return sanitized[:max_length] or None


def normalize_job_run(payload: Mapping[str, Any]) -> RunAuditRecord:
    """Normalize one Databricks Jobs API run without persisting a duplicate."""
    run_id = _required_text(payload.get("run_id"), "run_id")
    state = payload.get("state") if isinstance(payload.get("state"), Mapping) else {}
    status = normalize_status(state.get("result_state"), state.get("life_cycle_state"))
    tasks = payload.get("tasks") if isinstance(payload.get("tasks"), Sequence) else ()
    failed_task, task_error = _failed_task(tasks)
    started_at = _timestamp(payload.get("start_time"))
    ended_at = _timestamp(payload.get("end_time"))
    error = task_error or state.get("state_message")

    return RunAuditRecord(
        job_id=_text(payload.get("job_id")),
        run_id=run_id,
        task_key=_text(payload.get("task_key")),
        status=status.value,
        started_at=_isoformat(started_at),
        ended_at=_isoformat(ended_at),
        duration_seconds=_duration_seconds(started_at, ended_at),
        retry_count=_nonnegative_int(
            payload.get("attempt_number", payload.get("repair_id", 0))
        ),
        failed_task=failed_task,
        termination_code=_text(
            state.get("termination_code", state.get("result_state"))
        ),
        error_message=sanitize_error_message(error),
        run_page_url=_safe_url(payload.get("run_page_url")),
        git_commit=_git_commit(payload),
    )


def assess_freshness(
    actual_through: date | str | None,
    expected_through: date | str,
    tolerance_days: int = 0,
) -> FreshnessResult:
    """Compare dataset coverage with the configured historical window."""
    if tolerance_days < 0:
        raise ValueError("tolerance_days must be nonnegative")
    expected = _date(expected_through, "expected_through")
    actual = _date(actual_through, "actual_through") if actual_through else None
    if actual is None:
        return FreshnessResult(
            expected.isoformat(),
            None,
            tolerance_days,
            FreshnessStatus.UNKNOWN.value,
            None,
        )
    lag_days = (expected - actual).days
    status = (
        FreshnessStatus.FRESH if lag_days <= tolerance_days else FreshnessStatus.STALE
    )
    return FreshnessResult(
        expected.isoformat(), actual.isoformat(), tolerance_days, status.value, lag_days
    )


def aggregate_quality_status(outcomes: Sequence[str]) -> QualityStatus:
    """Return the most severe quality outcome without inventing a pass."""
    normalized = {str(outcome).strip().upper() for outcome in outcomes}
    if not normalized:
        return QualityStatus.NOT_EVALUATED
    for status in (
        QualityStatus.ERROR,
        QualityStatus.FAIL,
        QualityStatus.WARN,
        QualityStatus.PASS,
    ):
        if status.value in normalized:
            return status
    return QualityStatus.NOT_EVALUATED


def failure_rate(records: Sequence[RunAuditRecord]) -> tuple[int, int, float | None]:
    """Calculate failures per distinct completed parent run."""
    latest_by_run: dict[str, RunAuditRecord] = {}
    for record in records:
        current = latest_by_run.get(record.run_id)
        if current is None or (record.ended_at or "") >= (current.ended_at or ""):
            latest_by_run[record.run_id] = record
    completed = [
        record
        for record in latest_by_run.values()
        if record.status
        in {
            RunStatus.SUCCEEDED.value,
            RunStatus.FAILED.value,
            RunStatus.TIMED_OUT.value,
            RunStatus.CANCELED.value,
        }
    ]
    failures = sum(
        record.status in {RunStatus.FAILED.value, RunStatus.TIMED_OUT.value}
        for record in completed
    )
    return failures, len(completed), failures / len(completed) if completed else None


def _failed_task(tasks: Sequence[Any]) -> tuple[str | None, Any]:
    for task in tasks:
        if not isinstance(task, Mapping):
            continue
        state = task.get("state") if isinstance(task.get("state"), Mapping) else {}
        status = normalize_status(
            state.get("result_state"), state.get("life_cycle_state")
        )
        if status in {RunStatus.FAILED, RunStatus.TIMED_OUT}:
            return _text(task.get("task_key")), state.get("state_message")
    return None, None


def _git_commit(payload: Mapping[str, Any]) -> str | None:
    metadata = payload.get("git_source")
    if not isinstance(metadata, Mapping):
        return None
    return _text(metadata.get("git_commit"))


def _timestamp(value: Any) -> datetime | None:
    if value in (None, "", 0, "0"):
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (TypeError, ValueError, OSError) as error:
        raise ValueError(f"Invalid timestamp in milliseconds: {value!r}") from error


def _duration_seconds(
    started_at: datetime | None, ended_at: datetime | None
) -> int | None:
    if started_at is None or ended_at is None:
        return None
    return max(0, int((ended_at - started_at).total_seconds()))


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat().replace("+00:00", "Z") if value else None


def _date(value: date | str, field_name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as error:
        raise ValueError(f"{field_name} must be an ISO date") from error


def _text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _required_text(value: Any, field_name: str) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"{field_name} is required")
    return text


def _nonnegative_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"retry count must be an integer: {value!r}") from error
    if number < 0:
        raise ValueError("retry count must be nonnegative")
    return number


def _safe_url(value: Any) -> str | None:
    url = _text(value)
    return url if url and url.startswith("https://") else None
