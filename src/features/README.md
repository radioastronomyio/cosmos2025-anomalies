<!--
---
title: "Feature Engineering"
description: "Derived feature computation for Phase 2 COSMOS2025 anomaly detection"
author: "VintageDon"
date: "2026-05-01"
version: "1.0"
status: "Phase 2 In Progress"
tags:
  - type: directory-readme
  - domain: feature-engineering
---
-->

# Feature Engineering

Derived feature computation for the COSMOS2025 anomaly detection pipeline. This directory contains Phase 2 scripts that transform verified catalog tables into joinable scalar data products for downstream anomaly detection and ARD release.

---

## 1. Files

| File | Description |
|------|-------------|
| `compute_tension_scalars.py` | Creates the plausibility-filtered analysis sample (`catalog.v_analysis_sample`), computes error-normalized LePhare/CIGALE disagreement metrics into `catalog.tension_scalars`, and generates `docs/phase2-tension-diagnostic-report.md` |

---

## 2. Database Objects

| Object | Type | Purpose |
|--------|------|---------|
| `catalog.v_analysis_sample` | Materialized view | One-column `id` filter defining the 553,830-source clean analysis sample. Applies catalog-security, CIGALE convergence, physical-plausibility, and information-content gates. |
| `catalog.tension_scalars` | Persistent table | One row per analysis-sample source. Stores raw deltas, propagated uncertainties, `t_mass`, `t_sfr_inst`, `t_sfr_100`, chi2 context, F770W coverage, and LePhare quiescent context. |

---

## 3. Usage

```bash
source /opt/agents/venv/bin/activate
cd /opt/repos/cosmos2025-anomalies
python src/features/compute_tension_scalars.py
```

The script is idempotent: it drops and recreates the materialized view and table, then writes the diagnostic report.

---

## 6. Related

| Directory | Relationship |
|-----------|--------------|
| [src/](../) | Parent directory |
| [etl/](../etl/) | Phase 1 FITS-to-PostgreSQL pipeline that populates the source catalog tables |
| [docs/phase2-tension-diagnostic-report.md](../../docs/phase2-tension-diagnostic-report.md) | Generated diagnostic report |
