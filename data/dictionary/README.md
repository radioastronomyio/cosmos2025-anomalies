<!--
---
title: "ETL v2 Load Dictionary"
description: "Structural source-to-target dictionary for the COSMOS-Web v1.1 lossless mirror"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "0.1"
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

Gate 3.1 structural skeleton for the COSMOS-Web v1.1 lossless mirror. The
CSV records native source fields and the thirteen authorized master-table
metadata rows. Descriptions, units, semantic notes, null encodings, and
sentinel provenance are reserved for later dictionary gates.

---

## 1. Contents

```
dictionary/
├── columns-v11.csv     # Generated source-to-target structural mapping
└── README.md           # Scope and regeneration contract
```

---

## 2. Files

| File | Description | Status |
|------|-------------|--------|
| [columns-v11.csv](columns-v11.csv) | One row per native field plus seven `source_row` and six injected `id` rows | Active skeleton |

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
