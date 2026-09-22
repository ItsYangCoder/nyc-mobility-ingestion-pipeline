# Databricks notebook source
# MAGIC %md
# MAGIC # NYC Mobility environment setup
# MAGIC Creates idempotent Unity Catalog schemas and verifies the configured
# MAGIC landing volume path before source acquisition starts.

# COMMAND ----------

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
from nyc_mobility.sql import render_sql_file

configure_logging()
LOGGER = get_logger("notebooks.setup")
CONFIG = load_notebook_config(dbutils, spark)

# COMMAND ----------

setup_path = repo_root / "src" / "sql" / "00_setup" / "00_setup.sql"
setup_sql = render_sql_file(setup_path, CONFIG)
for statement in setup_sql.split(";"):
    if statement.strip():
        spark.sql(statement)

log_event(
    LOGGER,
    logging.INFO,
    "setup.schemas_ready",
    "Unity Catalog schemas are ready",
    catalog=CONFIG.catalog,
    schemas=[
        CONFIG.bronze_schema,
        CONFIG.silver_schema,
        CONFIG.gold_schema,
        CONFIG.quality_schema,
    ],
)

# COMMAND ----------

try:
    dbutils.fs.ls(CONFIG.landing_path)
except Exception as error:
    log_event(
        LOGGER,
        logging.ERROR,
        "setup.landing_unavailable",
        "Configured landing path is unavailable",
        landing_path=CONFIG.landing_path,
        error=str(error),
        exc_info=True,
    )
    raise RuntimeError(
        "The external landing volume must exist and be accessible before "
        f"deployment runs: {CONFIG.landing_path}"
    ) from error

log_event(
    LOGGER,
    logging.INFO,
    "setup.completed",
    "Environment setup completed",
    landing_path=CONFIG.landing_path,
)
