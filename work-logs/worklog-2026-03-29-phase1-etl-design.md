<!--
---
title: "Phase 1 ETL Design & Infrastructure Migration"
description: "Repo scaffolding, data profiling, competitive landscape research, ETL schema design, data migration to ML01, database creation"
author: "CrainBramp"
date: "2026-03-29"
version: "1.0"
status: "Complete"
tags:
  - type: worklog
  - domain: [astronomy, data-engineering]
related_documents:
  - "[AGENTS.md](../AGENTS.md)"
  - "[ETL One-Pager](../docs/research/etl-pipeline-one-pager.md)"
  - "[Master Catalog Profile](../docs/reference/master-catalog-profile.md)"
  - "[ROADMAP.md](../ROADMAP.md)"
---
-->

# Phase 1: ETL Design & Infrastructure Migration

## Summary

| Attribute | Value |
|-----------|-------|
| Status | ✅ Complete |
| Sessions | ~6 (Feb 7 through Mar 29) |
| Span | 2026-02-07 to 2026-03-29 |
| Artifacts | ROADMAP.md, AGENTS.md, ETL one-pager, DDL, data_paths.yaml, catalog profile, KC/OC structured prompts |

Objective: Take the COSMOS-Web DR1 catalog from raw download through competitive landscape analysis, opportunity selection, catalog profiling, ETL schema design, infrastructure migration, and database creation, producing a fully specified handoff for agent-executed ETL.

---

## Work Completed

### Competitive Landscape (Feb 7)

Two independent deep research surveys (Gemini, GPT) assessed the COSMOS-Web DR1 publication landscape. Both converged on the same finding: the highest-ROI anomaly detection strategy exploits tension between independent measurements already present in the catalog. Eight claimed territories identified and documented as no-go zones. Five opportunities ranked. O1 (cross-code algorithmic disagreement) and O5 (contextual anomalies) selected as primary targets.

### Repository Scaffolding (Feb 7, Mar 1)

Repository structure established following project-template-repository conventions. AGENTS.md written with science context, data locations, tech stack. ROADMAP.md created with consolidated opportunity landscape, 4-phase execution plan, and ARD output track. Documentation standards, tagging strategy, and interior README pattern applied.

### Catalog Profiling (Mar 1)

Master catalog (8.4GB FITS, 6 extensions) structurally profiled. Extension column counts, data types, array vs scalar columns, sentinel value patterns, NaN distributions, and cross-extension alignment characterized. Profile script at `src/etl/profile_master_catalog.py`. Results documented in `docs/reference/master-catalog-profile.md`. Column schema reference files created for all 6 extensions.

### ETL Schema Design (Mar 1-15)

ETL one-pager written specifying: 4 parquet files from 4 extensions (skipping extensions 3 and 6), column inclusion/exclusion lists, sentinel-to-NULL mapping rules, column name sanitization (hyphens to underscores), id injection strategy, ssfr_cigale derived column. PostgreSQL DDL written at `src/etl/create_schema.sql` covering all 7 tables (4 core + 3 supplementary), indexes, and table-level comments.

### Data Migration to ML01 (Mar 29)

All catalog data except SED archives migrated from Windows desktop (`E:\`) to ML01 NVMe (`/mnt/nvme02/cosmosweb2025-dr1/`). This shifted the execution model: ETL runs on ML01 where the data lives. SED archives (~577GB total) remain on the desktop pending NAS capacity.

### Infrastructure Updates (Mar 29)

agents01 VM deleted from Proxmox cluster. All agent workloads consolidated to ML01 bare metal. AGENTS.md and data_paths.yaml updated to reflect ML01 paths. Database credentials sourced from `/opt/agents/.env`. crystaldb MCP dependency dropped in favor of direct psycopg2. cosmos2025 database created on psql01, DDL executed.

### Agent Handoff Prompts (Mar 29)

Two KC structured prompts written: one for the ETL pipeline execution, one for Samba share setup and skill file updates. Prompts follow the kc-structured-prompt skill pattern (deliverables with matched validations, implementation freedom within spec bounds).

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Skip extensions 3 (SE++APER) and 6 (B+D) | Array columns in ext 3 are unusable without restructuring. B+D is deferred to Phase 2. |
| ML01 as primary execution environment | Data locality. 128GB RAM handles the 8.4GB FITS in memory. A4000 available for ML phases. |
| Direct psycopg2 over MCP | CC/KC on ML01 can write Python scripts directly. No container intermediary needed for ETL. |
| O1 + O5 as primary targets | Highest novelty, lowest scoopability, pure catalog operations, complementary axes. |
| Sentinel conversion at extraction time | Prevents sentinel contamination in all downstream analysis. |

---

## Next Steps (completed in subsequent session)

ETL pipeline execution and verification. See `worklog-2026-04-05-phase1-verification.md`.

---

<!--
Source: Claude.ai project sessions, Feb-Mar 2026
Repo: https://github.com/radioastronomyio/cosmos2025-anomalies
-->
