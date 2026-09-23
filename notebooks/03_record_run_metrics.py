# Databricks notebook source
# MAGIC %md
# MAGIC # NYC Mobility run monitoring
# MAGIC
# MAGIC Normalizes immediate Jobs API or task parameters for logs and task
# MAGIC values. Durable execution history remains in `system.lakeflow`; this
# MAGIC notebook does not copy platform job metadata into another table.

# COMMAND ----------

import json
import logging
import sys
from pathlib import Path

repo_root = next(
    (
        candidate
        for candidate in (Path.cwd(), Path.cwd().parent)
        if (candidate / "src" / "nyc_mobility").is_dir()
    ),
    None,
)
if repo_root is None:
    raise RuntimeError("Cannot locate the deployed bundle root.")

sys.path.insert(0, str(repo_root / "src"))

from nyc_mobility.config import load_notebook_config
from nyc_mobility.logging import configure_logging, get_logger, log_event
from nyc_mobility.monitoring import (
    aggregate_quality_status,
    assess_freshness,
    normalize_job_run,
)

configure_logging()
LOGGER = get_logger("notebooks.record_run_metrics")
CONFIG = load_notebook_config(dbutils, spark)


def parameter(name, default=None):
    try:
        value = dbutils.widgets.get(name)
    except Exception:
        value = None
    return value.strip() if isinstance(value, str) and value.strip() else default


def optional_integer(name):
    value = parameter(name)
    return int(value) if value is not None else None


def run_payload():
    serialized = parameter("run_payload_json")
    if serialized:
        payload = json.loads(serialized)
        if not isinstance(payload, dict):
            raise ValueError("run_payload_json must contain a JSON object")
        return payload
    return {
        "job_id": parameter("job_id"),
        "run_id": parameter("run_id"),
        "task_key": parameter("task_key"),
        "start_time": optional_integer("start_time_ms"),
        "end_time": optional_integer("end_time_ms"),
        "attempt_number": parameter("attempt_number", "0"),
        "run_page_url": parameter("run_page_url"),
        "state": {
            "life_cycle_state": parameter("life_cycle_state"),
            "result_state": parameter("result_state"),
            "state_message": parameter("error_message"),
            "termination_code": parameter("termination_code"),
        },
    }


AUDIT = normalize_job_run(run_payload())
FRESHNESS = assess_freshness(
    parameter("actual_through"),
    CONFIG.analysis_end_date,
    tolerance_days=int(parameter("freshness_tolerance_days", "0")),
)
DQ_STATUS = aggregate_quality_status(
    [item for item in parameter("dq_outcomes", "").split(",") if item.strip()]
)
SUMMARY = {
    "run": AUDIT.as_dict(),
    "freshness": FRESHNESS.as_dict(),
    "dq_status": DQ_STATUS.value,
    "source": "jobs_api_or_task_parameters",
}

try:
    dbutils.jobs.taskValues.set(key="run_audit_summary", value=json.dumps(SUMMARY))
except Exception as error:
    log_event(
        LOGGER,
        logging.WARNING,
        "monitoring.task_value_unavailable",
        "Monitoring summary could not be published as a task value",
        error=str(error),
    )

log_event(
    LOGGER,
    logging.INFO,
    "monitoring.run_normalized",
    "Workflow run metadata normalized for immediate monitoring",
    **SUMMARY,
)
