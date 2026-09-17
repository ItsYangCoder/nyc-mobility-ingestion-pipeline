# Contributing

## Branch model

The repository uses three long-lived environment branches:

| Branch | Environment | Allowed changes |
|---|---|---|
| `development` | Development | Reviewed feature, fix, docs, and chore pull requests |
| `testing` | Testing/QA | Release candidates promoted only from `development` |
| `main` | Production | Production releases promoted only from `testing` |

Create focused branches from the latest `development` branch. Use prefixes such as `feature/`, `fix/`, `docs/`, or `chore/`.

## Pull requests

Use this promotion path:

1. Feature branches target `development`.
2. Release pull requests promote `development` to `testing`.
3. Production pull requests promote `testing` to `main`.

Include:

- what changed and why;
- exact run instructions;
- validation evidence and row-count reconciliation;
- affected Unity Catalog tables;
- known limitations or follow-up work.

A change is not complete until its pull request is reviewed, CI passes, and it is merged. Do not merge a failing pull request or bypass the promotion order.

## Data safety

Never commit credentials, raw datasets, external-volume contents, generated checkpoints, or private connection values. Preserve Bronze source records and lineage. Do not reset production checkpoints or run destructive full refreshes without explicit team approval.

## Validation

Install `requirements-dev.txt` and run `python -m pytest -q` locally. Databricks changes must also include pipeline-run evidence and relevant Bronze/Silver/Gold quality counts.

Before promoting `development` to `testing`, confirm the complete test suite passes. Before promoting `testing` to `main`, record release validation and obtain approval.
