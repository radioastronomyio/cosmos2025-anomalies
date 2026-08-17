<!--
---
title: "ETL v2 Load Dictionary"
description: "Structural and semantic dictionary for the COSMOS-Web v1.1 lossless mirror"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "0.2"
status: "Active"
tags:
  - type: directory-readme
  - domain: etl
related_documents:
  - "[Dictionary Builder](../../src/etl/load_dictionary.py)"
  - "[Data Path Configuration](../../configs/data_paths.yaml)"
---
-->

# ETL v2 Load Dictionary

Gate 3.1 structural skeleton and Gate 3.2 semantic reconciliation for the
COSMOS-Web v1.1 lossless mirror. The CSV records native source fields, the
thirteen authorized master-table metadata rows, canonical source descriptions,
independently evidenced units, description status, and sourced project semantic
notes. Null encodings and sentinel provenance remain reserved for later gates;
Gate 3.4 remains responsible for the formal dictionary seal.

---

## 1. Contents

```
dictionary/
├── columns-v11.csv     # Generated structural and semantic mapping
└── README.md           # Scope and regeneration contract
```

---

## 2. Files

| File | Description | Status |
|------|-------------|--------|
| [columns-v11.csv](columns-v11.csv) | One row per native field plus seven `source_row` and six injected `id` rows, with Gate 3.2 semantics | Active, not yet sealed |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Parent](../README.md) | Repository data-product directory |
| [Dictionary Builder](../../src/etl/load_dictionary.py) | Regenerates and validates the CSV |

## 5. Regeneration

```bash
python src/etl/load_dictionary.py
python src/etl/load_dictionary.py --check
```

Both commands read paths from `configs/data_paths.yaml`. The check exits
nonzero if the tracked CSV differs from the live source structures.
