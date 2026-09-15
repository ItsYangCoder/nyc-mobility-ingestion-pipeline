from pathlib import Path
from datetime import datetime
import csv
import requests

SOURCE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

OUTPUT_DIR = Path("data/raw/taxi_zones")
OUTPUT_FILE = OUTPUT_DIR / "taxi_zone_lookup.csv"

REQUIRED_COLUMNS = {"LocationID", "Zone", "Borough"}

def profile_csv(file_path: Path):
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

        print(f"Rows: {row_count}")
        print(f"Columns: {columns}")
        print(f"Null LocationID values: {null_location_ids}")
        print(f"Duplicate LocationID values: {duplicate_location_ids}")

def download_or_reuse():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        print(f"Existing file found: {OUTPUT_FILE}")
        print("Verifying existing file...")

        profile_csv(OUTPUT_FILE)

        print("Existing file is valid. Reusing it.")
        print(f"File size: {OUTPUT_FILE.stat().st_size} bytes")
        return

    print(f"Downloading from: {SOURCE_URL}")

    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()

    OUTPUT_FILE.write_bytes(response.content)

    retrieval_time = datetime.now().astimezone().isoformat(timespec="seconds")

    print(f"Downloaded: {OUTPUT_FILE}")
    print(f"Retrieval time: {retrieval_time}")
    print(f"File size: {OUTPUT_FILE.stat().st_size} bytes")

    print("Verifying downloaded CSV...")
    profile_csv(OUTPUT_FILE)

if __name__ == "__main__":
    download_or_reuse()