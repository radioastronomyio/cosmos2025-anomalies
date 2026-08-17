<!--
---
title: "ETL Pipeline"
description: "COSMOS-Web catalog extraction, load-dictionary, and verification scripts"
author: "VintageDon"
date: "2026-04-05"
version: "1.6"
status: "Active"
tags:
  - type: directory-readme
  - domain: etl
---
-->

# ETL Pipeline

FITS-to-PostgreSQL pipeline for the COSMOS-Web DR1 master catalog. Phase 1 is complete — 784,016 sources loaded across 4 catalog tables plus 3 supplementary tables.

---

## Files

| File | Description |
|------|-------------|
| `load_dictionary.py` | Builds and validates the ETL v2 structural and semantic dictionary from configured v1.1 source and evidence artifacts |
| `profile_values.py` | Profiles every native scalar/vector index, enriches the dictionary, and generates the sentinel candidate report without changing source values |
| `validate_dictionary_seal.py` | Resolves the configured Gate 3.4 dictionary and validates its formal README, fixed JSON/count contract, and narrow Git ignore exception without live profiling |
| `verify_source_fidelity.py` | Runs the read-only Gate 3.5 manifest/input preflight and exact seven-table standalone/master fidelity comparison with importable structured evidence |
| `generate_schema_v11.py` | Generates the ETL v2 `source` mirror DDL solely from the sealed dictionary and versioned provenance contract; `--check` rejects hand drift |
| `schema_v11.sql` | Generated-only Gate 3.6 DDL for eleven source mirrors plus the fixed provenance table; never edit this artifact directly |
| `verify_schema_v11_scratch.py` | Creates one random prefix-scoped scratch database, verifies catalogs/comments/constraints and mutations, and drops it in `finally` |
| `extract_catalog.py` | Main ETL script. Reads 8.4GB FITS (6 extensions), extracts 4 parquet files, loads into PostgreSQL via COPY FROM |
| `verify_catalog.py` | Post-ETL verification. Runs 13 check sections (row counts, sentinel residuals, unit validation, O1 readiness), writes Markdown + HTML reports with embedded charts |
| `create_schema.sql` | DDL for the `catalog` schema. Creates all 7 tables with correct column types, constraints, and indexes |
| `profile_master_catalog.py` | Diagnostic script. Profiles the master catalog FITS file structure (column counts, types, array shapes per extension) |

---

## Gate 3.6 DDL generation and scratch verification

Generate or reproduce-check the tracked SQL from the sealed dictionary:

```bash
python src/etl/generate_schema_v11.py
python src/etl/generate_schema_v11.py --check
```

Run the live disposable validation only with the corrected ML01 development
credential scope. The verifier refuses `cosmos2025`, `cosmos2025_v11`, and any
database name outside its configured random scratch prefix.

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/verify_schema_v11_scratch.py
```

The live verifier performs no load and creates no target database or role.

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [src/](../) | Parent directory |
| [configs/](../../configs/) | `data_paths.yaml` provides input/output paths and DB connection config |
| [docs/verification-report.md](../../docs/verification-report.md) | Output of `verify_catalog.py` |
| [docs/reference/data-manifest-v1.1.md](../../docs/reference/data-manifest-v1.1.md) | Immutable source boundary validated before any fidelity comparison |
