<!--
---
title: "Agent Instructions"
description: "Repository identity, constraints, conventions, and the work-spec execution contract for cosmos2025-anomalies"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "2.0"
status: "Active"
tags:
  - type: policy
  - domain: documentation
related_documents:
  - "[Project State](docs/project-state.md)"
  - "[Unit Conventions](docs/reference/unit-conventions.md)"
  - "[Science Opportunities](docs/research/science-opportunities.md)"
---
-->

# Agent Instructions

## Repository Identity

Systematic anomaly detection on the COSMOS-Web DR1 photometric catalog
(Shuntov et al. 2025): catalog-level feature analysis across 37-band
photometry and two independent SED-fitting codes (LePhare, CIGALE), without
proprietary data or image-level analysis. The verified v1.1 ETL v2 mirror is
the release-driven data boundary. The v1 catalog remains a read-only baseline;
MetaMCP cutover, T_A v2, and disposition of the P2R-04 spec-z linkage review
surface (docs/research/specz-linkage-evidence.md) remain pending operator
approval. The catalog's `id_specz_khostovan25` column does not resolve
against the held DR1.1 compilation; the correct spec-z join path is the
compilation's `Id_COSMOS25` crossmatch, and no spectroscopic sample, view, or
materialized join exists until the operator disposes that surface.

## Context Loading

Agents working on this repository should load context in this order:

1. This file (`AGENTS.md`), which covers repository identity, constraints, and conventions
2. `README.md` for project overview and current state
3. `docs/project-state.md` for the live database inventory, data holdings, and phase posture
4. `docs/documentation-standards/` for templates and standards to follow
5. Any domain-specific docs referenced below:
   - `docs/reference/unit-conventions.md` before any cross-code quantity is computed
   - `docs/research/science-opportunities.md` for the selected analysis targets (O1/O5)

## Architectural Constraints

- Raw data is immutable. Never modify anything under `/mnt/nvme01/`; the SHA-256 manifest is the provenance anchor for everything downstream.
- The psql01 `cosmos2025.catalog` v1 schema is a read-only baseline. A needed
  write is a finding, not an action. Runtime mirror reads target
  `cosmos2025_v11.source` through the database-specific analyst contract after
  operator cutover.
- Config-driven paths only: source code reads paths and DB environment variable names from `configs/data_paths.yaml`; no hardcoded data paths or connection strings.
- Administrator credentials arrive only through `doppler run --project ml01
  --config dev -- <cmd>` and are bootstrap/verification-only. Runtime v1.1
  consumers use the fixed `PGSQL01_COSMOS2025_V11_*` handoff names. Never
  hardcode, log, or commit secrets; direct analyst HBA access from ML01 remains
  a pending operator infrastructure action.
- Only FITS masks and NaN become SQL NULL in the source mirror. Every finite sentinel
  remains a source value; future cleaning belongs in `analysis`.
- Science logic changes (tension formulas, SFR censoring handling, `chi2_ratio`) require an approved spec; executors record defects, they do not fix them in passing.
- Agents never delete tracked files; retired content moves to `recycle-bin/` with worklog justification.
- Executors never perform remote git operations (fetch, push, PR). The operator owns the remote.

## Documentation Conventions

- All Markdown files require YAML frontmatter (see `docs/documentation-standards/tagging-strategy.md`)
  - Exempt: standard repo furniture (CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, licenses) and source materials in `internal-files/`
- New directories require an interior README (see `docs/documentation-standards/interior-readme-template.md`)
- Script files require language-appropriate headers (see `docs/documentation-standards/script-header-*.md`)
- Follow dual-audience commenting (see `docs/documentation-standards/code-commenting-dual-audience.md`)
- Follow writing style conventions (see `docs/documentation-standards/writing-style-guide.md`)
- Agents never delete files; move unnecessary files to `recycle-bin/` with documented justification

## Commit Messages

- Present tense, imperative mood
- 72-character first line limit
- Spec-gated work: one commit per gate, first line referencing its gate number (e.g. `gate 1.5: repair executable environment`)
- Reference issues after first line

## Session Pattern

1. Load context (this file + README + project state)
2. Work within defined scope
3. Document changes appropriately
4. Update work-logs if significant work completed

## Executing a Work Spec

The central queue at `/opt/agents/repos/spec/` is the dispatch authority for
repo-mode work. This repository's `spec/` directory is an archive/index, not
an active queue. A dispatched central spec is the authorization; this section
is the procedure.

- **Branch:** `task/<n>-<slug>` off `main`, created at startup after `spec-startup` preflight. The executor notes the starting branch and base commit for the worklog.
- **Commits:** one commit per gate, each referencing its gate number. Closeout commits stop at local commits: **no push, no PR, no remote operations by the executor**; the operator reviews, pushes, and owns merges.
- **Worklog:** `work-logs/worklog-YYYY-MM-DD-<slug>.md`, appended per gate as checkpoints, sealed at close with per-gate commit SHAs and runtime facts.
- **Specs:** dispatch from `/opt/agents/repos/spec/`, named
  `YYYY-MM-DD-<series>-NN-<slug>.md`. Completed specs archive to the repository
  `spec/YYYY-MM/` index as part of the authorized closeout.
- **Closeout:** append one row to the central registry at `/opt/agents/repos/work-logs/work-registry.csv` following `spec-closeout` (ML01 estate: attestation trailers on the closeout commit, registry row with the same model string).
