"""
Local raw-data acquisition and verification checks.

Purpose:
- Verify that expected raw files exist and are non-empty.
- Verify that files are readable and match their expected format.
- Verify required columns and basic date coverage.
- Report duplicate and missing key indicators without modifying raw data.
- Detect HTML/error responses saved as data files.

This script does NOT clean, transform, or delete raw records.
"""

import json
from calendar import monthrange
from datetime import date
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

GREEN_TAXI_DIR = RAW_DIR / "green_taxi"
GREEN_TAXI_FILES = {
    "2026-03": GREEN_TAXI_DIR / "green_tripdata_2026-03.parquet",
    "2026-04": GREEN_TAXI_DIR / "green_tripdata_2026-04.parquet",
    "2026-05": GREEN_TAXI_DIR / "green_tripdata_2026-05.parquet",
}
GREEN_TAXI_REQUIRED_COLUMNS = {
    "VendorID",
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
}
GREEN_TAXI_DUPLICATE_KEYS = [
    "VendorID",
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
]
GREEN_TAXI_INVENTORY_PATH = PROJECT_ROOT / "docs" / "green_taxi_inventory.csv"

WEATHER_DIR = RAW_DIR / "weather"
WEATHER_FILES = {
    "2026-03": WEATHER_DIR / "weather_2026-03-01_2026-03-31.json",
    "2026-04": WEATHER_DIR / "weather_2026-04-01_2026-04-30.json",
    "2026-05": WEATHER_DIR / "weather_2026-05-01_2026-05-31.json",
}
WEATHER_REQUIRED_FIELDS = {
    "time",
    "temperature_2m",
    "precipitation",
    "wind_speed_10m",
}

TAXI_ZONES_FILE = RAW_DIR / "taxi_zones" / "taxi_zone_lookup.csv"
TAXI_ZONES_REQUIRED_COLUMNS = {"LocationID", "Borough", "Zone"}


# ---------------------------------------------------------------------
# Generic checks
# ---------------------------------------------------------------------


def check_exists(path: Path) -> bool:
    """Check that a file exists."""
    if not path.exists():
        print(f"FAIL | Missing file: {path}")
        return False

    print(f"PASS | Exists: {path}")
    return True


def check_non_empty(path: Path) -> bool:
    """Check that a file is not empty."""
    if path.stat().st_size == 0:
        print(f"FAIL | Empty file: {path}")
        return False

    print(f"PASS | Non-empty: {path}")
    return True


def check_not_html(path: Path) -> bool:
    """Detect common HTML/error-page responses saved as data."""
    try:
        content = path.read_bytes()[:1000].lower()
    except OSError as exc:
        print(f"FAIL | Could not read {path}: {exc}")
        return False

    html_markers = (
        b"<!doctype html",
        b"<html",
        b"<head",
        b"<body",
        b"access denied",
    )

    if any(marker in content for marker in html_markers):
        print(f"FAIL | Possible HTML/error response: {path}")
        return False

    print(f"PASS | No obvious HTML/error response: {path}")
    return True


def check_required_columns(
    columns: list[str], required_columns: set[str], dataset_name: str
) -> bool:
    """Check that all required columns are present."""
    missing_columns = required_columns - set(columns)

    if missing_columns:
        print(
            f"FAIL | {dataset_name} missing required columns: "
            f"{sorted(missing_columns)}"
        )
        return False

    print(f"PASS | {dataset_name} required columns are present")
    return True


# ---------------------------------------------------------------------
# Green Taxi Parquet checks
# ---------------------------------------------------------------------


