<!--
---
title: "Specs"
description: "Active work-spec queue and lifecycle conventions for spec-driven execution"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "2.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: agent-specs
related_documents:
  - "[Agent Instructions](../AGENTS.md)"
---
-->

# Specs

Work specs for AI-assisted execution. A spec in this directory is the authorization for a repo-mode run; the execution contract (branch, per-gate commits, worklog, closeout) lives in [AGENTS.md](../AGENTS.md) under "Executing a Work Spec".

---

## Layout

- **Active queue (this directory, flat):** specs currently dispatchable or in execution.
- **Archive (`spec/YYYY-MM/`):** completed specs, moved there by the closeout commit. `YYYY-MM` derives from the spec's date.

Naming: `spec-<series>-NN-<slug>.md` (series such as `p2r` for the Phase 2 restart).

---

## Files

Active queue contents, generated from the directory listing:

| File | Description |
|------|-------------|
| `spec-p2r-01-reentry-v11-inspection.md` | P2R-01: lifecycle re-entry and v1.1 structural inspection, ending at the ETL v2 approval surface |

---

## Removed Content (historical note)

The v1-era specs `spec01-etl-pipeline.md` through `spec05-codex-review.md` and the two Phase 1 worklogs were removed from the tree in commit `2b71b1b` ("removes centralized specs and worklogs post-migration"). They are retrievable from git history (`git show 2b71b1b^:<path>`) and are **not** present in this directory. The Phase 1 work they authorized is recorded in `docs/verification-report.md`, `docs/research/phase1-precommit-codex-review.md`, and `docs/research/etl-pipeline-one-pager.md`.

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [AGENTS.md](../AGENTS.md) | Agent instructions and the work-spec execution contract |
| [Work Logs](../work-logs/README.md) | Per-gate execution logs for spec runs |
