"""Local checks for acquired raw files. Raw records are never modified."""

import csv
import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path

import pyarrow.parquet as parquet

from nyc_mobility.config import CONFIG, PipelineConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

GREEN_TAXI_REQUIRED_COLUMNS = {
    "VendorID",
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
}

GREEN_TAXI_CANDIDATE_KEY = [
    "VendorID",
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
]

GREEN_TAXI_INVENTORY = PROJECT_ROOT / "docs" / "evidence" / "green_taxi_inventory.csv"

WEATHER_REQUIRED_FIELDS = {
    "time",
    "temperature_2m",
    "precipitation",
    "wind_speed_10m",
}

TAXI_ZONES_FILE = RAW_DIR / "taxi_zones" / "taxi_zone_lookup.csv"
TAXI_ZONES_REQUIRED_COLUMNS = {"LocationID", "Borough", "Zone"}


def configured_source_files(
    config: PipelineConfig,
    raw_dir: Path,
) -> tuple[dict[str, Path], dict[str, tuple[Path, str, str]]]:
    """Build deterministic raw-file expectations from an injected config."""
    green_taxi_files = {
        period: raw_dir / "green_taxi" / f"green_tripdata_{period}.parquet"
        for period in config.analysis_months()
    }
    weather_files = {
        start[:7]: (
            raw_dir / "weather" / f"weather_{start}_{end}.json",
            start,
            end,
        )
        for start, end in config.monthly_date_ranges()
    }
    return green_taxi_files, weather_files


def check_file(path: Path) -> bool:
    """Check file presence, size, and obvious error-page content."""
    if not path.exists():
        print(f"FAIL | Missing file: {path}")
        return False

    if path.stat().st_size == 0:
        print(f"FAIL | Empty file: {path}")
        return False

    try:
        with path.open("rb") as file:
            sample = file.read(1000).lower()
    except OSError as error:
        print(f"FAIL | Could not read {path}: {error}")
        return False

    error_markers = (
        b"<!doctype html",
        b"<html",
        b"<head",
        b"<body",
        b"access denied",
    )

    if any(marker in sample for marker in error_markers):
        print(f"FAIL | Possible HTML/error response: {path}")
        return False

    print(f"PASS | File exists and is non-empty: {path}")
    return True


def month_bounds(month: str) -> tuple[date, date]:
    year, month_number = map(int, month.split("-"))

    return (
        date(year, month_number, 1),
        date(year, month_number, monthrange(year, month_number)[1]),
    )


def as_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None

    return None


def check_green_taxi(
    path: Path,
    expected_month: str,
) -> tuple[bool, dict[str, int]]:
    print(f"\nChecking Green Taxi: {path.name}")

    metrics = {
        "missing": 0,
        "duplicates": 0,
    }

    if not check_file(path):
        return False, metrics

    try:
        parquet_file = parquet.ParquetFile(path)
    except Exception as error:
        print(f"FAIL | Could not read Parquet: {error}")
        return False, metrics

    columns = set(parquet_file.schema_arrow.names)
    missing_columns = GREEN_TAXI_REQUIRED_COLUMNS - columns

    if missing_columns:
        print(f"FAIL | Missing columns: {sorted(missing_columns)}")
        return False, metrics

    row_count = parquet_file.metadata.num_rows
    if row_count == 0:
        print("FAIL | Parquet contains zero rows")
        return False, metrics

    expected_start, expected_end = month_bounds(expected_month)
    boundary_dates = set()
    seen_keys = set()
    duplicate_keys = 0
    missing_key_rows = 0
    invalid_dates = 0
    outside_month = 0

    for batch in parquet_file.iter_batches(columns=GREEN_TAXI_CANDIDATE_KEY):
        key_columns = [
            batch.column(name).to_pylist() for name in GREEN_TAXI_CANDIDATE_KEY
        ]
        for key in zip(*key_columns, strict=True):
            pickup_date = as_date(key[1])
            if pickup_date is None:
                invalid_dates += 1
            elif pickup_date in (expected_start, expected_end):
                boundary_dates.add(pickup_date)
            elif not expected_start <= pickup_date <= expected_end:
                outside_month += 1

            if any(value is None for value in key):
                missing_key_rows += 1

            if key in seen_keys:
                duplicate_keys += 1
            else:
                seen_keys.add(key)

    if expected_start not in boundary_dates or expected_end not in boundary_dates:
        print(
            "FAIL | Pickup coverage does not include the full expected month: "
            f"{expected_start} to {expected_end}"
        )
        return False, metrics

    metrics["missing"] = missing_key_rows
    metrics["duplicates"] = duplicate_keys

    print(f"PASS | Rows: {row_count:,}")
    print(f"INFO | Invalid pickup dates: {invalid_dates:,}")
    print(f"INFO | Rows outside expected month: {outside_month:,}")
    print(f"INFO | Missing candidate-key rows: {missing_key_rows:,}")
    print(f"INFO | Duplicate candidate keys: {duplicate_keys:,}")

    return True, metrics


