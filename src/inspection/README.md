<!--
---
title: "Inspection"
description: "Structural inspection utilities for the COSMOS-Web v1.1 holdings"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: data-engineering
  - tech: python
  - tech: astropy
related_documents:
  - "[v1.1 Structural Profile](../../docs/reference/master-catalog-profile-v1.1.md)"
---
-->

# Inspection

Read-only inspection utilities for the COSMOS-Web v1.1 holdings at `/mnt/nvme01/cosmos-web-dr1-catalog`: manifest hashing, structural profiling, and the v1→v1.1 comparison evidence. Created by spec P2R-01; these scripts never write to the holdings or the database.

---

## 1. Contents

```
inspection/
├── check_frontmatter.py            # Documentation frontmatter/tag checker
├── build_data_manifest.py          # SHA-256 manifest of both provenance roots
├── profile_v11.py                  # HDU/row/column profiler, regenerable inventories
├── diff_v1_v11.py                  # v1-to-v1.1 column/ID-space classification
├── param_migration_evidence.py     # CIGALE/LePhare value comparison vs live v1
├── supplement_evidence.py          # Supplement value-level comparison vs live tables
└── README.md                       # This file
```

---

## 2. Files

| File | Description | Status |
|------|-------------|--------|
| [check_frontmatter.py](check_frontmatter.py) | Validates HTML-comment frontmatter and tag vocabulary across tracked Markdown files | ✅ Active |
| [build_data_manifest.py](build_data_manifest.py) | Pins the v1.1 holdings and spec-z compilation with SHA-256; LFS materialization check | ✅ Active |
| [profile_v11.py](profile_v11.py) | Profiles the catalog family to HDU/row/column level; `--check` diffs regenerated inventories | ✅ Active |
| [diff_v1_v11.py](diff_v1_v11.py) | Classifies column and ID-space deltas against documented and loaded v1 | ✅ Active |
| [param_migration_evidence.py](param_migration_evidence.py) | Sampled value comparison of CIGALE/LePhare parameters, per tile group | ✅ Active |
| [supplement_evidence.py](supplement_evidence.py) | Row counts and sampled value checks for LSS and group supplements | ✅ Active |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Source](../README.md) | Parent directory |
| [v1.1 Structural Profile](../../docs/reference/master-catalog-profile-v1.1.md) | Consumes the profiling outputs |
