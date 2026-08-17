<!--
---
title: "Repository Data Products"
description: "Tracked structural data products generated from immutable source holdings"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: data-engineering
related_documents:
  - "[Data Path Configuration](../configs/data_paths.yaml)"
---
-->

# Repository Data Products

Tracked, deterministic data products that define ETL structure without
copying source catalog values into Git. Raw holdings remain outside the
repository and immutable.

---

## 1. Contents

```
data/
├── dictionary/     # Unified v1.1 load-column contract
│   ├── columns-v11.csv
│   └── README.md
└── README.md       # This file
```

---

## 3. Subdirectories

| Directory | Description |
|-----------|-------------|
| [dictionary/](dictionary/README.md) | Structural source-to-target column mappings for ETL v2 |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent project |
| [Data Paths](../configs/data_paths.yaml) | Configures source and output locations |
