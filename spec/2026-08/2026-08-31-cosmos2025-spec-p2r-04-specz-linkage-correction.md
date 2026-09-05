<!--
---
title: "Phase 2 Restart Unit 4: Spec-z Linkage Correction and Measurement-Level Mirror"
description: "Mirror the measurement-level spec-z compilation, correct the catalog-to-compilation join path, annotate the defective upstream identifier, and characterize the recovery populations and selection bias without deciding their policy"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.0"
status: "Active"
tags:
  - type: specification
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
  - tech: python
  - tech: postgresql
  - tech: astropy
related_documents:
  - "../cosmos2025-anomalies/AGENTS.md"
  - "../cosmos2025-anomalies/docs/research/etl-v2-verification.md"
  - "../cosmos2025-anomalies/docs/reference/schema-v11.md"
  - "../cosmos2025-anomalies/docs/reference/data-manifest-v1.1.md"
  - "2026-08/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md"
  - "../docs/workload-guidance/astronomy.md"
---
-->

# Spec P2R-04: Spec-z Linkage Correction and Measurement-Level Mirror

**Task 4 of the Phase 2 restart series.** Gates: 4.1 through 4.10.

Predecessor: P2R-03 (ETL v2 lossless mirror), merged to `main`. Successor: the spec-z science surface unit, which does not dispatch until this spec's review surface carries recorded operator dispositions. T_A v2 may proceed in parallel on non-spectroscopic axes but must not use spectroscopy for calibration or validation until that successor lands.

**Mode: central-queue repo execution.** This file in the central active queue is the authorization; the target repository is `/opt/agents/repos/cosmos2025-anomalies`. Follow that repository's "Executing a Work Spec" contract for branch and per-gate commits. Use the current central worklog template and `spec-closeout` skill for worklog naming, frontmatter, runtime evidence, registry indexing, attestation, and archive position. Working branch: `task/4-specz-linkage-correction`.

**Startup prerequisites.** `main` must contain the P2R-03 merge commit and the spec archive repair that accompanied it, such that `spec/2026-08/` holds three archived specs. `cosmos2025_v11.source` must hold twelve relations with the row counts recorded in `source.provenance`. `docs/research/etl-v2-verification.md` must be present. The speczcompilation checkout must be clean at its manifest-pinned HEAD, and both `specz_compilation_COSMOS_DR1.1_all.fits` and `specz_compilation_COSMOS_DR1.1_unique.fits` must have manifest rows whose declared SHA-256 the executor freshly reproduces. Any missing predecessor evidence, count disagreement, unclean checkout, absent manifest row, or hash mismatch stops before branch creation.

---

## Objective

At completion, `cosmos2025_v11.source` holds the measurement-level spec-z compilation as `specz_compilation_all` alongside the existing galaxy-level table, renamed `specz_compilation_unique`, both mirrored losslessly under the P2R-03 dictionary contract with provenance rows, generated comments, conformance coverage, and full-coverage value reconciliation. `photometry_primary.id_specz_khostovan25` carries a database comment recording that it does not resolve against the held DR1.1 compilation, with the evidence locator.

A linkage evidence report characterizes the correct join path through `Id_COSMOS25`, the two recovery populations the corrected path exposes, and the spectroscopic selection function of the defective path. It states recommended dispositions as closed questions and decides none of them. No analysis schema, no materialized join, no view, and no spectroscopic sample definition exists at completion.

---

## Why This Exists

P2R-03 gate 3.8 required the executor to compute the `id_specz_khostovan25` to compilation match against a live-side prior of 37,219 and to state any discrepancy rather than reconcile it away. It did, and the discrepancy reached the verification surface: 37,219 non-sentinel links, of which a substantially smaller number resolve. That instruction is why this unit exists rather than the gap being absorbed into a footnote.

Investigation between 2026-08-30 and 2026-08-31 established, from the mirror and the pinned FITS artifacts, that the identifier is not merely lossy. It is addressing a namespace the held compilation does not use. The corrected path exists and is exact. Three things follow, and an executor that does not understand them will make the wrong repair.

