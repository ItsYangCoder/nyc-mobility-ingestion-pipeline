import argparse
import csv
import logging
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as parquet
import requests

from nyc_mobility.config import CONFIG, PipelineConfig
from nyc_mobility.logging import configure_logging, get_logger, log_event

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "green_taxi"
DEFAULT_INVENTORY_PATH = PROJECT_ROOT / "docs" / "evidence" / "green_taxi_inventory.csv"
INVENTORY_FIELDS = (
    "filename",
    "source_url",
    "retrieved_at_utc",
    "file_size_bytes",
    "row_count",
    "columns",
)
LOGGER = get_logger(__name__)


def inspect_parquet(path: Path) -> tuple[int, list[str]]:
    parquet_file = parquet.ParquetFile(path)
    row_count = parquet_file.metadata.num_rows
    columns = parquet_file.schema_arrow.names
    required = {
        "VendorID",
        "lpep_pickup_datetime",
        "lpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
    }
    missing = required - set(columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if row_count == 0:
        raise ValueError("Parquet contains zero rows.")
    return row_count, columns


def load_inventory(inventory_path: Path) -> dict[str, dict[str, str]]:
    if not inventory_path.exists():
        return {}

    with inventory_path.open(newline="", encoding="utf-8") as file:
        return {row["filename"]: row for row in csv.DictReader(file)}


def save_inventory(records: dict[str, dict[str, object]], inventory_path: Path) -> None:
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
    period: str,
    inventory: dict[str, dict[str, object]],
    output_dir: Path,
    base_url: str = CONFIG.green_taxi_base_url,
) -> bool:
    try:
        datetime.strptime(period, "%Y-%m")
    except ValueError as error:
        message = f"Invalid Green Taxi period: {period!r}; use YYYY-MM"
        raise ValueError(message) from error

    filename = f"green_tripdata_{period}.parquet"
    url = f"{base_url.rstrip('/')}/{filename}"
    output_path = output_dir / filename
    temp_path = output_path.with_suffix(".parquet.part")

    if output_path.exists():
        try:
            row_count, columns = inspect_parquet(output_path)
            existing = inventory.get(filename)
            if existing is None:
                raise ValueError("inventory record is missing")
            if existing.get("source_url") != url:
                raise ValueError(
                    "inventory source URL does not match current configuration"
                )
            retrieved_at = str(existing["retrieved_at_utc"])
            inventory[filename] = inventory_record(
                filename, url, output_path, row_count, columns, retrieved_at
            )
            log_event(
                LOGGER,
                logging.INFO,
                "green_taxi.reused",
                "Existing Green Taxi file is valid; download skipped",
                filename=filename,
                output_path=output_path,
                row_count=row_count,
                file_size_bytes=output_path.stat().st_size,
            )
            return True
        except Exception as error:
            log_event(
                LOGGER,
                logging.WARNING,
                "green_taxi.existing_invalid",
                "Existing Green Taxi file is unreadable and will be replaced",
                filename=filename,
                error=str(error),
            )

    try:
        log_event(
            LOGGER,
            logging.INFO,
            "green_taxi.download_started",
            "Downloading Green Taxi source",
            filename=filename,
            source_url=url,
            output_path=output_path,
        )
        with requests.get(url, stream=True, timeout=(10, 60)) as response:
            response.raise_for_status()
            with temp_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

        row_count, columns = inspect_parquet(temp_path)
        temp_path.replace(output_path)
        retrieved_at = datetime.now(UTC).isoformat()
        inventory[filename] = inventory_record(
            filename, url, output_path, row_count, columns, retrieved_at
        )
        log_event(
            LOGGER,
            logging.INFO,
            "green_taxi.download_completed",
            "Green Taxi source downloaded and validated",
            filename=filename,
            output_path=output_path,
            row_count=row_count,
            file_size_bytes=output_path.stat().st_size,
        )
        return True
    except requests.HTTPError as error:
        status_code = (
            error.response.status_code if error.response is not None else "unknown"
        )
        log_event(
            LOGGER,
            logging.ERROR,
            "green_taxi.http_error",
            "Green Taxi source is unavailable; no substitute month was downloaded",
            filename=filename,
            source_url=url,
            status_code=status_code,
            error=str(error),
        )
    except requests.RequestException as error:
        log_event(
            LOGGER,
            logging.ERROR,
            "green_taxi.request_failed",
            "Green Taxi download failed",
            filename=filename,
            source_url=url,
            error=str(error),
            exc_info=True,
        )
    except Exception as error:
        log_event(
            LOGGER,
            logging.ERROR,
            "green_taxi.processing_failed",
            "Green Taxi validation or file write failed",
            filename=filename,
            output_path=output_path,
            error=str(error),
            exc_info=True,
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return False


def ingest_green_taxi(
    period: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    inventory_path: Path = DEFAULT_INVENTORY_PATH,
    config: PipelineConfig = CONFIG,
) -> int:
    output_dir = Path(output_dir)
    inventory_path = Path(inventory_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = load_inventory(inventory_path)
    configured_periods = config.analysis_months()
    selected_periods = configured_periods if period == "all" else (period,)
    invalid_periods = set(selected_periods) - set(configured_periods)
    if invalid_periods:
        raise ValueError(
            "Green Taxi period must be within the configured analysis window: "
            f"{sorted(invalid_periods)}"
        )
    succeeded = [
        download_month(
            selected_period,
            inventory,
            output_dir,
            base_url=config.green_taxi_base_url,
        )
        for selected_period in selected_periods
    ]
    save_inventory(inventory, inventory_path)
    log_event(
        LOGGER,
        logging.INFO,
        "green_taxi.inventory_saved",
        "Green Taxi inventory saved",
        inventory_path=inventory_path,
        selected_periods=selected_periods,
        successful_files=sum(succeeded),
        failed_files=len(succeeded) - sum(succeeded),
    )
    return 0 if all(succeeded) else 1


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(
        description="Download and validate configured NYC TLC Green Taxi months."
    )
    parser.add_argument(
        "period",
        choices=(*CONFIG.analysis_months(), "all"),
        help="configured month in YYYY-MM format, or all",
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
        args.period,
        output_dir=args.output_dir,
        inventory_path=args.inventory_path,
        config=CONFIG,
    )


if __name__ == "__main__":
    raise SystemExit(main())
