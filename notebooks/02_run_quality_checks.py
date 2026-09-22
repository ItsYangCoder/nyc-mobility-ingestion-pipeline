# Databricks notebook source
# MAGIC %md
# MAGIC # NYC Mobility runtime data-quality checks
# MAGIC Executes the checked-in quality-rule catalogue after the medallion
# MAGIC refresh, persists every result, and stops on critical failures.

# COMMAND ----------

import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path
from uuid import uuid4

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
from nyc_mobility.quality import (
    QualityGateFailed,
    default_rules,
    enforce_quality_gate,
    persist_results,
    run_quality_checks,
    run_source_checks,
)

configure_logging()
LOGGER = get_logger("notebooks.run_quality_checks")
CONFIG = load_notebook_config(dbutils, spark)
RULES = default_rules(repo_root / "tests" / "sql")


def parameter(name, default=None):
    try:
        value = dbutils.widgets.get(name)
    except Exception:
        value = None
    return value.strip() if isinstance(value, str) and value.strip() else default


RUN_ID = parameter("run_id", os.getenv("DATABRICKS_JOB_RUN_ID") or str(uuid4()))
ATTEMPT_ID = parameter(
    "attempt_id", os.getenv("DATABRICKS_JOB_REPAIR_COUNT") or "0"
)
SELECTED_LAYERS = {
    layer.strip().lower()
    for layer in parameter("layers", "source,bronze,silver,gold").split(",")
    if layer.strip()
}
SUPPORTED_LAYERS = {"source", "bronze", "silver", "gold"}
if not SELECTED_LAYERS or not SELECTED_LAYERS <= SUPPORTED_LAYERS:
    raise ValueError(
        f"layers must contain only {sorted(SUPPORTED_LAYERS)}; "
        f"received {sorted(SELECTED_LAYERS)}"
    )

# COMMAND ----------


def summarize(results):
    counts = Counter(result.outcome for result in results)
    return {
        "run_id": RUN_ID,
        "attempt_id": ATTEMPT_ID,
        "layers": sorted(SELECTED_LAYERS),
        "result_table": CONFIG.table("quality", "quality_results"),
        "outcomes": dict(sorted(counts.items())),
        "failed_rules": [
            result.rule_id for result in results if result.outcome in {"FAIL", "ERROR"}
        ],
    }


def publish_summary(summary):
    try:
        dbutils.jobs.taskValues.set(key="quality_summary", value=json.dumps(summary))
    except Exception as error:
        log_event(
            LOGGER,
            logging.WARNING,
            "quality.task_value_unavailable",
            "Quality summary could not be published as a task value",
            error=str(error),
        )


try:
    RESULTS = []
    if "source" in SELECTED_LAYERS:
        RESULTS.extend(run_source_checks(CONFIG, RUN_ID, ATTEMPT_ID))
    SQL_RULES = [rule for rule in RULES if rule.layer in SELECTED_LAYERS]
    RESULTS.extend(run_quality_checks(spark, SQL_RULES, CONFIG, RUN_ID, ATTEMPT_ID))
    persist_results(spark, RESULTS, CONFIG)
    enforce_quality_gate(RESULTS)
except QualityGateFailed as error:
    RESULTS = list(error.results)
    SUMMARY = summarize(RESULTS)
    publish_summary(SUMMARY)
    log_event(
        LOGGER,
        logging.ERROR,
        "quality.failed",
        "Critical data-quality checks failed",
        **SUMMARY,
    )
    raise

SUMMARY = summarize(RESULTS)
publish_summary(SUMMARY)
log_event(
    LOGGER,
    logging.INFO,
    "quality.completed",
    "Runtime data-quality checks completed",
    **SUMMARY,
)