**The catalog's own pointer is not recoverable and must not be repaired by inference.** Its values span a range roughly a third of the compilation's identifier range, its block-shift structure indicates an earlier compilation release, and no artifact we hold defines the mapping. The tempting move is a positional or coordinate-based reconstruction of what it "meant". That would manufacture a linkage upstream never published, and it would be indistinguishable from a correct one in every downstream product. The column is mirrored as shipped, annotated, and not repaired.

**The correct path is a lateral one that is easy to miss.** The compilation carries its own crossmatch into COSMOS-Web. Its stored coordinates were observed to be verbatim identical to the mirror's own, at zero separation. Anyone joining the two products by the documented column gets a scrambled sample and no error.

**The corrected path exposes populations that require a policy decision, not an ETL default.** Some catalog sources appear in the measurement-level surface but not the galaxy-level one, meaning every measurement currently crossmatched to them was demoted in deduplication. Promoting one is a scientific selection decision. Some catalog sources are named by more than one compilation entry. And resolution status under the defective column correlates strongly with spectroscopic confidence, so any sample built on it is quality-conditioned in a way nothing in the catalog signals.

The silent failure this unit is designed against is a spectroscopic validation set that looks clean, joins without error, and is drawn from the wrong galaxies. A wrong redshift attached to a real source types cleanly, validates cleanly, and surfaces as a scientific result.

---

## Prior Observations, To Be Verified

Every number below was measured during investigation and is a **prior expectation the executor confirms against the artifact**, not a fact to restate. A disagreement is a finding for the review surface and does not halt the unit unless a validation names it as halting. The executor records observed values alongside these priors in every case.

| Observation | Prior |
|---|---|
| Non-sentinel `id_specz_khostovan25` values, all distinct | 37,219 |
| Of those, resolving against the galaxy-level table by `Id_specz` | 24,364 |
| Not resolving | 12,855 |
| Range of stored link values | 223 to 165,312 |
| Compilation `Id_specz` range, measurement level | 1 to 487,666 |
| Measurement-level rows; galaxy-level rows | 482,579; 261,975 |
| Galaxy-level set equals measurement-level rows at `Priority = 1` | full row and column equality |
| Stored `ra_COSMOS25`/`dec_COSMOS25` versus mirror coordinates at that id | zero separation, all rows |
| Measurement to matched source separation, compilation crossmatch | median 0.084 arcsec, ceiling 0.998 |
| Measurement to source named by `id_specz_khostovan25` | median 4,054 arcsec |
| Distinct sources via galaxy-level `Id_COSMOS25` | 45,007 |
| Distinct sources via measurement-level `Id_COSMOS25` | 46,039 |
| Sources with a usable non-sentinel redshift, galaxy level | 39,165 |
| Catalog-flagged sources absent from the galaxy-level surface | 3,062 |
| Catalog-flagged sources absent from the measurement-level surface | 2,378 |
| Catalog sources named by more than one galaxy-level entry | 185, across 371 rows |

The investigation artifact is `staging/cosmos_specz_linkage_probe.py`, which is ignored by Git and is evidence rather than a deliverable. The executor may read it; it must not treat its output as verification.

---

## Execution Environment

Deltas from P2R-03 only.

| Item | Value |
|------|-------|
| Executor requirement | `box-required`. Reads pinned FITS on ML01; writes psql01. |
| Reasoning effort | High on 4.1 and 4.7, which carry the analysis. Standard elsewhere. |
| Attended | The run does not pause for review. See the blocked-signal channel below for how it surfaces a stop. |
| Toolchain | Shared ML01 venv, per the astronomy workload guidance. |

**Environment selectors are startup observations, not authored facts.** The Doppler project and config in use, the admin variable names, and the venv path are read from `configs/data_paths.yaml` and the live environment at startup and recorded in the worklog. This spec does not name a Doppler config. A prior spec in this series authored one and it was wrong.

