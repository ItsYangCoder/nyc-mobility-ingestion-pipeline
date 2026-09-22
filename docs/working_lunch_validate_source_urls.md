# Team C Group Exercise: Ship NYC Mobility

## Implemented Change

**Validate ingestion source URLs**

## Purpose

Improve configuration safety by checking ingestion source URLs before the pipeline uses them. The change prevents insecure, malformed, or credential-bearing URLs from being accepted.

## 1. Sync and Branch

The work was created from the `development` branch on a dedicated feature branch:

`fix/validate-source-urls`

## 2. Configuration Safety Change

Updated `src/nyc_mobility/config.py` to validate the Weather, Green Taxi, and Taxi Zones source URLs.

The validation now requires a properly formed HTTPS address and rejects URLs containing an embedded username or password.

The repository already supports overriding these public source URLs through Spark configuration or the `NYC_MOBILITY_*` environment variables.

## 3. Automated Tests

Updated `tests/unit/test_config.py` with cases covering an insecure HTTP URL, a malformed URL, and a URL containing credentials.

**Focused result:** 11 configuration tests passed.

The complete local suite was not treated as final evidence because the local environment lacks PySpark and has unrelated Windows-specific temporary-path behavior. GitHub CI should run the supported Python 3.12 and Linux quality gates after a pull request is opened.

## 4. Commit and Push

**Commit:** `2c6e606 fix: validate ingestion source URLs`

The branch was pushed to GitHub as:

`origin/fix/validate-source-urls`

## 5. Pull Request and CI

A pull request was opened from `fix/validate-source-urls` to `development`.

**Link of PR:**  
https://github.com/ItsYangCoder/nyc-mobility-ingestion-pipeline/pull/84

GitHub Actions should run formatting, linting, tests, dependency auditing, and security checks.

Fix any failures before requesting approval.

## 6. Review, Merge, and Deployment

Merge only after CI is green and the pull request is reviewed.

Then deploy the merged `development` branch using the Databricks bundle workflow and run `mobility_workflow` in the development environment.

## 7. Post-Deployment Verification

Confirm that the workflow completes with the approved HTTPS source URLs.

Check data freshness, required-key null counts, schema conformity, expected row counts, and duplicate behavior.

Perform repeated runs to confirm idempotency.

## Scope Clarification

The NYC and Open-Meteo endpoints are public data-source addresses, not passwords or secrets.

This change validates those addresses but does not remove their non-secret defaults from the repository.

Actual credentials or signed URLs must be stored in Databricks secret scopes and must never be committed to Git.

## Current Status

**Completed:** feature branch, URL validation, focused automated tests, commit, GitHub push, and pull request.

**Pending:** GitHub CI, review, merge, Databricks deployment, pipeline run, rerun testing, and data-quality evidence.
