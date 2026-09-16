import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import requests


SOURCE_URL = (
    "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
)
DEFAULT_OUTPUT_DIR = Path("data/raw/taxi_zones")
REQUIRED_COLUMNS = {"LocationID", "Zone", "Borough"}


def profile_csv(file_path: Path) -> dict[str, object]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("The file does not contain a valid CSV header.")

        columns = reader.fieldnames
        missing_columns = REQUIRED_COLUMNS - set(columns)
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {sorted(missing_columns)}"
            )

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

    print(f"Rows: {row_count}")
    print(f"Columns: {columns}")
    print(f"Null LocationID values: {null_location_ids}")
    print(f"Duplicate LocationID values: {duplicate_location_ids}")
    return {"row_count": row_count, "columns": columns}


def download_or_reuse(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "taxi_zone_lookup.csv"
    metadata_file = output_dir / "taxi_zone_lookup_metadata.json"

    if output_file.exists():
        print(f"Existing file found: {output_file}")
        print("Verifying existing file...")
        profile_csv(output_file)
        print("Existing file is valid. Download skipped.")
        print(f"File size: {output_file.stat().st_size} bytes")
        return

    temp_file = output_file.with_suffix(".csv.part")
    metadata_temp = metadata_file.with_suffix(".json.part")
    print(f"Downloading from: {SOURCE_URL}")

    try:
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
        temp_file.write_bytes(response.content)
        profile = profile_csv(temp_file)

        retrieval_time = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )
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

    print(f"Downloaded and verified: {output_file}")
    print(f"Saved metadata: {metadata_file}")
    print(f"File size: {output_file.stat().st_size} bytes")


def main() -> None:
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