**Principal preflight.** This unit creates no new role, but it creates tables that an existing principal must be able to read. P2R-03 established `cosmos2025_v11_ro` with `ALTER DEFAULT PRIVILEGES FOR ROLE <owner>`, which applies only to objects created by that same owner role. Before any DDL, confirm that the connecting identity is the role named in those default-privilege entries. If it is not, new tables will be created without the analyst grant, every structural check will pass, and the read-only path will silently lose the new tables. Confirm it, and confirm the grant landed after creation rather than assuming inheritance.

---

## Reversal

Phased around a declared seal, with its cost stated.

**Before the seal.** Effects are one new table, one table rename, and ordinary branch commits. Full reversal is `DROP TABLE source.specz_compilation_all`, rename back, drop the branch. Cost is one reload of roughly 482,579 rows from a 200-megabyte-class FITS file, measured in minutes.

**The seal.** The load seal is declared at the end of gate 4.5: `source.specz_compilation_all` has passed its row-count, key-uniqueness, null-encoding, and full-coverage value reconciliation checks, and `specz_compilation_unique` has passed post-rename re-verification. The worklog records the seal explicitly with the gate SHA.

**After the seal.** The loaded data is validated work. Reversal of an administrative, documentation, conformance-generation, or verifier-code failure is repair in place, not reload. Dropping and reloading a sealed table for a failure that is not a data-integrity failure requires explicit operator authorization through the blocked-signal channel.

**Destructive-retry budget: two, cumulative across the unit.** A destructive retry is any drop-and-reload of a table that has passed its load gate, or any drop of the target database. On exhausting the budget the executor stops and signals rather than attempting a third.

No effect in this unit falls into the `provenance` or `publication` classes. The manifest is read and never re-pinned. The `cosmos2025` v1 database is not a write target. The `analysis` schema is not created.

---

## Recovery Latitude

The executor may preserve validated work and pursue the narrowest recovery consistent with the invariants below. It is expected to prefer in-place repair over reload whenever the invariants hold, and to record the reasoning.

Invariants that may never be traded for speed:

- Loaded values equal source values exactly after the declared cast. No tolerance, no coercion, no repair of a mismatch by adjusting the comparison.
- Only FITS masks and NaN become SQL NULL. Every finite value, including sentinels, is stored unchanged.
- Manifest-declared and freshly observed source hashes are separate evidence and must be equal before a read.
- No inferred linkage. An unresolved identifier is a finding.

Anything not on that list is negotiable in service of not repeating work.

---

## Blocked-Signal Channel

Unattended means no scheduled review checkpoints. It does not mean the run never needs the operator.

On a block, the executor writes `staging/BLOCKED-p2r-04.md` containing the gate number, the condition, what it has already tried, and the specific authorization or decision it needs, then appends the same content to the worklog under a `BLOCKED` heading, then stops. It does not proceed on an assumption, and it does not spend the retry budget trying to route around a decision that belongs to the operator.

This file location is provisional pending an estate-level decision on notification paths, and is declared here so the executor has somewhere to write rather than nowhere.

---

## Scope

### Pre-existing (do not create)

- `cosmos2025_v11` with schema `source`, twelve relations, and role `cosmos2025_v11_ro`, as built and verified by P2R-03.
- `data/dictionary/columns-v11.csv` and its README: the sealed dictionary, extended by this unit rather than rebuilt.
- `src/etl/` generators from P2R-03: dictionary loader, schema generator, provenance loader, conformance generator, reconciliation modules, verification-surface generator. Reuse them. This unit adds source coverage to an existing pipeline; it does not author a second one.
- `docs/reference/data-manifest-v1.1.csv` and the sealed speczcompilation boundary.
- Both compilation FITS artifacts in the pinned checkout.

### Modify

