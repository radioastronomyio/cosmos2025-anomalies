<!--
---
title: "Work Logs"
description: "Session-by-session execution logs for spec runs and standalone work"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-18"
version: "2.1"
status: "Active"
tags:
  - type: directory-readme
  - domain: work-logs
related_documents:
  - "[Worklog Template](../docs/documentation-standards/worklog-readme-template.md)"
  - "[Agent Instructions](../AGENTS.md)"
---
-->

# Work Logs

Chronological execution logs documenting what was done, what failed, and what was decided during each work session. Spec-gated runs append a checkpoint per gate and seal the log at closeout (see [AGENTS.md](../AGENTS.md), "Executing a Work Spec"); structure follows the [worklog template](../docs/documentation-standards/worklog-readme-template.md).

---

## Files

| File | Description |
|------|-------------|
| [worklog-2026-08-15-reentry-v11-inspection.md](worklog-2026-08-15-reentry-v11-inspection.md) | P2R-01 per-gate checkpoints: template conformance, environment repair, v1.1 manifest/profile/delta, readiness review |
| [2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md](2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md) | P2R-02 manifest repair, provenance closeout amendments, operator dispositions, and final evidence chain |
| [2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md](2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md) | P2R-03 Gates 3.1 through 3.14: dictionary, verified mirror, provenance, conformance, documentation, and closeout |

---

## Naming Convention

`worklog-YYYY-MM-DD-<slug>.md` — date-prefixed, slug mirroring the spec that authorized the work (`<slug>` shared with the spec filename).

The v1-era Phase 1 worklogs were removed with the old specs in commit `2b71b1b` and are retrievable from history.

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [spec/](../spec/README.md) | Specs that correspond to logged work sessions |
