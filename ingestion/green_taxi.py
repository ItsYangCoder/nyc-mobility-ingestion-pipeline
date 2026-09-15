import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as parquet
import requests


BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "green_taxi"
DEFAULT_INVENTORY_PATH = PROJECT_ROOT / "docs" / "green_taxi_inventory.csv"
MONTHS = ("03", "04", "05")
INVENTORY_FIELDS = (
    "filename",
    "source_url",
    "retrieved_at_utc",
    "file_size_bytes",
    "row_count",
    "columns",
)


def inspect_parquet(path: Path) -> tuple[int, list[str]]:
    parquet_file = parquet.ParquetFile(path)
    return parquet_file.metadata.num_rows, parquet_file.schema_arrow.names


def load_inventory(inventory_path: Path) -> dict[str, dict[str, str]]:
    if not inventory_path.exists():
        return {}

    with inventory_path.open(newline="", encoding="utf-8") as file:
        return {row["filename"]: row for row in csv.DictReader(file)}


def save_inventory(
    records: dict[str, dict[str, object]], inventory_path: Path
) -> None:
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = inventory_path.with_suffix(".csv.part")

    with temp_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=INVENTORY_FIELDS)
        writer.writeheader()
        writer.writerows(records[name] for name in sorted(records))

    temp_path.replace(inventory_path)


def inventory_record(
    filename: str,
    url: str,
    path: Path,
    row_count: int,
    columns: list[str],
    retrieved_at: str,
) -> dict[str, object]:
    return {
        "filename": filename,
        "source_url": url,
        "retrieved_at_utc": retrieved_at,
        "file_size_bytes": path.stat().st_size,
        "row_count": row_count,
        "columns": " | ".join(columns),
    }


def download_month(
    month: str,
    inventory: dict[str, dict[str, object]],
    output_dir: Path,
) -> bool:
    filename = f"green_tripdata_2026-{month}.parquet"
    url = f"{BASE_URL}/{filename}"
    output_path = output_dir / filename
    temp_path = output_path.with_suffix(".parquet.part")

    if output_path.exists():
        try:
            row_count, columns = inspect_parquet(output_path)
            existing = inventory.get(filename)
            retrieved_at = (
                str(existing["retrieved_at_utc"])
                if existing
                else datetime.fromtimestamp(
                    output_path.stat().st_mtime, timezone.utc
                ).isoformat()
            )
            inventory[filename] = inventory_record(
                filename, url, output_path, row_count, columns, retrieved_at
            )
            print(
                f"Verified existing file, download skipped: "
                f"{filename} ({row_count:,} rows)"
            )
            return True
        except Exception as error:
            print(
                f"Existing file is unreadable and will be replaced: "
                f"{filename} ({error})"
            )

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
        inventory[filename] = inventory_record(
            filename, url, output_path, row_count, columns, retrieved_at
        )
        print(f"Downloaded and verified: {filename} ({row_count:,} rows)")
        return True
    except requests.HTTPError as error:
        status_code = (
            error.response.status_code
            if error.response is not None
            else "unknown"
        )
        print(
            f"Unavailable file: {filename} (HTTP {status_code}). "
            "No substitute month was downloaded."
        )
    except requests.RequestException as error:
        print(f"Download failed for {filename}: {error}")
    except Exception as error:
        print(f"Parquet validation or file write failed for {filename}: {error}")
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return False


def ingest_green_taxi(
    month: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    inventory_path: Path = DEFAULT_INVENTORY_PATH,
) -> int:
    output_dir = Path(output_dir)
    inventory_path = Path(inventory_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = load_inventory(inventory_path)
    selected_months = MONTHS if month == "all" else (month,)
    succeeded = [
        download_month(selected_month, inventory, output_dir)
        for selected_month in selected_months
    ]
    save_inventory(inventory, inventory_path)
    print(f"Inventory: {inventory_path}")
    return 0 if all(succeeded) else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download and validate NYC TLC Green Taxi data "
            "for March-May 2026."
        )
    )
    parser.add_argument(
        "month",
        choices=(*MONTHS, "all"),
        help="month number (03, 04, 05) or all",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="landing directory; accepts a Databricks /Volumes/... path",
    )
    parser.add_argument(
        "--inventory-path",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help="CSV inventory path; accepts a Databricks /Volumes/... path",
    )
    args = parser.parse_args()
    return ingest_green_taxi(
        args.month,
        output_dir=args.output_dir,
        inventory_path=args.inventory_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
