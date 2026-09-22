# Databricks notebook source
# MAGIC %md
# MAGIC # Group C raw landing
# MAGIC Downloads the three required NYC Mobility sources directly to the
# MAGIC external Unity Catalog volume backed by R2.

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
    raise RuntimeError("Open this notebook from the repository's notebooks folder.")

sys.path.insert(0, str(repo_root / "src"))

from nyc_mobility.config import load_notebook_config
from nyc_mobility.ingestion.download_taxi_zones import download_or_reuse
from nyc_mobility.ingestion.green_taxi import ingest_green_taxi
from nyc_mobility.ingestion.weather import download_weather
from nyc_mobility.logging import configure_logging, get_logger, log_event

configure_logging()
LOGGER = get_logger("notebooks.land_raw_sources")
CONFIG = load_notebook_config(dbutils, spark)
LANDING = Path(CONFIG.landing_path)

# COMMAND ----------

green_status = ingest_green_taxi(
    "all",
    output_dir=LANDING / "green_taxi",
    inventory_path=LANDING / "green_taxi" / "_metadata" / "green_taxi_inventory.csv",
    config=CONFIG,
)
if green_status:
    raise RuntimeError("One or more Green Taxi downloads failed.")

# COMMAND ----------

for start_date, end_date in CONFIG.monthly_date_ranges():
    download_weather(
        start_date,
        end_date,
        output_dir=LANDING / "weather",
        config=CONFIG,
    )

# COMMAND ----------

download_or_reuse(output_dir=LANDING / "taxi_zones", config=CONFIG)

# COMMAND ----------

expected = {
    "green_taxi": CONFIG.analysis_month_count,
    "weather": CONFIG.analysis_month_count * 2,
    "taxi_zones": 2,
}
for folder, minimum_count in expected.items():
    files = sorted(path for path in (LANDING / folder).rglob("*") if path.is_file())
    log_event(
        LOGGER,
        logging.INFO,
        "landing.inventory_checked",
        "Landing folder inventory checked",
        source=folder,
        file_count=len(files),
        minimum_file_count=minimum_count,
        files=[
            {"name": path.name, "size_bytes": path.stat().st_size} for path in files
        ],
    )
    if len(files) < minimum_count:
        raise RuntimeError(f"{folder} has fewer than {minimum_count} expected files.")

log_event(
    LOGGER,
    logging.INFO,
    "landing.completed",
    "All required sources landed in the configured volume",
    landing_path=LANDING,
)
