# Contributing

## Branches

Create a focused feature branch from the latest `development` branch. Use prefixes such as `feature/`, `fix/`, `docs/`, or `chore/`.

## Pull requests

Target `development`. Include:

- what changed and why;
- exact run instructions;
- validation evidence and row-count reconciliation;
- affected Unity Catalog tables;
- known limitations or follow-up work.

A branch is not complete until its pull request is reviewed, CI passes, and it is merged.

## Data safety

Never commit credentials, raw datasets, external-volume contents, generated checkpoints, or private connection values. Preserve Bronze source records and lineage. Do not reset production checkpoints or run destructive full refreshes without explicit team approval.

## Validation

Run `pytest -q` locally. Databricks changes must also include pipeline-run evidence and relevant Bronze/Silver/Gold quality counts.
