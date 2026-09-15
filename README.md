# nyc-mobility-ingestion-pipeline
An incremental data pipeline integrating NYC Green Taxi trips, weather, taxi zones, and traffic advisories into a trusted mobility dataset.


## Local tests

Use Python 3.12 (also used by CI):

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
```

The pytest suite uses temporary files and mocked HTTP responses; it requires no
credentials or downloaded datasets. Pull requests targeting `development` and
`main` run the same suite in GitHub Actions.

To verify acquired datasets separately, run `python tests/test_raw_files.py`
after downloading the raw sources. This requires the files under `data/raw`.
Databricks Bronze execution and volume access require a configured Databricks
workspace; they are not exercised by the offline suite.
