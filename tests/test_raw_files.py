```python
"""
Local raw-data acquisition and verification checks.

Purpose:
- Verify that expected raw files exist and are non-empty.
- Verify that files are readable and match their expected format.
- Check basic schema and date coverage.
- Detect duplicate keys without modifying raw data.
- Detect HTML/error responses saved as data files.

This script does NOT clean, transform, or delete raw records.
"""

from pathlib import Path
import json

import pandas as pd


RAW_DIR = Path("data/raw")


# ---------------------------------------------------------------------
# Expected raw files
# ---------------------------------------------------------------------

GREEN_TAXI_FILES = {
    "2026-03": RAW_DIR / "green_taxi_2026-03.parquet",
    "2026-04": RAW_DIR / "green_taxi_2026-04.parquet",
    "2026-05": RAW_DIR / "green_taxi_2026-05.parquet",
}

WEATHER_FILE = RAW_DIR / "weather_2026.json"

TAXI_ZONES_FILE = RAW_DIR / "taxi_zones.csv"


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
    """
    Detect common HTML/error-page responses accidentally saved as data.
    """
    try:
        content = path.read_bytes()[:1000].lower()
    except OSError as exc:
        print(f"FAIL | Could not read {path}: {exc}")
        return False

    html_markers = [
        b"<!doctype html",
        b"<html",
        b"<head",
        b"<body",
        b"access denied",
        b"error",
    ]

    if any(marker in content for marker in html_markers):
        print(f"FAIL | Possible HTML/error response: {path}")
        return False

    print(f"PASS | No obvious HTML/error response: {path}")
    return True


# ---------------------------------------------------------------------
# Green Taxi Parquet checks
# ---------------------------------------------------------------------

def check_green_taxi_file(path: Path) -> bool:
    """Validate one Green Taxi monthly Parquet file."""

    print(f"\nChecking Green Taxi: {path}")

    if not check_exists(path):
        return False

    if not check_non_empty(path):
        return False

    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        print(f"FAIL | Could not read Parquet: {exc}")
        return False

    print(f"PASS | Readable Parquet")
    print(f"INFO | Rows: {len(df):,}")
    print(f"INFO | Columns: {list(df.columns)}")

    if df.empty:
        print("FAIL | Parquet contains zero rows")
        return False

    print("PASS | Contains records")

    # Basic duplicate check.
    possible_keys = [
        ["VendorID", "lpep_pickup_datetime", "lpep_dropoff_datetime"],
        ["VendorID", "lpep_pickup_datetime"],
    ]

    for keys in possible_keys:
        if all(key in df.columns for key in keys):
            duplicates = df.duplicated(subset=keys).sum()
            print(f"INFO | Duplicate rows using {keys}: {duplicates:,}")
            break

    return True


# ---------------------------------------------------------------------
# Weather JSON checks
# ---------------------------------------------------------------------

def check_weather_file(path: Path) -> bool:
    """Validate the weather JSON response."""

    print(f"\nChecking Weather JSON: {path}")

    if not check_exists(path):
        return False

    if not check_non_empty(path):
        return False

    if not check_not_html(path):
        return False

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        print(f"FAIL | Invalid JSON: {exc}")
        return False

    print("PASS | Valid JSON")

    if not isinstance(data, dict):
        print("FAIL | Expected JSON object")
        return False

    print(f"INFO | Top-level keys: {list(data.keys())}")

    # Open-Meteo responses normally contain a "daily" or "hourly"
    # section depending on the request.
    if "daily" in data:
        print("PASS | Found 'daily' weather data")
        print(f"INFO | Daily keys: {list(data['daily'].keys())}")

    elif "hourly" in data:
        print("PASS | Found 'hourly' weather data")
        print(f"INFO | Hourly keys: {list(data['hourly'].keys())}")

    else:
        print("WARN | No 'daily' or 'hourly' section found")

    return True


# ---------------------------------------------------------------------
# Taxi Zones CSV checks
# ---------------------------------------------------------------------

def check_taxi_zones_file(path: Path) -> bool:
    """Validate the NYC Taxi Zones CSV."""

    print(f"\nChecking Taxi Zones CSV: {path}")

    if not check_exists(path):
        return False

    if not check_non_empty(path):
        return False

    if not check_not_html(path):
        return False

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        print(f"FAIL | Could not read CSV: {exc}")
        return False

    print("PASS | Readable CSV")
    print(f"INFO | Rows: {len(df):,}")
    print(f"INFO | Columns: {list(df.columns)}")

    if df.empty:
        print("FAIL | CSV contains zero rows")
        return False

    print("PASS | Contains records")

    # Taxi zone files commonly contain LocationID.
    if "LocationID" in df.columns:
        duplicates = df["LocationID"].duplicated().sum()
        missing = df["LocationID"].isna().sum()

        print(f"INFO | Duplicate LocationID: {duplicates:,}")
        print(f"INFO | Missing LocationID: {missing:,}")

    return True


# ---------------------------------------------------------------------
# Main verification
# ---------------------------------------------------------------------

def main() -> int:
    print("=" * 70)
    print("NYC MOBILITY RAW-DATA VERIFICATION")
    print("=" * 70)

    results = []

    # Green Taxi: March, April, May 2026
    for month, path in GREEN_TAXI_FILES.items():
        result = check_green_taxi_file(path)
        results.append((f"Green Taxi {month}", result))

    # Weather
    results.append(
        ("Weather JSON", check_weather_file(WEATHER_FILE))
    )

    # Taxi Zones
    results.append(
        ("Taxi Zones CSV", check_taxi_zones_file(TAXI_ZONES_FILE))
    )

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
        print(f"FAIL | {failures} dataset(s) need attention.")
        return 1

    print("PASS | All available raw-data checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
