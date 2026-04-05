<!--
---
title: "Configuration"
description: "Configuration files for data paths, database connections, and pipeline parameters"
author: "VintageDon"
date: "2026-04-05"
version: "1.0"
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
| `data_paths.yaml` | Master config. Defines catalog paths, output directories, database connection parameter names, and supplementary file locations |
| `.gitkeep` | Placeholder to preserve directory in git |

---

## Credential Pattern

Database credentials are NOT stored in this repository. Scripts load them at runtime from `/opt/agents/.env` using `python-dotenv`. The `data_paths.yaml` file stores only the *names* of environment variables (`host_env`, `port_env`, `user_env`, `password_env`), not the values themselves.

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [src/etl/](../src/etl/) | ETL scripts that consume `data_paths.yaml` |