- `data/dictionary/columns-v11.csv` and `data/dictionary/README.md`
- `src/etl/schema_v11.sql` and the generators, where extension is required
- `src/etl/` new loader for the measurement-level table, and a rename/re-verify utility
- `src/etl/conformance_cases_v11.py` and the conformance generator output
- `configs/data_paths.yaml`
- `docs/reference/schema-v11.md`
- `docs/research/specz-linkage-evidence.md` (new; the review surface)
- `docs/project-state.md`, `AGENTS.md`, and `README.md` where the table inventory or the spec-z statement becomes stale
- `tests/` and `tests/README.md`
- `work-logs/2026-08-31-cosmos2025-worklog-p2r-04-specz-linkage-correction.md`
- The work registry row appended at closeout
- This central spec and its archive move at closeout
- Interior READMEs and orientation indexes the docs pass makes stale
- Database objects: `source.specz_compilation_all` (new), `source.specz_compilation` renamed to `source.specz_compilation_unique`, `source.provenance` rows, and column comments

### Reference (consult, do not modify)

- `AGENTS.md`: lifecycle contract and architectural constraints.
- `docs/research/etl-v2-verification.md`: the P2R-03 evidence this unit builds on, including the spec-z findings carried forward.
- `docs/reference/schema-v11.md`: the as-built contract the extension must remain consistent with.
- The compilation's own README in the pinned checkout: the authoritative definition of the two artifacts and the deduplication rule. Cite it; do not paraphrase it into the dictionary without a locator.
- `staging/cosmos_specz_linkage_probe.py`: investigation evidence, not a verification tool.

### Do not touch

- **The `cosmos2025` v1 database.** It is the T_A v2 comparison baseline and cannot be rebuilt; upstream replaced the v1 downloads in place.
- **`/mnt/nvme01/` and the speczcompilation checkout.** Manifest-pinned and immutable. Read and hash only; never move a git HEAD.
- **`data-manifest-v1.1.{csv,md}` and the SED digest sidecar.** Re-pinning is an effect with no undo. This unit reads the manifest and reproduces hashes from it; it does not regenerate it.
- **The seven master mirror tables, the three supplements, and their loaded values.** The only change to `photometry_primary` is a column comment.
- **The `analysis` schema.** Reserved. Creating it here would put a science-policy artifact in a unit whose policy questions are still open.
- **Any materialized join, view, or spectroscopic sample.** The corrected join is characterized in evidence and not built.
- **`id_specz_khostovan25` values.** Mirrored as shipped. No repair, no remap, no coordinate reconstruction, no null-out.
- **Doppler secrets, MetaMCP configuration, and `pg_hba.conf`.** Operator surfaces.
- **Tension science.** No `chi2_ratio`, no analysis sample, no tension scalars.

---

## Deliverables

Gate discipline, stated once: each gate ends in one commit referencing its gate number, and a worklog checkpoint. Data decisions first, architecture second.

### Deliverable 1: Reproduce the linkage evidence (gate 4.1)

Independently reproduce the prior observations table above from the mirror and the pinned FITS, without consulting the investigation script's output. Record every observed value against its prior.

Establish four things by measurement, each of which the later gates depend on:

1. **Identifier semantics.** Whether `Id_specz` is unique across the measurement-level artifact, and whether the galaxy-level artifact's `Id_specz` set equals the measurement-level rows at `Priority = 1` by full row and column equality rather than set equality alone.
2. **Namespace validity.** Whether `ra_COSMOS25`/`dec_COSMOS25` equal `photometry_primary.ra`/`dec` at the row named by `Id_COSMOS25`. Separation, not string equality, and reported as a distribution rather than a boolean.
3. **Defective-path geometry.** The separation distribution between each linked measurement's corrected coordinates and the source named by `id_specz_khostovan25`, compared against the same distribution for the compilation's own crossmatch. Both distributions, not a summary verdict.
4. **Value-range incompatibility.** The observed range of stored link values against the compilation's identifier range, with the count of stored values exceeding the compilation's maximum.

**Validation:**

