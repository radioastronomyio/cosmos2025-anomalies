<!--
---
title: "Phase 2 Restart Unit 1: Lifecycle Re-entry and v1.1 Structural Inspection"
description: "Bring the repository current with the project template and lifecycle skills, repair retired environment assumptions, and produce a pinned, evidence-backed characterization of the local COSMOS-Web v1.1 file set ending at the ETL v2 approval surface"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Active"
tags:
  - type: specification
  - domain: astronomy
  - domain: cosmos-web
  - tech: python
  - tech: postgresql
  - tech: astropy
related_documents:
  - "../AGENTS.md"
  - "../docs/phase2-tension-diagnostic-report.md"
  - "../docs/reference/master-catalog-profile.md"
  - "/opt/agents/repos/project-template-repository/docs/documentation-standards/README.md"
---
-->

# Spec P2R-01: Lifecycle Re-entry and v1.1 Structural Inspection

**Task 1 of the Phase 2 restart series.** Gates: 1.1 through 1.13.

Task 2 (ETL v2: the clean v1.1 database rebuild) does not dispatch until this spec's readiness review is approved by the operator.

**Mode: repo.** This repository predates the lifecycle skills and does not yet carry an "Executing a Work Spec" contract in `AGENTS.md`. Gate 1.2 installs that contract; this run follows it as written here. Startup: run the `spec-startup` skill before the first deliverable. The working branch for this run is `task/1-reentry-v11-inspection`.

---

## Objective

At completion, the repository conforms to `project-template-repository` structure and documentation standards, carries a repo-mode work-spec contract in `AGENTS.md`, and no longer references retired paths or the retired `.env` loading pattern anywhere in executable code or configuration. The local COSMOS-Web v1.1 holdings at `/mnt/nvme01/cosmos-web-dr1-catalog` are pinned by a SHA-256 manifest, structurally profiled to the extension and column level, diffed against the documented v1 profile and the live v1 database, and the CIGALE and LePhare parameter-migration question is answered from value-level evidence rather than release notes. All of it converges on one readiness review document whose closed questions are the design inputs for ETL v2. Structurally: ETL v2 stops being designed from assumptions about the v1.1 files and becomes designed against their read structure.

---

## Why this exists

The project restarted on 2026-08-15 with a decision to retire the v1 catalog entirely and rebuild on v1.1. The repository was last worked in May 2026 and predates the lifecycle skills, the template repository's current form, and the Doppler credential migration (documentation was partly migrated; the executable was not). The v1.1 holdings were downloaded 2026-08-14/15 and have never been opened by this project.

The dangers in this unit are silent, which is why the validations discriminate rather than detect:

- A Git LFS pointer file hashes cleanly, manifests cleanly, and is not data. The speczcompilation checkout uses LFS.
- A CIGALE extension that silently carries v1 parameter values under a v1.1 filename would poison every downstream tension metric while validating perfectly at the schema level. Whether CIGALE physical parameters were recomputed for v1.1 is unknown and is answered here by comparing values, not by reading changelogs.
- Supplementary catalogs (LSS overdensity, group catalogs) join cleanly on source ID whether or not they are version-skewed against a recomputed photo-z. Skew status is recorded as evidence, not assumed away.

Prior findings from the May/July diagnostic work (the ~0.24 dex conditional mass offset, the censoring-dominated SFR tension ranking, the dimensionally incoherent `chi2_ratio`) are context, not facts to re-verify here and not defects to fix here. They are frozen inputs to the T_A v2 design unit, which runs after ETL v2. See Constraints.

**This unit writes no database objects and no data files.** Against psql01 and `/mnt/nvme01` it reads, hashes, counts, enumerates, and reports. Its only write target is the repository.

---

## Execution Environment

