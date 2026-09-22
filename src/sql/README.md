# SQL setup

This directory contains idempotent environment setup DDL only.

`notebooks/00_setup.py` renders `00_setup/00_setup.sql` through the validated
central configuration before executing each statement. For inspection or
manual execution, render a target file first:

```bash
python -m nyc_mobility.sql src/sql/00_setup/00_setup.sql --output setup.rendered.sql
```

The checked-in identifiers are safe defaults, not instructions to manually
find-and-replace catalog or schema names. Table and materialized-view
definitions belong in `src/nyc_mobility/transformations/`; validation SQL
belongs in `tests/sql/`.
