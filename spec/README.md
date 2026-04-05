<!--
---
title: "Specs"
description: "Structured execution prompts for AI-assisted pipeline development (KC/OpenCode/Codex)"
author: "VintageDon"
date: "2026-04-05"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: agent-specs
---
-->

# Specs

Structured prompts for AI-assisted execution. Each spec is a self-contained instruction set for a specific task, designed to be fed to KiloCode, OpenCode, or Codex agents on ML01.

---

## Files

| File | Description |
|------|-------------|
| `spec01-etl-pipeline.md` | Phase 1 ETL pipeline — FITS extraction, parquet conversion, PostgreSQL loading |
| `spec02-infra-samba.md` | Infrastructure — Samba share configuration for cross-machine file access |
| `spec03-verification-report-html.md` | Enhancement of `verify_catalog.py` to generate an HTML report with embedded charts |
| `spec04-readmes-and-commenting.md` | Interior READMEs for all directories and dual-audience commenting on ETL scripts |
| `spec05-codex-review.md` | Codex-based code review of the ETL pipeline scripts |

---

## Naming Convention

`specNN-short-description.md` — sequential numbering, kebab-case description.

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [AGENTS.md](../AGENTS.md) | Agent instructions and project context |