| Item | Value |
|------|-------|
| Executor requirement | `box-required`. The v1.1 files are local to ML01 and the comparison targets the live psql01 database. |
| Host | ML01 |
| Agent runtime | Claude Code (operator may dispatch another runtime; nothing here is runtime-specific) |
| Reasoning effort | High on gates 1.9 through 1.12; the rest is mechanical |
| Attended | The run does not pause for review. The operator reviews the readiness document after closeout; Task 2 is gated on that approval. |
| Toolchain | Shared ML01 venv at `/opt/agents/venv/` (astropy, numpy, pandas, psycopg2 expected; verify per `spec-startup`). Database credentials via `doppler run --project ml01 --config prd`. |
| Existing code | `src/` exists. `src/inspection/` does not exist yet and is created by this spec. |

---

## Scope

### Pre-existing (do not create)

- psql01 `cosmos2025` database, `catalog` schema: seven v1 tables plus `catalog.v_analysis_sample` and `catalog.tension_scalars`. Read-only in this unit.
- `/mnt/nvme01/cosmos-web-dr1-catalog/`: the v1.1 file set downloaded 2026-08-14/15 (master catalog, per-extension FITS products, LePhare PDFz pickle, LePhare SEDs HDF5, detection images, star masks, AGN/DESI cross-identification file, arXiv paper directory, column-description text).
- The speczcompilation git checkout, stated by the operator to be at `reference-files/speczcompilation`. Its absolute path is resolved and recorded in gate 1.7, not assumed.
- `/opt/agents/repos/project-template-repository/` and its `docs/documentation-standards/`.
- Lifecycle skills at `/opt/agents/repos/local-agent-skills/skills/`.
- The pre-flight commit (gitignore fix, Doppler config edits, this spec) is already on `main`; the tree is clean at startup.

### Modify

- `AGENTS.md` (restructure, gate 1.2)
- `CLAUDE.md` (new, gate 1.1)
- `docs/documentation-standards/` (new, gate 1.1)
- `recycle-bin/` (new, gate 1.1)
- `docs/project-state.md` (new, gate 1.2)
- `docs/reference/unit-conventions.md` (new, gate 1.2)
- `docs/research/science-opportunities.md` (new, gate 1.2)
- `spec/README.md` and `work-logs/README.md` (gate 1.4)
- `configs/data_paths.yaml` and `src/features/compute_tension_scalars.py` (environment and path repair only, gate 1.5)
- `src/inspection/` (new, gates 1.7 through 1.11)
- `docs/reference/data-manifest-v1.1.csv` and `docs/reference/data-manifest-v1.1.md` (new, gate 1.7)
- `docs/reference/master-catalog-profile-v1.1.md` and regenerated per-extension column inventories (new, gate 1.8)
- `docs/research/v11-readiness-review.md` (new, gate 1.12)
- Interior READMEs for every directory this spec creates or materially changes (gate 1.6)
- This spec file (amendments, archive move at closeout)
- `work-logs/worklog-2026-08-15-reentry-v11-inspection.md` (new, per-gate checkpoints)
- `/opt/agents/repos/work-logs/work-registry.csv` (one closeout row, category `astronomy`)

### Reference (consult, do not modify)

- `project-template-repository` in its entirety. It is the canonical source; copy from it, never edit it.
- `docs/reference/master-catalog-profile.md` and `docs/reference/columns-*.txt`: the documented v1 profile. These are the v1 evidence base for gate 1.9 and remain untouched as the historical record.
- `docs/phase2-tension-diagnostic-report.md`, `docs/verification-report.md`: prior findings.
- Live psql01 (read-only queries via Doppler-injected credentials).
- On-disk v1.1 documentation: `cosmosweb-dr1-detailed-column-descriptions.txt`, the arXiv paper directory, any README shipped with the holdings.

### Do not touch