def check_green_taxi_file(path: Path, expected_month: str) -> bool:
    """Validate one Green Taxi monthly Parquet file."""
    print(f"\nChecking Green Taxi: {path}")

    if not check_exists(path) or not check_non_empty(path):
        return False

    if not check_not_html(path):
        return False

    try:
        dataframe = pd.read_parquet(path)
    except Exception as exc:
        print(f"FAIL | Could not read Parquet: {exc}")
        return False

    print("PASS | Readable Parquet")
    print(f"INFO | Rows: {len(dataframe):,}")
    print(f"INFO | Columns: {list(dataframe.columns)}")

    if dataframe.empty:
        print("FAIL | Parquet contains zero rows")
        return False

    print("PASS | Contains records")

    if not check_required_columns(
        list(dataframe.columns), GREEN_TAXI_REQUIRED_COLUMNS, "Green Taxi"
    ):
        return False

    pickup_dates = pd.to_datetime(
        dataframe["lpep_pickup_datetime"], errors="coerce"
    ).dt.date
    expected_year, expected_month_number = map(int, expected_month.split("-"))
    expected_start = date(expected_year, expected_month_number, 1)
    expected_end = date(
        expected_year,
        expected_month_number,
        monthrange(expected_year, expected_month_number)[1],
    )

    invalid_dates = pickup_dates.isna().sum()
    if invalid_dates:
        print(f"WARN | Invalid pickup dates: {invalid_dates:,}")
    else:
        print("PASS | Pickup dates are readable")

    actual_start = pickup_dates.min()
    actual_end = pickup_dates.max()
    print(f"INFO | Pickup date range: {actual_start} to {actual_end}")

    if actual_start is not None and actual_end is not None:
        if actual_start < expected_start or actual_end > expected_end:
            print(
                "WARN | Pickup date range extends outside the expected "
                f"month {expected_month}"
            )

    missing_key_values = dataframe[GREEN_TAXI_DUPLICATE_KEYS].isna().sum()
    missing_key_total = int(missing_key_values.sum())
    print(f"INFO | Missing values in candidate key columns: {missing_key_total:,}")

    duplicate_count = dataframe.duplicated(
        subset=GREEN_TAXI_DUPLICATE_KEYS
    ).sum()
    print(
        "INFO | Duplicate rows using candidate key "
        f"{GREEN_TAXI_DUPLICATE_KEYS}: {duplicate_count:,}"
    )

    return True


# ---------------------------------------------------------------------
# Weather JSON checks
# ---------------------------------------------------------------------


def check_weather_file(path: Path, expected_month: str) -> bool:
    """Validate one Open-Meteo hourly weather JSON response."""
    print(f"\nChecking Weather JSON: {path}")

    if not check_exists(path) or not check_non_empty(path):
        return False

    if not check_not_html(path):
        return False

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL | Invalid JSON: {exc}")
        return False

    if not isinstance(data, dict):
        print("FAIL | Expected JSON object")
        return False

    print("PASS | Valid JSON")

    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        print("FAIL | Missing or invalid 'hourly' weather data")
        return False

    missing_fields = WEATHER_REQUIRED_FIELDS - set(hourly)
    if missing_fields:
        print(
            "FAIL | Weather missing required fields: "
            f"{sorted(missing_fields)}"
        )
        return False

    print("PASS | Weather required fields are present")

    timestamps = hourly["time"]
    if not isinstance(timestamps, list) or not timestamps:
        print("FAIL | Weather timestamp list is missing or empty")
        return False

    variable_lengths_match = True
    for field in WEATHER_REQUIRED_FIELDS - {"time"}:
        values = hourly[field]
        if not isinstance(values, list):
            print(f"FAIL | Weather field is not a list: {field}")
            variable_lengths_match = False
            continue

        if len(values) != len(timestamps):
            print(
                f"FAIL | {field} length {len(values):,} does not match "
                f"timestamp length {len(timestamps):,}"
            )
            variable_lengths_match = False

    if not variable_lengths_match:
        return False

    print(f"INFO | Hourly records: {len(timestamps):,}")

    try:
        parsed_timestamps = pd.to_datetime(timestamps, errors="raise")
    except (TypeError, ValueError) as exc:
        print(f"FAIL | Invalid weather timestamp: {exc}")
        return False

    duplicate_timestamps = parsed_timestamps.duplicated().sum()
    print(f"INFO | Duplicate timestamps: {duplicate_timestamps:,}")

    expected_year, expected_month_number = map(int, expected_month.split("-"))
    expected_start = date(expected_year, expected_month_number, 1)
    expected_end = date(
        expected_year,
        expected_month_number,
        monthrange(expected_year, expected_month_number)[1],
    )

    actual_start = parsed_timestamps.min().date()
    actual_end = parsed_timestamps.max().date()
    print(f"INFO | Date coverage: {actual_start} to {actual_end}")

    if actual_start != expected_start or actual_end != expected_end:
        print(
            "FAIL | Weather date coverage does not match expected "
            f"{expected_start} to {expected_end}"
        )
        return False

    expected_dates = pd.date_range(expected_start, expected_end, freq="D").date
    actual_dates = set(parsed_timestamps.date)
    missing_dates = set(expected_dates) - actual_dates

    if missing_dates:
        print(f"FAIL | Missing weather dates: {sorted(missing_dates)}")
        return False

    if duplicate_timestamps:
        print("FAIL | Duplicate weather timestamps detected")
        return False

    print("PASS | Weather date coverage and timestamps are valid")
    return True