def check_weather(
    path: Path,
    expected_start: str,
    expected_end: str,
) -> tuple[bool, dict[str, int]]:
    print(f"\nChecking Weather: {path.name}")

    metrics = {
        "missing": 0,
        "duplicates": 0,
    }

    if not check_file(path):
        return False, metrics

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL | Invalid JSON: {error}")
        return False, metrics

    hourly = data.get("hourly") if isinstance(data, dict) else None

    if not isinstance(hourly, dict):
        print("FAIL | Missing or invalid hourly object")
        return False, metrics

    missing_fields = WEATHER_REQUIRED_FIELDS - set(hourly)

    if missing_fields:
        metrics["missing"] = len(missing_fields)
        print(f"FAIL | Missing weather fields: {sorted(missing_fields)}")
        return False, metrics

    timestamps = hourly["time"]

    if not isinstance(timestamps, list) or not timestamps:
        print("FAIL | Weather timestamps are missing or empty")
        return False, metrics

    for field in WEATHER_REQUIRED_FIELDS - {"time"}:
        values = hourly[field]

        if not isinstance(values, list) or len(values) != len(timestamps):
            print(f"FAIL | {field} does not match timestamp length")
            return False, metrics

    try:
        parsed = [
            datetime.fromisoformat(value.replace("Z", "+00:00")) for value in timestamps
        ]
    except (AttributeError, ValueError) as error:
        print(f"FAIL | Invalid timestamp: {error}")
        return False, metrics

    duplicate_timestamps = len(parsed) - len(set(parsed))
    metrics["duplicates"] = duplicate_timestamps

    if duplicate_timestamps:
        print(f"FAIL | Duplicate weather timestamps detected: {duplicate_timestamps:,}")
        return False, metrics

    start_date = date.fromisoformat(expected_start)
    end_date = date.fromisoformat(expected_end)

    actual_dates = {value.date() for value in parsed}

    expected_dates = {
        start_date + timedelta(days=offset)
        for offset in range((end_date - start_date).days + 1)
    }

    if actual_dates != expected_dates:
        print("FAIL | Weather date coverage does not match expected month")
        return False, metrics

    print(f"PASS | Hourly records: {len(timestamps):,}")
    print(f"INFO | Missing required fields: {metrics['missing']:,}")
    print(f"INFO | Duplicate timestamps: {metrics['duplicates']:,}")

    return True, metrics


def check_weather_metadata(weather_path: Path) -> bool:
    metadata_path = weather_path.with_name(f"{weather_path.stem}_metadata.json")

    if not check_file(metadata_path):
        return False

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL | Invalid weather metadata: {error}")
        return False

    required = {
        "retrieved_at",
        "request_parameters",
        "timezone",
        "units",
    }

    missing = required - set(metadata) if isinstance(metadata, dict) else required

    if missing:
        print(f"FAIL | Weather metadata missing fields: {sorted(missing)}")
        return False

    print("PASS | Weather acquisition metadata is recorded")
    return True