- [ ] Every prior in the observations table has an observed counterpart recorded; agreements and disagreements are both stated with both numbers
- [ ] `Id_specz` uniqueness is asserted across the measurement-level artifact, with the observed distinct count and total
- [ ] Galaxy-level equivalence is tested by column-set equality plus per-column value equality including masks and NaN, not by `Id_specz` set equality; the result is reported either way
- [ ] The `Id_COSMOS25` coordinate check reports a separation distribution over all rows carrying both a valid identifier and valid coordinates, with the count of rows excluded and why
- [ ] Both geometric distributions are reported at minimum, median, 90th, 99th, and maximum
- [ ] A mutation test perturbing one stored coordinate by 0.5 arcsec in a scratch copy causes the namespace check to report a non-zero separation, proving the check is not returning zero for a structural reason
- [ ] No linkage is inferred, repaired, or written at this gate

### Deliverable 2: Dictionary extension (gate 4.2)

Extend the sealed dictionary with one row per native field of the measurement-level artifact, following the P2R-03 field contract exactly: source family, file, locator, exact source column name, source type, element count, target table `specz_compilation_all`, generated target identifier, target type, and `column_origin` of `source_native`. Apply the same deterministic identifier rule and the same fidelity-preserving type mapping. No metadata column is added to this table; it has no `source_row` and no injected `id`.

Populate the separate semantic fields from the compilation's own documentation, with locator and source SHA-256. Fields the compilation does not define are `undocumented_upstream` with empty description. Do not compose a description from a column name.

Rename the existing table's dictionary rows from `specz_compilation` to `specz_compilation_unique`, changing the target table only. No other field on those rows changes.

Add a sourced `semantic_note` to the `photometry_primary.id_specz_khostovan25` row recording that the identifier does not resolve against the held DR1.1 compilation, citing the gate 4.1 evidence and the review surface by path. Its `description_text` and `description_source` remain as shipped: upstream's description is what upstream said, and our finding is a project semantic note, not a correction to their text.

**Validation:**

- [ ] Native row count for `specz_compilation_all` equals the artifact's live `TFIELDS`; the observed value is recorded
- [ ] Every native field appears exactly once; zero collisions, reserved words, invalid characters, or overlength identifiers
- [ ] Zero rows carry a metadata `column_origin` for this table
- [ ] Every semantic field is either sourced with locator and SHA-256 or explicitly `undocumented_upstream` with empty description
- [ ] Exactly the `target_table` value changes on the renamed rows; a field-level diff confirms no other change
- [ ] The `id_specz_khostovan25` row's upstream description and source fields are byte-identical to their previous values, and the new content is in `semantic_note` with a source
- [ ] The dictionary parses under its fixed schema with no ragged rows
- [ ] A mutation test introducing a duplicate target identifier within `specz_compilation_all` fails the dictionary validator

### Deliverable 3: DDL generation and scratch verification (gate 4.3)

Regenerate `src/etl/schema_v11.sql` from the extended dictionary. It must produce the thirteen source relations: the eleven existing mirrors with `specz_compilation` renamed, the new measurement-level table, and `source.provenance` from its fixed contract. Every column carries a generated comment. Constraints on the new table come only from the pinned source contract established at gate 4.1; the executor must not invent a key.

Execute the full generated DDL in an isolated scratch database and drop it. The scratch execution is the discriminator: a generator that emits DDL which does not execute is a generator that has never been tested.

**Validation:**

- [ ] The generated DDL creates exactly thirteen relations in `source` and no view
- [ ] The DDL column set equals the dictionary table by table with zero additions and zero omissions, asserted in both directions
- [ ] Comment count equals dictionary row count for the mirror tables and the fixed contract count for provenance
- [ ] The new table's primary key is `Id_specz` if and only if gate 4.1 proved its uniqueness; otherwise the table carries no invented key and the omission is recorded
- [ ] The full DDL executes in a scratch database and the scratch database is dropped
- [ ] A mutation test removing one dictionary row causes a generated-versus-live column-set assertion to fail in scratch

### Deliverable 4: Rename and re-verify the galaxy-level table (gate 4.4)

Rename `source.specz_compilation` to `source.specz_compilation_unique`. Update its `source.provenance` row's `table_name`. Re-verify after the rename: row count unchanged, all column comments intact, the analyst role's SELECT still effective, and constraints preserved.

A rename is cheap and reversible, and it is done here because the existing name is ambiguous once a measurement-level table exists. A future consumer joining `specz_compilation` and believing it holds every redshift is the exact failure this removes.

