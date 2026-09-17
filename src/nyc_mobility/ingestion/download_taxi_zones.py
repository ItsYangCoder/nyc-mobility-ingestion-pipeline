import argparse
import csv
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

from nyc_mobility.config import CONFIG
from nyc_mobility.logging import configure_logging, get_logger, log_event

SOURCE_URL = CONFIG.taxi_zones_source_url
DEFAULT_OUTPUT_DIR = Path("data/raw/taxi_zones")
REQUIRED_COLUMNS = {"LocationID", "Zone", "Borough"}
LOGGER = get_logger(__name__)


def profile_csv(file_path: Path) -> dict[str, object]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("The file does not contain a valid CSV header.")

        columns = reader.fieldnames
        missing_columns = REQUIRED_COLUMNS - set(columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

        row_count = 0
        null_location_ids = 0
        duplicate_location_ids = 0
        seen_location_ids = set()

        for row in reader:
            row_count += 1
            location_id = (row.get("LocationID") or "").strip()

            if not location_id:
                null_location_ids += 1
            elif location_id in seen_location_ids:
                duplicate_location_ids += 1
            else:
                seen_location_ids.add(location_id)

    if row_count == 0:
        raise ValueError("The CSV contains no data rows.")
    if null_location_ids or duplicate_location_ids:
        raise ValueError(
            "LocationID validation failed: "
            f"{null_location_ids} null and "
            f"{duplicate_location_ids} duplicate value(s)."
        )

    log_event(
        LOGGER,
        logging.INFO,
        "taxi_zones.profile_validated",
        "Taxi Zones source profile passed",
        file_path=file_path,
        row_count=row_count,
        columns=columns,
        null_location_ids=null_location_ids,
        duplicate_location_ids=duplicate_location_ids,
    )
    return {"row_count": row_count, "columns": columns}


def download_or_reuse(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "taxi_zone_lookup.csv"
    metadata_file = output_dir / "taxi_zone_lookup_metadata.json"

    if output_file.exists():
        profile_csv(output_file)
        log_event(
            LOGGER,
            logging.INFO,
            "taxi_zones.reused",
            "Existing Taxi Zones file is valid; download skipped",
            output_file=output_file,
            file_size_bytes=output_file.stat().st_size,
        )
        return

    temp_file = output_file.with_suffix(".csv.part")
    metadata_temp = metadata_file.with_suffix(".json.part")
    log_event(
        LOGGER,
        logging.INFO,
        "taxi_zones.download_started",
        "Downloading Taxi Zones source",
        source_url=SOURCE_URL,
        output_file=output_file,
    )

    try:
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
        temp_file.write_bytes(response.content)
        profile = profile_csv(temp_file)

        retrieval_time = datetime.now().astimezone().isoformat(timespec="seconds")
        metadata = {
            "source_url": SOURCE_URL,
            "retrieved_at": retrieval_time,
            "file_size_bytes": temp_file.stat().st_size,
            **profile,
        }
        with metadata_temp.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        temp_file.replace(output_file)
        metadata_temp.replace(metadata_file)
    finally:
        if temp_file.exists():
            temp_file.unlink()
        if metadata_temp.exists():
            metadata_temp.unlink()

    log_event(
        LOGGER,
        logging.INFO,
        "taxi_zones.download_completed",
        "Taxi Zones source downloaded and validated",
        output_file=output_file,
        metadata_file=metadata_file,
        file_size_bytes=output_file.stat().st_size,
    )


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(
        description="Download and validate the NYC Taxi Zone lookup CSV."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="landing directory; accepts a Databricks /Volumes/... path",
    )
    args = parser.parse_args()
    download_or_reuse(args.output_dir)


if __name__ == "__main__":
    main()