- **Any DDL or DML against psql01.** The rebuild is not approved. The live v1 tables are the comparison baseline for gate 1.10; a stray write invalidates the baseline this unit exists to use. Read-only `SELECT` is the entire database surface of this spec.
- **Anything under `/mnt/nvme01/`.** Raw data is immutable, and gate 1.7 hashes it. A single modified byte after the manifest lands makes the manifest a lie. This includes the tempting cleanup of `detection_images.tar`, which duplicates the extracted directory: that is an operator disk decision, out of scope, and belongs as a note in the readiness review.
- **Science logic in `compute_tension_scalars.py`.** Gate 1.5 touches environment loading and path strings only. The broken `chi2_ratio`, the SFR censoring handling, and the tension formulas are T_A v2 design decisions reserved to a later spec with operator sign-off. An executor that "fixes" them here changes the recorded semantics of the v1 baseline products mid-comparison. If the repair work surfaces a defect, it is a finding for the review document, not an edit.
- **Git remote operations.** No fetch, no push, no PR. Closeout is local; the operator carries the push.
- **Deletion of any tracked file.** Retired content moves to `recycle-bin/` with a one-line justification in the worklog.

---

## Deliverables

Gate discipline, stated once: each gate ends in one commit referencing its gate number and a worklog checkpoint. Data decisions first, architecture second.

### Deliverable 1: Template structure install (gate 1.1)

Copy `CLAUDE.md`, `recycle-bin/`, and `docs/documentation-standards/` from the template repository. Customize `tagging-strategy.md` for this repository: the domain vocabulary must cover every domain tag already in use across the repo's frontmatter plus the tags used by this spec (`astronomy`, `cosmos-web`) and the ones the new documents will need. Hydrate copied templates' frontmatter for this repo; do not leave template placeholder text in committed files.

**Validation:**

- [ ] `CLAUDE.md`, `recycle-bin/README.md`, and all thirteen files of `docs/documentation-standards/` exist in-repo
- [ ] No committed file contains the literal string `HYDRATE` or template placeholder brackets
- [ ] Every domain tag that appears in any tracked file's frontmatter after gate 1.3 appears in `tagging-strategy.md` (checked again at 1.3; authored here)

### Deliverable 2: AGENTS.md restructure and work-spec contract (gate 1.2)

Rebuild `AGENTS.md` to template shape: identity, context loading, architectural constraints, documentation conventions, commit messages, session pattern, plus one new section, **Executing a Work Spec**, containing the repo-mode contract this run itself follows:

- Branch `task/<n>-<slug>` off `main`; one commit per gate referencing its gate number
- Worklog at `work-logs/worklog-YYYY-MM-DD-<slug>.md`, appended per gate, sealed at close
- Closeout stops at local commits. No push, no PR, no remote operations by the executor; the operator reviews, pushes, and owns merges
- Specs live in `spec/` named `spec-<series>-NN-<slug>.md`, active queue flat, completed specs archived to `spec/YYYY-MM/`
- Closeout appends one row to the central registry at `/opt/agents/repos/work-logs/work-registry.csv`

Relocate the deep content the current file carries, per the router pattern: current-state narrative and table inventories to `docs/project-state.md`; the log10/linear unit-convention note to `docs/reference/unit-conventions.md`; science opportunities (O1/O5 analysis) to `docs/research/science-opportunities.md`. AGENTS.md links each destination. Correct every stale fact in flight: data root is `/mnt/nvme01/cosmos-web-dr1-catalog`, catalog files are v1.1, LePhare SEDs and PDFz are now local to ML01, CIGALE per-source spectra are not downloaded (~175 GB, deferred), repo path is `/opt/agents/repos/cosmos2025-anomalies`. The relocated project-state document must reconcile its narrative with the May/July diagnostics: `t_sfr_100` is not "well calibrated" (censoring-dominated ranking), and the open items are the ones this restart addresses.

**Validation:**

- [ ] `grep -r '/mnt/nvme02\|/opt/repos/' AGENTS.md docs/project-state.md configs/` returns nothing
- [ ] The formula `delta = lephare_log10_value - LOG10(cigale_linear_value)` appears verbatim in `docs/reference/unit-conventions.md`
- [ ] All seven `catalog.*` table names and both Phase 2 product names appear in `docs/project-state.md`
- [ ] AGENTS.md contains an "Executing a Work Spec" section carrying the literal branch pattern `task/<n>-<slug>` and the no-push closeout rule
- [ ] `docs/project-state.md` states the censoring finding for `t_sfr_100`; the phrase "well calibrated" does not survive unqualified

### Deliverable 3: Frontmatter and tagging pass (gate 1.3)