**Validation:**

- [ ] `source.specz_compilation` no longer exists; `source.specz_compilation_unique` holds the same row count as recorded in provenance before the rename
- [ ] A row-level digest computed before and after the rename over a seeded sample is identical
- [ ] Every column comment survives the rename, verified by count and by a sampled comparison against the pre-rename values
- [ ] The provenance row's `table_name` is updated and every other field on that row is unchanged
- [ ] `cosmos2025_v11_ro` can still select from the renamed table
- [ ] No other relation in `source` changed name, owner, or row count

### Deliverable 5: Load the measurement-level mirror and declare the seal (gate 4.5)

Freshly hash the source artifact and compare against its manifest row before reading. Load `source.specz_compilation_all` under the P2R-03 load contract: only FITS masks and NaN become SQL NULL, every finite value including sentinels is stored unchanged, no transformation occurs.

Then run full-coverage value reconciliation on this table specifically, independently of the load path, re-reading the source fresh. Sample rows, not columns, with a recorded seed, and compare every loaded column. Equality is exact after the declared cast.

**On passing every check in this gate, declare the load seal in the worklog with the gate SHA.** From that point the reversal contract and retry budget above apply.

**Validation:**

- [ ] Observed source SHA-256 and byte count equal the manifest-declared values; a mismatch halts the unit
- [ ] Loaded row count equals the source row count; the prior of 482,579 is recorded as expectation, not forced
- [ ] `Id_specz` is non-null and unique across all rows, if gate 4.1 established that property
- [ ] Column count equals the dictionary count for this table
- [ ] Every loaded column reconciles against independently target-cast source values with zero mismatches; the seed, sample size, and column coverage in both directions are recorded
- [ ] NULLs reconcile only against FITS masks and NaN; a database NULL where the source carries a finite sentinel is a failure
- [ ] `cosmos2025_v11_ro` can select from the new table, and the grant is verified rather than assumed from default privileges
- [ ] The seven master tables, three supplements, and the renamed galaxy-level table are unchanged, verified by row count and a seeded digest
- [ ] The worklog records the seal explicitly

### Deliverable 6: Provenance (gate 4.6)

Add a `source.provenance` row for the measurement-level table under the existing fixed field contract, carrying both manifest-declared and freshly observed source SHA-256 values as separate evidence, and a freshly computed hash of the manifest CSV used by the run.

**Validation:**

- [ ] Provenance holds twelve rows and the `table_name` set equals the set of relations in `source` excluding `provenance`
- [ ] The new row's manifest and observed hashes are both present and exactly equal, and neither was copied from the other
- [ ] `loaded_rows` equals the live count
- [ ] `manifest_ref_sha256` matches a fresh hash of the on-disk manifest CSV
- [ ] No existing provenance row changed except the `table_name` updated at gate 4.4

### Deliverable 7: Characterize the linkage, decide nothing (gate 4.7)

Produce the measurements the successor unit needs to set policy. This gate writes no join, no view, and no sample.

**The corrected path.** Distinct catalog sources reachable through `Id_COSMOS25` at galaxy level and at measurement level. Multiplicity distribution of compilation entries per catalog source in each. Distinct sources carrying a usable non-sentinel redshift, and the same broken out by the compilation's own confidence values without applying a threshold.

**Recovery population A, the measurement-level-only sources.** Catalog sources present in the measurement-level surface but absent from the galaxy-level one, meaning every compilation entry crossmatched to them carries `Priority = 0`. For each: how many entries, their confidence and flag values, their separation from the catalog source, and where the deduplication's chosen representative for the same spectroscopic source actually went, expressed as the catalog source that representative names and its separation. That last measurement tests the neighbour-promotion hypothesis rather than assuming it.

**Recovery population B, the multiply-named sources.** Catalog sources named by more than one galaxy-level entry. For each: the entries' redshifts, confidences, flags, surveys, and separations, and whether their redshifts agree.

