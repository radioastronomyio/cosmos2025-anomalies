<!--
---
title: "Source Code"
description: "Pipeline source code for ETL, feature engineering, anomaly detection, and utilities"
author: "VintageDon"
date: "2026-04-05"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: source-code
---
-->

# Source Code

Python source code for the COSMOS2025 anomaly detection pipeline, organized by pipeline stage.

---

## Subdirectories

| Directory | Description |
|-----------|-------------|
| [etl/](etl/) | FITS-to-PostgreSQL ETL pipeline (Phase 1 complete). Extraction, schema creation, and verification scripts |
| [features/](features/) | Derived feature computation (scaffolded, Phase 2) |
| [detection/](detection/) | Anomaly detection methods — Isolation Forest, SOM, statistical tests (scaffolded, Phase 2) |
| [utils/](utils/) | Config loading, DB helpers, shared utilities (scaffolded, Phase 2) |

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [AGENTS.md](../AGENTS.md) | Agent instructions and project context |
| [configs/](../configs/) | Configuration files consumed by source code |
