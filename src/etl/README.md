<!--
---
title: "ETL Pipeline"
description: "COSMOS-Web DR1 extraction, transformation, and loading scripts (Phase 1 complete)"
author: "VintageDon"
date: "2026-04-05"
version: "1.0"
status: "Phase 1 Complete"
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
| `extract_catalog.py` | Main ETL script. Reads 8.4GB FITS (6 extensions), extracts 4 parquet files, loads into PostgreSQL via COPY FROM |
| `verify_catalog.py` | Post-ETL verification. Runs 13 check sections (row counts, sentinel residuals, unit validation, O1 readiness), writes Markdown + HTML reports with embedded charts |
| `create_schema.sql` | DDL for the `catalog` schema. Creates all 7 tables with correct column types, constraints, and indexes |
| `profile_master_catalog.py` | Diagnostic script. Profiles the master catalog FITS file structure (column counts, types, array shapes per extension) |

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [src/](../) | Parent directory |
| [configs/](../../configs/) | `data_paths.yaml` provides input/output paths and DB connection config |
| [docs/verification-report.md](../../docs/verification-report.md) | Output of `verify_catalog.py` |
