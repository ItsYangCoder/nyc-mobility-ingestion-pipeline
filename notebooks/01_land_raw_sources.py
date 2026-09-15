# Databricks notebook source
# MAGIC %md
# MAGIC # Group C raw landing
# MAGIC Downloads the three required NYC Mobility sources directly to the
# MAGIC external Unity Catalog volume backed by R2.

# COMMAND ----------

from pathlib import Path
import sys

repo_root = next(
    (
        candidate
        for candidate in (Path.cwd(), Path.cwd().parent)
        if (candidate / "ingestion").is_dir()
    ),
    None,
)
if repo_root is None:
    raise RuntimeError(
        "Open this notebook from the repository's notebooks folder."
    )

sys.path.insert(0, str(repo_root))

from ingestion.download_taxi_zones import download_or_reuse
from ingestion.green_taxi import ingest_green_taxi
from ingestion.weather import download_weather

LANDING = Path(
    "/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing"
)

# COMMAND ----------

green_status = ingest_green_taxi(
    "all",
    output_dir=LANDING / "green_taxi",
    inventory_path=LANDING
    / "green_taxi"
    / "_metadata"
    / "green_taxi_inventory.csv",
)
if green_status:
    raise RuntimeError("One or more Green Taxi downloads failed.")

# COMMAND ----------

for start_date, end_date in (
    ("2026-03-01", "2026-03-31"),
    ("2026-04-01", "2026-04-30"),
    ("2026-05-01", "2026-05-31"),
):
    download_weather(
        start_date,
        end_date,
        output_dir=LANDING / "weather",
    )

# COMMAND ----------

download_or_reuse(output_dir=LANDING / "taxi_zones")

# COMMAND ----------

expected = {
    "green_taxi": 3,
    "weather": 6,
    "taxi_zones": 2,
}
for folder, minimum_count in expected.items():
    files = sorted(
        path
        for path in (LANDING / folder).rglob("*")
        if path.is_file()
    )
    print(f"\n{folder}: {len(files)} file(s)")
    for path in files:
        print(f"  {path.name} ({path.stat().st_size:,} bytes)")
    if len(files) < minimum_count:
        raise RuntimeError(
            f"{folder} has fewer than {minimum_count} expected files."
        )

print("\nPASS: all three required sources landed in the R2-backed volume.")