# ---------------------------------------------------------------------
# Taxi Zones CSV checks
# ---------------------------------------------------------------------


def check_taxi_zones_file(path: Path) -> bool:
    """Validate the NYC Taxi Zones CSV."""
    print(f"\nChecking Taxi Zones CSV: {path}")

    if not check_exists(path) or not check_non_empty(path):
        return False

    if not check_not_html(path):
        return False

    try:
        dataframe = pd.read_csv(path)
    except Exception as exc:
        print(f"FAIL | Could not read CSV: {exc}")
        return False

    print("PASS | Readable CSV")
    print(f"INFO | Rows: {len(dataframe):,}")
    print(f"INFO | Columns: {list(dataframe.columns)}")

    if dataframe.empty:
        print("FAIL | CSV contains zero rows")
        return False

    print("PASS | Contains records")

    if not check_required_columns(
        list(dataframe.columns), TAXI_ZONES_REQUIRED_COLUMNS, "Taxi Zones"
    ):
        return False

    duplicate_count = dataframe["LocationID"].duplicated().sum()
    missing_count = dataframe["LocationID"].isna().sum()

    print(f"INFO | Duplicate LocationID: {duplicate_count:,}")
    print(f"INFO | Missing LocationID: {missing_count:,}")

    return True


# ---------------------------------------------------------------------
# Metadata checks
# ---------------------------------------------------------------------


def check_green_taxi_inventory() -> bool:
    """Check that Green Taxi acquisition metadata is recorded."""
    if not GREEN_TAXI_INVENTORY_PATH.exists():
        print(f"WARN | Green Taxi inventory not found: {GREEN_TAXI_INVENTORY_PATH}")
        return False

    try:
        inventory = pd.read_csv(GREEN_TAXI_INVENTORY_PATH)
    except Exception as exc:
        print(f"WARN | Could not read Green Taxi inventory: {exc}")
        return False

    required_fields = {
        "filename",
        "source_url",
        "retrieved_at_utc",
        "file_size_bytes",
        "row_count",
        "columns",
    }
    missing_fields = required_fields - set(inventory.columns)

    if missing_fields:
        print(f"WARN | Green Taxi inventory missing fields: {sorted(missing_fields)}")
        return False

    print("PASS | Green Taxi acquisition metadata is recorded")
    return True


# ---------------------------------------------------------------------
# Main verification
# ---------------------------------------------------------------------


def main() -> int:
    print("=" * 70)
    print("NYC MOBILITY RAW DATA VERIFICATION")
    print("=" * 70)

    results = []

    for month, path in GREEN_TAXI_FILES.items():
        result = check_green_taxi_file(path, month)
        results.append((f"Green Taxi {month}", result))

    results.append(("Green Taxi metadata", check_green_taxi_inventory()))

    for month, path in WEATHER_FILES.items():
        result = check_weather_file(path, month)
        results.append((f"Weather {month}", result))

    results.append(("Taxi Zones", check_taxi_zones_file(TAXI_ZONES_FILE)))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    failures = 0

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status:5} | {name}")
        if not passed:
            failures += 1

    print("=" * 70)

    if failures:
        print(f"FAIL | {failures} check(s) need attention.")
        return 1

    print("PASS | All raw-data verification checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
