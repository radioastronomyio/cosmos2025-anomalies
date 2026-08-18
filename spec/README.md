<!--
---
title: "Spec Archive"
description: "Repository-local archive and index for centrally dispatched work specs"
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

# Spec Archive

The central queue at `/opt/agents/repos/spec/` is the dispatch authority for
AI-assisted repository work. This directory is the repository-local archive
and index for completed specs; files here do not constitute an active queue.
The execution contract lives in [AGENTS.md](../AGENTS.md) under "Executing a
Work Spec."

---

## Layout

- **Central queue (`/opt/agents/repos/spec/`):** specs authorized for dispatch
  or currently in execution.
- **Repository archive (`spec/YYYY-MM/`):** completed specs moved here by their
  authorized closeout commit. `YYYY-MM` derives from the spec date.

Naming: `spec-<series>-NN-<slug>.md` (series such as `p2r` for the Phase 2 restart).

---

## Files

Repository archive/index contents:

| File | Description |
|------|-------------|
| [spec/2026-08/](2026-08/) | Completed repository-local spec archive; active dispatch remains central |

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
