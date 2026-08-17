<!--
---
title: "Configuration"
description: "Configuration files for data paths, database connections, and pipeline parameters"
author: "VintageDon"
date: "2026-04-05"
version: "1.5"
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
| `data_paths.yaml` | Master config. Defines catalog, semantic evidence, provenance-pin, dictionary/DDL/report, staging, database environment-name, maintenance database, scratch prefix, and supplement paths |
| `.gitkeep` | Placeholder to preserve directory in git |

---

## Credential Pattern

Database credentials are NOT stored in this repository. Scripts read them at runtime from Doppler-injected environment variables (`doppler run --project ml01 --config dev -- <cmd>`). The `data_paths.yaml` file stores only the *names* of environment variables (`host_env`, `port_env`, `user_env`, `password_env`), not the values themselves. Gate 3.6 admin operations connect through configured maintenance database `postgres`; the verifier accepts only random names under `cosmos2025_v11_scratch_`.

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [src/etl/](../src/etl/) | ETL scripts that consume `data_paths.yaml` |
