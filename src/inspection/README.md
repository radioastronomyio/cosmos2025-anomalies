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
├── check_frontmatter.py  # Documentation frontmatter/tag vocabulary checker
└── README.md             # This file
```

---

## 2. Files

| File | Description | Status |
|------|-------------|--------|
| [check_frontmatter.py](check_frontmatter.py) | Validates HTML-comment frontmatter and tag vocabulary across tracked Markdown files | ✅ Active |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Source](../README.md) | Parent directory |
| [v1.1 Structural Profile](../../docs/reference/master-catalog-profile-v1.1.md) | Consumes the profiling outputs |
