<!--
---
title: "Documentation"
description: "Project documentation, reference materials, and research artifacts"
author: "VintageDon"
date: "2026-03-01"
version: "1.1"
status: "Active"
tags:
  - type: directory-readme
  - domain: documentation
---
-->

# Documentation

Project documentation including catalog reference materials, research artifacts, and infrastructure notes.

---

## Contents

```
docs/
├── project-state.md                # Live phase, database inventory, holdings
├── reference/                      # Schemas, profiles, manifests, conventions
├── research/                       # Opportunities, reviews, design records
├── documentation-standards/        # Templates, tagging, style guide
├── data-science-infrastructure.md  # Infrastructure reference
└── README.md                       # This file
```

---

## Subdirectories

| Directory | Description |
|-----------|-------------|
| [reference/](reference/README.md) | Column schemas, v1/v1.1 structural profiles, pinned v1.1 manifest, unit conventions, quality flags, upstream documentation |
| [research/](research/README.md) | Science opportunities (O1/O5), v1.1 readiness review, ETL one-pager, Phase 1 code review |
| [documentation-standards/](documentation-standards/README.md) | Document templates, tagging strategy, writing style guide, script header standards |

---

## Reference Documents

| Document | Description |
|----------|-------------|
| [project-state.md](project-state.md) | Current phase, live table inventory, data holdings, compute environment |
| [phase2-tension-diagnostic-report.md](phase2-tension-diagnostic-report.md) | 2026-05-02 tension pull distributions (generator output) |
| [verification-report.md](verification-report.md) | v1 ETL verification record (generator output) |
| [data-science-infrastructure.md](data-science-infrastructure.md) | Cluster infrastructure reference — psql01, gpu01, network layout |

---

## Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [AGENTS.md](../AGENTS.md) | Agent instructions and project context |
