# NYC TLC Taxi Zone Lookup — Source and Profile Notes

## Source

- Source: NYC Taxi & Limousine Commission (TLC)
- Source page: NYC TLC Trip Record Data
- Direct CSV URL: https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
- Filename: `taxi_zone_lookup.csv`
- Retrieval time: `2026-09-15T00:52:06+08:00`
- File size: 12,331 bytes

## Raw File Location

`data/raw/taxi_zones/taxi_zone_lookup.csv`

The downloaded source file is stored unchanged in the raw data directory.

## Profile Results

- Row count: 265
- Columns:
  - `LocationID`
  - `Borough`
  - `Zone`
  - `service_zone`
- Null `LocationID` values: 0
- Duplicate `LocationID` values: 0

## Verification

The CSV was successfully parsed and contains the required location identifiers, zone names, and borough information.

The existing verified file is reused instead of downloading duplicate copies.

## Run Instructions

From the repository root, activate the Python environment and run:

```powershell
python ingestion/download_taxi_zones.py
```

Behavior:

- If `data/raw/taxi_zones/taxi_zone_lookup.csv` does not exist, the script downloads the official CSV, performs HTTP error checking, saves the raw file unchanged, and verifies its contents.
- If a valid copy already exists, the script verifies and reuses it instead of creating a duplicate.