**The selection function of the defective path.** Confidence and flag distributions for the catalog-flagged sources that resolve under `id_specz_khostovan25` against those that do not, reported as full distributions rather than means. Precision and recall of the defective column treated as a boolean flag, computed separately against the galaxy-level and measurement-level surfaces and labelled with which surface each figure refers to.

Redshift comparisons at this gate exclude sentinel values explicitly and restrict to unambiguous one-to-one mappings, or report per-group where a source carries multiple entries. Do not select arbitrarily among duplicates.

**Validation:**

- [ ] Every reported figure names the surface it was computed against; no precision or recall figure is stated without its denominator's surface
- [ ] Both recovery populations are enumerated with per-source detail sufficient for a policy decision, not summarized to a count
- [ ] The representative-destination measurement for population A is reported, and the neighbour-promotion hypothesis is stated as supported or unsupported by that measurement rather than assumed
- [ ] Redshift comparisons exclude sentinel values by an explicit stated rule and handle duplicates per-group; the excluded count is reported
- [ ] Selection-function distributions are full distributions; a mean alone fails this gate
- [ ] Zero rows were written to any table, and zero views exist, verified after the gate
- [ ] Every figure is reproducible from a committed script, and the script re-reads sources rather than consuming staging state

### Deliverable 8: Schema and project documentation (gate 4.8)

Regenerate `docs/reference/schema-v11.md` from the extended dictionary and the verified live database, covering thirteen relations. Document the two compilation artifacts as distinct upstream products with their own provenance, and record the observed relationship between them from gate 4.1 without presenting the galaxy-level table as derivable rather than shipped.

Refresh `docs/project-state.md`, `AGENTS.md`, and `README.md` only where the table inventory or the spec-z statement is now stale.

**Validation:**

- [ ] An `information_schema` diff against the schema document's listings is empty
- [ ] Both compilation tables are documented with separate provenance and their observed relationship stated as measured
- [ ] The `id_specz_khostovan25` entry carries the semantic note and points at the review surface
- [ ] Project state, AGENTS, and README agree with the live inventory and with each other
- [ ] Documentation passes the frontmatter checker and the writing style guide

### Deliverable 9: Review surface (gate 4.9)

Create `docs/research/specz-linkage-evidence.md`. Every finding carries an ID, a one-line statement, evidence with exact numbers and their source, and a closed question answerable yes or no.

It reports the gate 4.1 evidence with observed values against priors, the corrected path, both recovery populations, the selection function, and the mirror's new state.

It closes with the dispositions the successor unit inherits, each stated as a closed question with a recommendation and explicitly deferred: the selection rule for recovery population A, the rule for population B, which surface defines the spectroscopic sample, what confidence threshold applies, how the calibration and held-out validation split is drawn given the selection function, and whether the upstream defect is reported to the COSMOS-Web team.

Findings this spec already suspects are posed as questions to confirm or contradict from the evidence, never as answers to restate.

**Validation:**

- [ ] Every claim carries a number and a source: query, file, test, or worklog line
- [ ] Every finding has a stable ID and a yes/no closed question
- [ ] Observed values are reported against their priors in every case where a prior existed
- [ ] No recovery-population selection rule is applied anywhere in the repository or database
- [ ] The deferred questions are listed as questions, with recommendations marked as recommendations

### Deliverable 10: Closeout (gate 4.10)

Follow the target repository's per-gate commit contract and run the current `spec-closeout` skill for the documentation, consistency, worklog, registry, attestation, and archive evidence chain.

**Validation:**

- [ ] Branch `task/4-specz-linkage-correction`, no push, no remote operation
- [ ] One commit per gate, each referencing its gate number
- [ ] Worklog uses the current template, is checkpointed per gate, records the load seal and any destructive retries against the budget, distinguishes actual runtime facts from estimates, and is sealed with every gate SHA
- [ ] Registry row appended, category `astronomy`, matching the worklog
- [ ] This spec archived to its month folder and absent from the active queue
- [ ] `staging/BLOCKED-p2r-04.md` is absent, or its content is reproduced in the worklog with the resolution

---

## Human Approval Surface