Every tracked Markdown file outside the exemption set (CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, licenses) carries HTML-comment-wrapped YAML frontmatter with tags drawn from the customized vocabulary. Build the checker as a small utility (its home is the executor's choice; `tests/` or `src/inspection/`) so the check is repeatable, and run it as the validation.

**Validation:**

- [ ] The checker enumerates files from `git ls-files '*.md'` minus exemptions; every file parses valid frontmatter
- [ ] Every tag value across all frontmatter appears in `tagging-strategy.md`; the run output lists zero violations
- [ ] Mutation test recorded in the worklog: an out-of-vocabulary tag added to a scratch copy makes the checker fail

### Deliverable 4: Spec and worklog directory reconciliation (gate 1.4)

Rewrite `spec/README.md` for the lifecycle convention: flat active queue, `spec/YYYY-MM/` archive, `spec-<series>-NN-<slug>.md` naming. Record that spec01 through spec05 and the two Phase 1 worklogs were removed from the tree in commit `2b71b1b` ("removes centralized specs and worklogs post-migration") and are retrievable from history; the README must stop listing them as present. Align `work-logs/README.md` with the worklog convention and the template's worklog guidance.

**Validation:**

- [ ] The file table in `spec/README.md` matches the actual directory listing exactly (a generated listing diff is empty)
- [ ] `spec/README.md` cites `2b71b1b` for the removed specs; no removed file is described as present

### Deliverable 5: Executable environment repair (gate 1.5)

`configs/data_paths.yaml`: point `data_root` and every catalog, supplementary, PDFz, SED, and processed path at the actual v1.1 holdings under `/mnt/nvme01/cosmos-web-dr1-catalog`; add the per-extension v1.1 files and the speczcompilation path (absolute, as resolved in gate 1.7 planning; if 1.5 runs first, resolve it here and 1.7 confirms); remove the desktop `D:\` SED section, recording its retirement in the worklog. `src/features/compute_tension_scalars.py`: remove the retired `/opt/agents/.env` loading in favor of reading Doppler-injected environment variables per the config contract; correct usage text and docstring paths. No other change to that script (see Do not touch).

**Validation:**

- [ ] `grep -rn '/opt/agents/.env\|/mnt/nvme02\|/opt/repos/' src/ configs/` returns nothing
- [ ] Every filesystem path value in `data_paths.yaml` exists on disk, verified by a loop over the parsed config (processed/staging dirs may be created-on-demand; they are annotated as such and exempted explicitly, not silently)
- [ ] `doppler run --project ml01 --config prd -- python -c "<load config, connect, SELECT 1>"` succeeds
- [ ] `pytest tests/` passes unchanged

### Deliverable 6: Interior README pass (gate 1.6)

Every directory created or materially changed by gates 1.1 through 1.5 (`docs/documentation-standards/`, `src/inspection/` placeholder, `recycle-bin/`, plus any docs directory whose contents changed) carries an interior README per the template, and the parent READMEs' link tables are current.

**Validation:**

- [ ] A tree walk over tracked directories reports a README.md in every directory
- [ ] Each new README passes the gate 1.3 frontmatter checker

### Deliverable 7: Pinned data manifest (gate 1.7)

SHA-256, byte size, and mtime for every file under `/mnt/nvme01/cosmos-web-dr1-catalog/` recursively, and for the speczcompilation checkout: resolve its absolute path, record its git HEAD SHA, and verify LFS materialization for every LFS-tracked file (a pointer is a ~130-byte text file; the data is not). The `*_unique.fits` compilation catalog specifically must open under astropy with its row count recorded. Output: `docs/reference/data-manifest-v1.1.csv` (machine layer) and `data-manifest-v1.1.md` (summary with totals and the checkout SHA).

**Validation:**

- [ ] Manifest row count equals `find <root> -type f | wc -l` for each root, stated in the md summary
- [ ] Re-hashing three randomly chosen files reproduces the manifest values
- [ ] Every LFS-tracked file in the checkout is materialized: size inconsistent with a pointer and, for FITS, the file opens under astropy
- [ ] The speczcompilation HEAD SHA and the `_unique.fits` row count appear in the summary

### Deliverable 8: v1.1 structural profile (gate 1.8)

For each catalog-family FITS product (master, cigale, lephare, bulgedisk, galight_morph, ml_morph, photom_primary, photom_secondary, agngal_desi; star masks and detection images summarized at the header level only): full HDU list with EXTNAME, per-extension row counts, and machine-generated column name and dtype inventories mirroring the v1 `columns-*.txt` pattern. Output: `docs/reference/master-catalog-profile-v1.1.md` plus per-extension inventory files. The master catalog's extension count is settled here by enumerating EXTNAMEs, not by citing release notes.

**Validation:**

- [ ] Regenerating every column inventory from the FITS files and diffing against the committed inventories returns empty
- [ ] The profile states the master extension count with the EXTNAME list as evidence
- [ ] Row counts are recorded for every extension of every profiled file

### Deliverable 9: v1 to v1.1 delta (gate 1.9)

Column-level diff per extension against two v1 evidence sources: the documented profile (`columns-*.txt`, `master-catalog-profile.md`) and the live database's `information_schema` for what was actually loaded. Classify every column as unchanged, added, removed, renamed (with the mapping), or dtype-changed. Row-count deltas per extension. ID-space check against the live `catalog.photometry_core`: counts of retained, dropped, and new source IDs in v1.1, computed by actual set operations.

**Validation:**

- [ ] For each extension, the classification counts sum exactly to the v1 documented column count plus additions
- [ ] Retained, dropped, and new ID counts are reported with the query or code path that produced them
- [ ] Every rename claim shows both names; none is inferred from position alone

### Deliverable 10: Parameter migration evidence (gate 1.10)

The central question: did v1.1 recompute CIGALE physical parameters, or only photometry and LePhare products? Answer by value comparison. Draw a random sample of at least 50,000 source IDs present in both the v1.1 extension files and the live v1 tables. For CIGALE: exact-match fraction and delta distribution per column for mass, SFR (both timescales as named in the schema), and chi2, joined on source ID, split by tile group (B5/B9/B10 versus all others; obtain tile from the master extension if the CIGALE extension lacks it). For LePhare: same pattern for the primary photo-z, `mass_med`, and `sfr_med`. Rule, stated in advance: a per-column match fraction that is neither approximately 0 nor approximately 1 must be flagged explicitly in the review document as its own finding, never averaged into a summary.

**Validation:**

- [ ] Joined-row count equals the drawn sample size for each comparison (the join is verified, not assumed)
- [ ] Match fractions and delta distributions are reported per column, per code, per tile group
- [ ] The conclusion in the review document states changed or unchanged per code per tile group, citing these numbers, and any intermediate match fraction is flagged as a standalone finding

### Deliverable 11: Supplement and spec-z readiness evidence (gate 1.11)

Record the provenance of the LSS overdensity and group catalogs as held on disk and as loaded in the database (file hashes from gate 1.7, any version strings in headers or readmes). From on-disk v1.1 documentation only (the arXiv paper directory, column descriptions, shipped readmes; no web access assumed), extract what v1.1 changed and state whether the supplements shipped updated versions in the local holding. If local evidence cannot settle skew, record it as an open finding with a closed question for the operator. Separately, establish spec-z join readiness: count live `catalog` sources whose `id_specz_khostovan25` matches an `Id_specz` in the compilation's `_unique.fits`, reported against the known 37,219 linked sources and the 26,323 in the current analysis sample.

**Validation:**

- [ ] Supplement skew status is stated with file-level citations, or recorded as an open finding with a closed question; it is not resolved by assumption
- [ ] The spec-z join count is computed by an actual ID join and reported against both prior counts, with discrepancies stated rather than reconciled away

### Deliverable 12: Readiness review, the approval surface (gate 1.12)

`docs/research/v11-readiness-review.md`. Every finding carries an ID (F1, F2, ...), a one-line statement, evidence (file, section, query, or code path, with the exact numbers), and a closed question the operator can answer yes or no. Findings suspected before this task starts, each to be confirmed or contradicted from the evidence and never by citing this spec:

1. Does the v1.1 master catalog carry seven extensions against v1's six, and if so, what is the seventh?
2. Were CIGALE physical parameters recomputed for v1.1, or carried from v1?
3. Are LePhare photo-z changes concentrated in tiles B5/B9/B10?
4. Are the LSS and group supplements version-skewed against the v1.1 photo-z recompute?
5. Which photometry product (primary versus secondary) feeds ETL v2, and what distinguishes them structurally?
6. Is the speczcompilation join fully materialized and consistent with the 37,219 linked sources?

Close the document with the ETL v2 design questions the answers imply (extension-to-table mapping, per-extension file strategy, supplement handling, spec-z ingest as an ETL v2 gate), each as a closed question with a recommendation.

**Validation:**

- [ ] Every finding carries all four parts: ID, statement, evidence, closed question
- [ ] The six suspected findings are each addressed from the evidence produced by gates 1.7 through 1.11
- [ ] The document passes the frontmatter checker and follows the writing style guide

### Deliverable 13: Closeout (gate 1.13)

Follow the "Executing a Work Spec" section installed in `AGENTS.md` by gate 1.2.

**Validation:**

- [ ] Branch is `task/1-reentry-v11-inspection` with no upstream set and no remote operation performed
- [ ] One commit per gate, each referencing its gate number
- [ ] Worklog checkpointed per gate, sealed, recording per-gate commit SHAs
- [ ] One row appended to `/opt/agents/repos/work-logs/work-registry.csv`, category `astronomy`
- [ ] This spec moved to `spec/2026-08/` as part of the final commit

---

## Constraints

- **Do not write to psql01, in any form.** The live v1 tables are the comparison baseline; the rebuild is unapproved. A needed write is a finding, not an action.
- **Do not modify anything under `/mnt/nvme01/`.** Gate 1.7's manifest is the provenance anchor for every artifact ETL v2 will produce. A post-manifest write silently unpins the entire chain.
- **Do not repair science logic.** `chi2_ratio` and SFR censoring are known defects and they stay defective in this unit; their fix is a T_A v2 design decision the operator has not yet made. Record, do not adopt.
- **Do not resolve ambiguity by assumption.** An unresolvable path, an intermediate match fraction, an unverifiable version string: each is a finding with a closed question. A default is not.
- **Every claim traces to evidence.** This spec's own assertions about the file set, including the operator-stated speczcompilation location and the file listing that motivated this unit, are prior findings the executor verifies from the filesystem, never restates on this spec's authority.

---

## Execution Order

1. Gates 1.1, 1.2 (structure and contract exist before anything is documented against them)
2. Gates 1.3, 1.4, 1.5, 1.6 (conformance completes; 1.5's config repair defines the paths the inspection code loads)
3. Gate 1.7 (nothing downstream can be trusted until the inputs are pinned)
4. Gates 1.8, 1.9 (structure before comparison)
5. Gates 1.10, 1.11 (value evidence; depends on 1.8's column inventories and 1.7's materialization checks)
6. Gate 1.12 (the surface; consumes everything)
7. Gate 1.13: Closeout

---

## Notes

**On why this unit ends here.** The next action after approval is Task 2, ETL v2: pg_dump archive of the v1 schema (restore-tested, the declared reversal), schema drop and rebuild, extraction against the v1.1 file layout, load, verification, and a provenance table chained to gate 1.7's manifest hashes. Every one of those design choices is frozen by this unit's approved answers, which is the entire reason the approval sits between them. Task 2's spec is not written until the readiness review is approved.

**On what Task 2 will be allowed to choose.** Module decomposition, iteration strategy, and load mechanics. The extension-to-table mapping, the photometry product selection, supplement handling, the spec-z ingest policy, and the versioning posture are decided by the operator on this unit's review surface.

**On the pre-flight commit.** The gitignore repair, the standing Doppler documentation edits, and this spec were committed to `main` by the operator before dispatch, which is why the tree is clean at startup and why those files do not appear as work in this unit's gates.
