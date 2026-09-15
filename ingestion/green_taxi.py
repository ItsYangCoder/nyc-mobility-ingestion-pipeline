import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as parquet
import requests


BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "green_taxi"
INVENTORY_PATH = PROJECT_ROOT / "docs" / "green_taxi_inventory.csv"
MONTHS = ("03", "04", "05")
INVENTORY_FIELDS = ("filename", "source_url", "retrieved_at_utc", "file_size_bytes", "row_count", "columns")


def inspect_parquet(path):
    parquet_file = parquet.ParquetFile(path)
    return parquet_file.metadata.num_rows, parquet_file.schema_arrow.names


def load_inventory():
    if not INVENTORY_PATH.exists():
        return {}

    with INVENTORY_PATH.open(newline="", encoding="utf-8") as file:
        return {row["filename"]: row for row in csv.DictReader(file)}


def save_inventory(records):
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = INVENTORY_PATH.with_suffix(".csv.part")

    with temp_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=INVENTORY_FIELDS)
        writer.writeheader()
        writer.writerows(records[name] for name in sorted(records))

    temp_path.replace(INVENTORY_PATH)


def inventory_record(filename, url, path, row_count, columns, retrieved_at):
    return {
        "filename": filename,
        "source_url": url,
        "retrieved_at_utc": retrieved_at,
        "file_size_bytes": path.stat().st_size,
        "row_count": row_count,
        "columns": " | ".join(columns),
    }


def download_month(month, inventory):
    filename = f"green_tripdata_2026-{month}.parquet"
    url = f"{BASE_URL}/{filename}"
    output_path = OUTPUT_DIR / filename
    temp_path = output_path.with_suffix(".parquet.part")

    if output_path.exists():
        try:
            row_count, columns = inspect_parquet(output_path)
            existing = inventory.get(filename)
            retrieved_at = existing["retrieved_at_utc"] if existing else datetime.fromtimestamp(
                output_path.stat().st_mtime, timezone.utc
            ).isoformat()
            inventory[filename] = inventory_record(filename, url, output_path, row_count, columns, retrieved_at)
            print(f"Verified existing file, download skipped: {filename} ({row_count:,} rows)")
            return True
        except (OSError, ValueError):
            print(f"Existing file is not readable and will be replaced: {filename}")

    try:
        print(f"Downloading: {url}")
        with requests.get(url, stream=True, timeout=(10, 60)) as response:
            response.raise_for_status()
            with temp_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

        row_count, columns = inspect_parquet(temp_path)
        temp_path.replace(output_path)
        retrieved_at = datetime.now(timezone.utc).isoformat()
        inventory[filename] = inventory_record(filename, url, output_path, row_count, columns, retrieved_at)
        print(f"Downloaded and verified: {filename} ({row_count:,} rows)")
        return True
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else "unknown"
        print(f"Unavailable file: {filename} (HTTP {status_code}). No substitute month was downloaded.")
    except requests.RequestException as error:
        print(f"Download failed for {filename}: {error}")
    except (OSError, ValueError) as error:
        print(f"Parquet validation failed for {filename}: {error}")
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return False


def main():
    parser = argparse.ArgumentParser(description="Download and validate NYC TLC Green Taxi data for March–May 2026.")
    parser.add_argument("month", choices=(*MONTHS, "all"), help="month number (03, 04, 05) or all")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    inventory = load_inventory()
    selected_months = MONTHS if args.month == "all" else (args.month,)
    succeeded = [download_month(month, inventory) for month in selected_months]
    save_inventory(inventory)
    print(f"Inventory: {INVENTORY_PATH}")
    return 0 if all(succeeded) else 1


if __name__ == "__main__":
    raise SystemExit(main())