`docs/research/specz-linkage-evidence.md`, produced at gate 4.9.

Operator disposition of that surface authorizes the spec-z science surface unit and unblocks spectroscopic calibration and validation for T_A v2.

---

## Constraints

- **Never infer a linkage.** The defective identifier is mirrored as shipped and annotated. Reconstructing what it meant by coordinate matching, positional offset, or block-shift inversion would manufacture a linkage upstream never published, and the result would be indistinguishable from a correct one downstream. An unresolved identifier is a finding.
- **Never promote a demoted measurement.** Selecting a `Priority = 0` entry for a source with no `Priority = 1` entry is a scientific selection decision belonging to the operator. Characterize the population; do not resolve it.
- **Never apply a confidence threshold.** The compilation's flags are source data. Report distributions; do not label a subset secure, and do not filter.
- **Never compose a description or unit.** Transcribe from a named source with a locator, or mark it undocumented. Project findings live in semantic notes, never in upstream description fields.
- **Never null by inference.** Only FITS masks and NaN become SQL NULL. Finite sentinels are stored unchanged, in this table as in every other.
- **The v1 database is not a write target.** It cannot be rebuilt.
- **The manifest is read, never re-pinned.** Re-pinning has no undo and its damage is invisible.
- **Secrets never enter evidence.** No credential value appears in a log, worklog, diff, test, or commit.
- **Prior findings are verified, not restated.** Every number in the observations table is a claim the executor confirms against the artifact.

---

## What the Executor May Choose

Chosen by the executor: module decomposition and file naming, iteration and batching strategy, staging versus direct COPY, test organization, the analysis and reporting approach at gate 4.7, worklog prose organization, and recovery strategy within the bounds set by the Recovery Latitude section.

Frozen by this spec: the two-table boundary and their names; the absence of metadata columns on the new table; type and identifier mappings inherited from P2R-03; the load and null contract; the prohibition on inferred linkage, promotion, and thresholding; the seal and the retry budget; the review surface and the questions it must leave open; and the exclusion of the analysis schema, any view, and any materialized join.

---

## Execution Order

1. Preflight: predecessor evidence, live inventory, manifest rows and fresh hashes, checkout cleanliness, connecting identity against the default-privilege owner
2. Gate 4.1 (reproduce the linkage evidence)
3. Gate 4.2 (dictionary extension)
4. Gate 4.3 (DDL generation and scratch verification)
5. Gate 4.4 (rename and re-verify)
6. Gate 4.5 (load, reconcile, declare the seal)
7. Gate 4.6 (provenance)
8. Gate 4.7 (characterize the linkage)
9. Gate 4.8 (schema and project documentation)
10. Gate 4.9 (review surface)
11. Gate 4.10 (closeout)

---

## Notes

**On why this is not folded into T_A v2.** The spectroscopic sample is an input to T_A v2's calibration and validation. Discovering mid-analysis that the sample was drawn through a broken pointer would invalidate whatever had been calibrated against it, and the invalidation would surface as a scientific result rather than an error. This unit ends before any policy decision so that T_A v2 inherits a correct foundation and an explicit selection function rather than a plausible-looking join.

**On the rename.** It is the one change here that touches an artifact the operator already approved. It is included because the cost of leaving `specz_compilation` ambiguous is paid by every future consumer, and because the dictionary-driven pipeline means the regeneration cost is being paid anyway to add the second table. Gate 4.4 exists to prove the rename cost nothing.

**On what this unit deliberately does not decide.** Both recovery populations, the spectroscopic sample definition, the confidence threshold, the calibration and validation split, and the upstream report are successor work. This unit makes the linkage correct and its selection function visible, so that those decisions are made against evidence rather than against a default nobody chose.

**On the geometry.** The compilation's crossmatch was measured with a sub-arcsecond distribution and a one-arcsecond ceiling, which is the signature of a deliberate match radius. The defective path's distribution is field-scale. These are not two crossmatches disagreeing about hard cases; they are one crossmatch and one broken pointer, and the evidence should read that way rather than hedging.
