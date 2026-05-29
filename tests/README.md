<!--
---
title: "Tests"
description: "Focused verification tests for COSMOS2025 anomaly detection scripts"
author: "VintageDon"
date: "2026-05-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: testing
---
-->

# Tests

Focused tests for repository scripts and generated SQL helpers. The current suite covers Phase 2 tension scalar SQL construction and report rendering safeguards.

---

## 1. Files

| File | Description |
|------|-------------|
| `test_compute_tension_scalars.py` | Tests the tension scalar SQL builder, markdown report renderer, and PostgreSQL numeric formatting edge cases |

---

## 2. Running Tests

```bash
/opt/agents/venv/bin/python -m pytest tests/
```

---

## 6. Related

| Directory | Relationship |
|-----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [src/features/](../src/features/) | Feature engineering code under test |
