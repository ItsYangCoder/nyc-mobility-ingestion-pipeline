# SQL setup

This directory contains idempotent environment setup DDL only.

Run `00_setup/00_setup.sql` before deploying pipeline tables. Table and
materialized-view definitions belong in
`src/nyc_mobility/transformations/`; validation SQL belongs in `tests/sql/`.
