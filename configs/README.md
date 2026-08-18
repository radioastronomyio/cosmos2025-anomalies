<!--
---
title: "Configuration"
description: "Configuration files for data paths, database connections, and pipeline parameters"
author: "VintageDon"
date: "2026-08-18"
version: "1.7"
status: "Active"
tags:
  - type: directory-readme
  - domain: configuration
---
-->

# Configuration

Configuration files consumed by pipeline source code. All paths and connection parameters are centralized here — source code never hardcodes data locations.

---

## Files

| File | Description |
|------|-------------|
| `data_paths.yaml` | Master config. Defines immutable inputs, generated dictionary/DDL/schema reference, named v1 baseline, bootstrap verification transport, v1.1 read-only runtime contract, scratch/persistent targets, handoff, and bounded ETL settings |
| `.gitkeep` | Placeholder to preserve directory in git |

---

## Credential Pattern

Database credentials are NOT stored in this repository. Bootstrap and
verification tools receive administrator values from `doppler run --project
ml01 --config dev -- <cmd>`; the flat `host_env`, `port_env`, `user_env`, and
`password_env` keys are bootstrap-only. The named `baseline_v1` contract keeps
`cosmos2025.catalog` read-only. The named `runtime_v11` contract uses
`PGSQL01_COSMOS2025_V11_DB`, `_USER`, and `_PASSWORD` plus shared host/port
names for read-only `cosmos2025_v11.source` consumers. Configuration stores
names, never values.

Gate 3.7 fixes the persistent target to `cosmos2025_v11`, the login role to
`cosmos2025_v11_ro`, and the ignored handoff to
`internal-files/cosmos2025-v11.env`. The config also bounds COPY frames at
2,000 rows and requires at least 50 GiB free on the PostgreSQL data volume
immediately before creation. The create/load CLI refuses any pre-existing
target and has no table-reload path. `--finalize-admin` accepts only an exact
retained seven-master load with absent role/handoff and completes administration
only after exact nullability and canonical constraint-definition checks,
without FITS reads or COPY. `--verify-only` performs post-load inspection.
The active operator-corrected credential scope is `ml01/dev`. No Doppler value
is imported, changed, or written by the repository.

The completed Gate 3.7 run used the configured `clusteradmin_pg01` session for
all database operations and PostgreSQL `SET SESSION AUTHORIZATION` for analyst
privilege checks. Direct network authentication as `cosmos2025_v11_ro` from
ML01 was not exercised because the cluster HBA currently covers only the admin
role. The operator explicitly accepted that limitation for this run. Adding
SCRAM HBA coverage for the analyst from ML01 remains a required post-run
infrastructure action; this repository does not edit or reload HBA policy.

Gate 3.12 adds `dictionary.schema_v11_docs` for the generated
`docs/reference/schema-v11.md` artifact. Its generator performs one bounded
read-only live catalog/count observation and no immutable-source read.

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [src/etl/](../src/etl/) | ETL scripts that consume `data_paths.yaml` |
