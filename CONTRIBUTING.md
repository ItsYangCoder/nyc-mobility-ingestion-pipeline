# Contributing

## Branch model

The repository uses three long-lived environment branches:

| Branch | Environment | Allowed changes |
|---|---|---|
| `dev` | Development | Reviewed feature, fix, docs, and chore pull requests |
| `testing` | Testing/QA | Release candidates promoted only from `dev` |
| `main` | Production | Production releases promoted only from `testing` |

Create focused branches from the latest `dev` branch. Use prefixes such as `feature/`, `fix/`, `docs/`, or `chore/`.

The legacy `development` branch is retained temporarily for migration. Do not target it with new pull requests.

## Pull requests

Use this promotion path:

1. Feature branches target `dev`.
2. Release pull requests promote `dev` to `testing`.
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

Run `pytest -q` locally. Databricks changes must also include pipeline-run evidence and relevant Bronze/Silver/Gold quality counts.

Before promoting `dev` to `testing`, confirm the complete test suite passes. Before promoting `testing` to `main`, record release validation and obtain approval.