def check_taxi_zones(
    path: Path,
) -> tuple[bool, dict[str, int]]:
    print(f"\nChecking Taxi Zones: {path.name}")

    metrics = {
        "missing": 0,
        "duplicates": 0,
    }

    if not check_file(path):
        return False, metrics

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)
            columns = set(reader.fieldnames or [])
            rows = list(reader)

    except (OSError, csv.Error) as error:
        print(f"FAIL | Could not read CSV: {error}")
        return False, metrics

    missing_columns = TAXI_ZONES_REQUIRED_COLUMNS - columns

    if missing_columns:
        print(f"FAIL | Missing columns: {sorted(missing_columns)}")
        return False, metrics

    if not rows:
        print("FAIL | CSV contains zero rows")
        return False, metrics

    ids = [(row.get("LocationID") or "").strip() for row in rows]

    missing_ids = sum(not value for value in ids)

    duplicate_ids = len([value for value in ids if value]) - len(
        {value for value in ids if value}
    )

    metrics["missing"] = missing_ids
    metrics["duplicates"] = duplicate_ids

    if missing_ids or duplicate_ids:
        print(
            f"FAIL | Missing LocationID: {missing_ids:,}; duplicates: {duplicate_ids:,}"
        )
        return False, metrics

    print(f"PASS | Rows: {len(rows):,}; LocationID is complete and unique")
    print(f"INFO | Missing LocationID: {missing_ids:,}")
    print(f"INFO | Duplicate LocationID: {duplicate_ids:,}")

    return True, metrics


def check_green_taxi_inventory(inventory_path: Path) -> bool:
    if not check_file(inventory_path):
        return False

    required = {
        "filename",
        "source_url",
        "retrieved_at_utc",
        "file_size_bytes",
        "row_count",
        "columns",
    }

    try:
        with inventory_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)
            missing = required - set(reader.fieldnames or [])
            rows = list(reader)

    except (OSError, csv.Error) as error:
        print(f"FAIL | Could not read Green Taxi inventory: {error}")
        return False

    if missing or not rows:
        print(f"FAIL | Green Taxi inventory missing fields: {sorted(missing)}")
        return False

    print("PASS | Green Taxi acquisition metadata is recorded")
    return True


def main(
    config: PipelineConfig = CONFIG,
    raw_dir: Path = RAW_DIR,
    inventory_path: Path = GREEN_TAXI_INVENTORY,
) -> int:
    results = []
    green_taxi_files, weather_files = configured_source_files(config, raw_dir)

    for month, path in green_taxi_files.items():
        passed, metrics = check_green_taxi(path, month)

        results.append(
            (
                f"Green Taxi {month}",
                passed,
                metrics,
            )
        )

    results.append(
        (
            "Green Taxi metadata",
            check_green_taxi_inventory(inventory_path),
            None,
        )
    )

    for month, (path, expected_start, expected_end) in weather_files.items():
        passed, metrics = check_weather(path, expected_start, expected_end)

        results.append(
            (
                f"Weather {month}",
                passed,
                metrics,
            )
        )

        results.append(
            (
                f"Weather metadata {month}",
                check_weather_metadata(path),
                None,
            )
        )

    passed, metrics = check_taxi_zones(raw_dir / "taxi_zones" / TAXI_ZONES_FILE.name)

    results.append(
        (
            "Taxi Zones",
            passed,
            metrics,
        )
    )

    print("\nSUMMARY")

    failures = 0

    for name, passed, metrics in results:
        status = "PASS" if passed else "FAIL"

        print(f"{status:5} | {name}")

        if metrics is not None:
            print(
                f"       Missing: {metrics['missing']:,} | "
                f"Duplicates: {metrics['duplicates']:,}"
            )

        failures += not passed

    if failures:
        print(f"FAIL | {failures} check(s) need attention.")
        return 1

    print("PASS | All raw-data verification checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
