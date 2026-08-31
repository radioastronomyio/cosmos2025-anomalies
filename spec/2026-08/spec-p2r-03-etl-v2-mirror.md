<!--
---
title: "Phase 2 Restart Unit 3: ETL v2 Lossless Mirror of COSMOS-Web v1.1"
description: "Build a unified machine-readable load dictionary proving complete coverage of all 1,349 master FITS columns and every loaded supplement/spec-z field, then load the release into a new cosmos2025_v11 database while leaving v1 untouched"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.7"
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
  - "../cosmos2025-anomalies/docs/research/v11-readiness-review.md"
  - "../cosmos2025-anomalies/docs/reference/data-manifest-v1.1.md"
  - "../cosmos2025-anomalies/docs/reference/master-catalog-profile-v1.1.md"
  - "../cosmos2025-anomalies/docs/reference/unit-conventions.md"
  - "2026-08/2026-08-16-cosmos2025-spec-p2r-02-manifest-amendment.md"
---
-->

# Spec P2R-03: ETL v2 Lossless Mirror of COSMOS-Web v1.1

**Task 3 of the Phase 2 restart series.** Gates: 3.1 through 3.14.

Predecessor: P2R-02 plus Amendment 1/P2R-02a, Amendment 2/P2R-02b, and Amendment 3/P2R-02c (exact manifest, evidence-chain, and final lifecycle repair). **This spec does not dispatch until the completed A3.3 stacked branch is merged to `main` with its readiness-review dispositions recorded.** Successor: T_A v2, which does not dispatch until this spec's verification surface is approved.

**Mode: central-queue repo execution.** This file in the central active queue is the authorization; the target repository is `/opt/agents/repos/cosmos2025-anomalies`. Follow the target repository's "Executing a Work Spec" contract for branch and per-gate commits. Use the current central worklog template and `spec-closeout` skill for worklog naming/frontmatter, runtime evidence, registry indexing, attestation, and central archive position; these current lifecycle sources supersede the repo's stale in-repo-spec and older worklog wording. Working branch: `task/3-etl-v2-mirror`.

**Startup prerequisites:** `main` must contain the final additive A3.3 closeout commit from P2R-02 Amendment 3/P2R-02c; commit `2f99326` is explicitly not sufficient. Identify A3.3 from branch history and its directly verified current-lifecycle attestation. The completed worklog must use the current central template, preserve the original gate 2.1/2.2 LFS evidence from `2e41631`, record every exact prior gate SHA through A3.2, and identify A3.3 relationally as its own containing closeout commit. The central predecessor spec must be archived at version 1.5, carrying its post-execution addendum recording the CIGALE SED disposition and the P2R-02d split, and absent from the active queue. `docs/research/v11-readiness-review.md` on `main` must carry a recorded operator disposition for all thirteen items (F1–F9, Q1–Q4) with no empty disposition cell. There is no signature artifact; the operator's merge of the A3.3 branch to `main` is the authorization. `docs/reference/data-manifest-v1.1.csv` must be byte-for-byte equal to the serialized `0f3e31d` baseline after removal of exactly its 29 `.git/**` records: exact ordered header, retained serialization and order, 155 data rows (103 NVMe catalog files and 52 complete speczcompilation worktree rows), zero `.git/**`, zero `cigale-seds/**`, no duplicate key, and no retained-field change. `docs/reference/data-manifest-v1.1-cigale-seds.csv` must be present and its aggregate must reproduce from the NVMe full listing: 1,185,322 files, 468,554,723,694 bytes. The committed discriminator tests and fresh read-only full verifier must pass. The authoritative central Markdown defect register must contain the four P2R-02 authored defects in its `SD-` namespace; both misplaced registers must be absent from active locations and preserved at their declared recycle paths. Exactly one P2R-02 registry row must point to the final worklog and archived spec and agree with the A3.3 attestation model identity and trustworthy usage policy. No active repo-local defect register may remain, and the target tree must be clean. Any missing predecessor evidence, empty disposition cell, malformed manifest contract, row-order drift, weak or failing discriminator, unresolved path, duplicate registry row, runtime-identity disagreement, missing attestation, or lifecycle disagreement stops before branch creation. Separately, `cosmos2025_v11` and role `cosmos2025_v11_ro` must not already exist; if either exists, stop for operator disposition rather than dropping, reusing, or overwriting it. The source-mirror sentinel contract in this approved spec supersedes the v1-era sentinel sentence in the current `AGENTS.md`; gate 3.12 removes that stale policy after the mirror is verified.

---

## Objective

At completion a new PostgreSQL database `cosmos2025_v11` on psql01 holds a lossless mirror of the declared COSMOS-Web v1.1 catalog boundary in schema `source`: all seven master catalog extensions with every FITS column preserved, the three supplement tables, and the spectroscopic redshift compilation. Vector columns remain PostgreSQL arrays rather than being flattened. The seven master tables additionally carry explicit relational metadata: zero-based `source_row` on all seven and an `id` injected into the six extensions that lack one natively, taken from primary photometry at the same source row. These fields are marked as project metadata; no science-derived column exists in the mirror.

A version-controlled unified load dictionary covers every native field loaded from all eleven source tables, proves separate complete coverage of the 1,349 master FITS columns, and carries the thirteen master-table metadata fields. It generates the DDL, database comments, schema documentation, and conformance tests. Source description, unit, project semantic notes, FITS null encoding, documented numeric sentinels, and candidate numeric sentinels have separate provenance fields rather than being collapsed into one status. A `source.provenance` table binds each loaded table to both the manifest-declared and freshly observed SHA-256 of the file it came from.

The executor uses the existing Doppler-injected cluster-admin variables only to create and load the new database. It also creates a dedicated read-only login `cosmos2025_v11_ro` for later MetaMCP use and writes its generated handoff values to gitignored `internal-files/cosmos2025-v11.env` with mode `0600`; it does not add or change Doppler secrets. The operator imports that handoff into Doppler later.

The existing `cosmos2025` database is untouched throughout. The unit ends at a verification surface. It computes no tension scalars and creates no analytical views.

---

## Why This Exists

The v1 load was a curated projection, and the curation removed the columns this project's science needs most.

Of the 287 columns in the primary photometry extension, v1 loaded 158: the 84 core scalars plus two of the five 37-band families. The three families it dropped are `flux_model`, `flux_err-uncal_model`, and `flux_err-cal_model`. The database therefore holds model magnitudes but not the model fluxes both SED codes were fit to, and neither error family. For a project whose entire thesis is that LePhare and CIGALE disagree and the interesting question is why, the input photometry is absent and so is the distinction between calibrated and uncalibrated flux errors, which is the quantity T_A normalizes tension by. ML morphology loaded 31 of 150 columns. B+D, SE++APER, and GALIGHT-MORPHO were not loaded at all; the last of these did not exist in v1.

The governing principle, adopted by the operator: **ETL is release-driven, not hypothesis-driven.** Research findings change what is studied, how measurements are cleaned and compared, and which anomalies are ranked. They must never force a return to the FITS files because a column looked irrelevant at the time. "No current research consumer" is not a valid exclusion reason and does not appear anywhere in this spec.

The v1 pipeline is a reference for technique only. Its column policy is encoded in code rather than in a reviewable artifact, its committed DDL drifted from the live database around `flag_star_hsc`, and 10 of its 331 columns carry a database comment. There is no v1 documentation style to carry forward; the phrase should not appear in the executor's reasoning.

The danger in this unit is silent. A wrong dtype fails a gate. A wrong unit, a mis-mapped column, or a sentinel nulled by inference passes every structural check and corrupts every downstream comparison, and the corruption surfaces as a scientific result rather than as an error. Two structures exist to contain that: the dictionary makes every semantic claim carry its provenance, and the reconciliation gate compares every one of the 1,349 columns against the source FITS rather than sampling columns.

---

## Execution Environment

| Item | Value |
|------|-------|
| Executor requirement | `box-required`. Reads local v1.1 FITS on ML01; writes psql01. |
| Host | ML01; database on psql01 (`10.25.20.8`) |
| Agent runtime | Long-horizon agent at high reasoning effort. The unit is fourteen gates of evidenced, fully reversible work. |
| Reasoning effort | High on 3.1 through 3.5 (dictionary construction, semantic reconciliation, sentinel profiling, fidelity verification). Standard on the generation and load gates, which are mechanical given a correct dictionary. |
| Attended | The run does not pause at any gate. The operator reviews the verification surface afterward. |
| Toolchain | Shared ML01 venv; credentials via Doppler (`doppler run --project ml01 --config prd`) |
| Preflight | Doppler authed with `PGSQL01_HOST`, `PGSQL01_PORT`, `PGSQL01_ADMIN_USER`, and `PGSQL01_ADMIN_PASSWORD`; venv carries astropy, numpy, pandas, psycopg2, pyarrow, pyyaml; psql01 reachable; admin can create a database and login role; target database and role absent; measured free space covers at least twice the estimated database plus staging, indexes, temporary files, and WAL headroom |

---

## Reversal

For resources created by this run only: terminate connections, `DROP DATABASE cosmos2025_v11`, revoke and `DROP ROLE cosmos2025_v11_ro`, and revoke the generated credential. The gitignored handoff file may then be removed by the operator. If the database or role exists before startup, this reversal is not authorized and the unit stops. The v1 database is not a write target, the NVMe holdings are read-only, and repository changes are ordinary commits on a branch. There is no irreversible gate in this spec, which is what licenses running fourteen gates unattended.

The MetaMCP redirect to the new database is an operator action taken after the verification surface is approved. It is **out of scope** for this unit and the executor does not touch MetaMCP configuration.

---

## Scope

### Pre-existing (do not create)

- `/mnt/nvme01/cosmos-web-dr1-catalog/`: the pinned v1.1 holdings, 103 catalog files, immutable. Includes `cosmosweb-dr1-detailed-column-descriptions.txt` (92,994 bytes), the upstream semantic source. The `cigale-seds/` subtree under this path is a declared out-of-boundary region pinned by aggregate digest; it is not read by this unit.
- `/opt/agents/repos/reference-files/speczcompilation/`: materialized, bounded to the worktree by P2R-02a, and sealed by P2R-02c.
- `docs/reference/data-manifest-v1.1.{csv,md}` and `data-manifest-v1.1-cigale-seds.{csv,md}`: as repaired and sealed by P2R-02/P2R-02a/P2R-02c/P2R-02d. P2R-02b failed review; its commits are retained as historical evidence only and are not the seal.
- `docs/reference/master-catalog-profile-v1.1.md` and the nine `columns-v1.1-*.txt` inventories.
- `docs/reference/unit-conventions.md`.
- The live `cosmos2025` database. **Read-only reference for this unit. Never a write target.**
- `src/etl/` v1 code and `src/inspection/` P2R-01 helpers.

### Modify

- `.gitignore` (allow the version-controlled dictionary CSV while retaining the general data-file ignore)
- `data/dictionary/columns-v11.csv` (new; the unified machine-readable load dictionary)
- `data/dictionary/README.md` (new; field definitions, provenance fields, and controlled vocabularies)
- `src/etl/build_dictionary.py`, `profile_values.py`, `generate_ddl.py`, `extract_v11.py`, `load_supplements.py`, `load_specz.py`, `verify_v11.py` (new; names are illustrative, decomposition is the executor's)
- `configs/data_paths.yaml` (add the v11 database target, the dictionary path, the per-extension inputs)
- `docs/reference/schema-v11.md` (new; the as-built schema reference)
- `docs/reference/sentinel-candidates-v11.md` (new; the profiling report)
- `docs/research/etl-v2-verification.md` (new; the approval surface)
- `AGENTS.md`, `README.md`, `docs/project-state.md`, and `spec/README.md` (as-built lifecycle, architecture, and orientation refresh)
- `assets/icon.svg` (operator-supplied flat project icon, present in the working tree at dispatch; commit it as-is. The existing banner and other assets remain in `assets/` but leave the README front page)
- `tests/` (new conformance tests, generated from the dictionary)
- `internal-files/cosmos2025-v11.env` (new, gitignored, mode `0600`; temporary credential handoff, never committed)
- `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md` (new; exact spec-mirrored name, current central template)
- Central registry indexing through `spec-closeout`, category `astronomy`
- This central spec and its lifecycle archive move
- Interior READMEs for `data/`, `data/dictionary/`, and any index the docs pass makes stale
- New database `cosmos2025_v11`, its `source` schema, and dedicated read-only role `cosmos2025_v11_ro` on psql01

### Reference (consult, do not modify)

- `AGENTS.md`: lifecycle contract.
- `docs/research/v11-readiness-review.md`: the recorded operator dispositions and their answered questions.
- `src/etl/extract_catalog.py` and `create_schema.sql`: v1 pipeline. **Technique only.** The extraction, clean, and COPY pattern and the psycopg2 usage carry forward. The column policy, the skip lists, and the sentinel handling do not, and must not be read as precedent.
- Yang et al. 2026, exact version `arXiv:2606.14869v1`, Table 1: the column-pattern definitions for GALIGHT-MORPHO. A read-only fetch of this exact arXiv version is authorized; record the fetched artifact SHA-256 and citation locator in the worklog before transcription.

### Do not touch

- **The `cosmos2025` database.** It is the comparison baseline for T_A v2 and the only surviving v1 artifact; upstream replaced the v1 downloads in place, so it cannot be rebuilt. No DDL, no DML, no rename, no drop.
- **`/mnt/nvme01/` and the speczcompilation checkout.** Manifest-pinned and immutable. The load reads; it never writes back, and it never moves a git HEAD.
- **`data-manifest-v1.1.{csv,md}` and the `cigale-seds` digest sidecar.** Re-pinned by P2R-02, repaired to the worktree-only boundary by P2R-02a, machine-contract sealed by P2R-02c, and split to a per-file catalog pin plus an aggregate SED digest by P2R-02d. Re-hashing or regenerating either would replace a reviewed pin with an unreviewed one, which is an effect with no undo.
- **Doppler and MetaMCP configuration.** The executor reads the existing admin variables from Doppler but creates or changes no Doppler secret. The MetaMCP redirect and import of `internal-files/cosmos2025-v11.env` are operator actions after approval.
- **Analytical layer.** No analytical views, science-derived columns, cleaned tables, or `analysis` schema. The thirteen declared relational metadata fields are the only non-native source-table columns. The name `analysis` is reserved for a successor spec; this unit does not create it.
- **Tension science.** No `chi2_ratio`, no SFR censoring logic, no `tension_scalars`, no analysis sample, no candidate ranking.
- **The AGN/DESI reference product.** Its roughly 18-million-row scale and separate release identity place it outside this catalog-mirror boundary. Absence of a current consumer is not the reason; it requires its own source and storage contract.
- **PDFz, the LePhare SED archive, and the CIGALE SED subtree.** Deferred, and the reason is shape rather than relevance: a per-source probability distribution over a redshift grid and a per-source spectrum are not relational rows, and ingesting them is a storage-design decision belonging to its own unit. T_z has a named need for PDFz; that need does not make this the right unit to satisfy it. The CIGALE SEDs are now local and pinned by aggregate digest rather than off-box, which changes their provenance status only. The 1,185,322 per-source SED files remain lookup assets for later triage, and this unit neither reads nor loads them.

---

## Deliverables

Gate discipline, stated once: each gate ends in one commit referencing its gate number, and a worklog checkpoint. Data decisions first, architecture second.

### Deliverable 1: Unified load-dictionary skeleton (gate 3.1)

Build `data/dictionary/columns-v11.csv` from the live source artifacts, not from P2R-01 inventories. It contains one row per native field loaded from the seven master extensions, the three supplement files, and the spec-z unique FITS table. The seven master extensions must separately reconcile to the live `TFIELDS` sum; 1,349 (287 + 43 + 148 + 56 + 150 + 461 + 204) is the prior expectation, not a number to force.

Add thirteen explicitly non-native master-table metadata rows:

- `source_row` on all seven master tables: zero-based row ordinal, target type `bigint`.
- `id` on the six master extensions that lack it: copied from `photometry_primary.id` at the same `source_row`. Primary photometry's `id` remains source-native.

Each row records source family, source file, source table/HDU or text-table locator, exact source column name, source type, element count, target table, target identifier, target type, and `column_origin` from `source_native`, `source_row_metadata`, or `id_injected`.

Type mapping is fidelity-preserving: `D` to `double precision`, `E` to `real`, `K` to `bigint`, `J` to `integer`, `I` to `smallint`, `L` to `boolean`, `nA` to `text`, and vector `nD`/`nE` to the corresponding PostgreSQL array type. Source names remain exact in the dictionary. Target identifiers are generated deterministically: lowercase; replace each maximal run outside `[a-z0-9_]` with `_`; prefix `c_` if the result does not begin with `[a-z_]` or is a PostgreSQL reserved keyword. Never truncate or hand-disambiguate. Any mapping collision within a table or any identifier over PostgreSQL's 63-byte limit halts the gate.

**Validation:**

- [ ] Native master-row count equals the sum of the seven live FITS `TFIELDS`; the live total and its comparison with 1,349 are stated
- [ ] Every native field from all eleven load tables appears exactly once; per-source native counts are recorded
- [ ] Exactly seven `source_row_metadata` rows and six `id_injected` rows exist
- [ ] Full inventory confirms only primary photometry has a native `id`
- [ ] Every target identifier maps back to exactly one source or metadata row within its table; zero collisions, reserved words, invalid characters, or overlength identifiers remain
- [ ] Zero rows have a null or empty target type
- [ ] Element counts come from source structure, not assumptions; every vector count is recorded
- [ ] Mutation tests for a wrong `D` mapping, an identifier collision, and an overlength identifier all fail the skeleton validator

### Deliverable 2: Semantic reconciliation (gate 3.2)

Populate separate semantic fields: `description_text`, `description_source`, `description_locator`, `description_source_sha256`, `description_status`, `unit`, `unit_source`, `unit_locator`, `unit_source_sha256`, `semantic_note`, `semantic_note_source`, `semantic_note_locator`, and `semantic_note_source_sha256`. The name `description_text` is intentional: source descriptions are canonicalized only by trimming ends and collapsing internal whitespace to one space, so multiline source text fits a line-oriented CSV without changing words. It is not mislabeled as raw. Validation applies the same canonicalization to the cited source block; the exact source remains recoverable through its locator and SHA-256.

Precedence:

1. The pinned `cosmosweb-dr1-detailed-column-descriptions.txt` for master extensions it documents: status `verified`.
2. Yang et al. 2026 `arXiv:2606.14869v1` Table 1 for GALIGHT-MORPHO: status `pattern_expanded`, with exact pattern, filter, version, locator, and fetched-artifact SHA-256.
3. Pinned supplement documentation and the pinned speczcompilation repository's own schema/flag documentation for their native fields: status `verified` when an exact field definition exists.
4. No source definition: status `undocumented_upstream`, `description_text` empty.
5. The thirteen relational metadata rows: status `project_derived`, with exact construction and purpose stated.

The GALIGHT per-filter pattern is not symmetric, and an expander that assumes it is will produce 208 rows rather than 204. Within each filter's bulge-disk error block there are eight columns, not ten: `nsersic` carries no error term for either the bulge or the disk component, while `rearc`, `mag`, `qratio`, and `phi` each do. The 51-per-filter breakdown is 10 single-Sersic, 10 bulge-disk parameters, 8 bulge-disk errors, 11 point-source, 6 fit statistics, and 6 Statmorph. Transcribe the asymmetry from Table 1; do not regularize it.

`ebv_stars` and `ebv_stars_err` remain `undocumented_upstream`; their names do not license a composed description. Units come from separately cited sources or are `unknown`; never infer a unit from a column name. Project semantic facts such as LePhare log10 and CIGALE linear conventions go only in `semantic_note` with `docs/reference/unit-conventions.md` as their source. They are never appended to `description_text`.

**Validation:**

- [ ] Every row carries exactly one of `verified`, `pattern_expanded`, `undocumented_upstream`, or `project_derived`
- [ ] Every non-empty source description equals the canonicalized cited source block; source path/reference, exact locator, and SHA-256 are present
- [ ] Every `pattern_expanded` row names its Yang Table 1 pattern and filter, and expansion reproduces exactly 204 GALIGHT rows
- [ ] Every `undocumented_upstream` row has empty `description_text` and unit `unknown` unless a separately cited unit source exists
- [ ] Exactly thirteen metadata rows are `project_derived`; no source-native row has that status
- [ ] Zero source descriptions were composed
- [ ] LePhare log10 and CIGALE linear statements appear in sourced semantic-note fields, not in upstream description fields

### Deliverable 3: Value, null-encoding, and sentinel profiling (gate 3.3)

Profile every native field read-only. Numeric scalars record null-mask fraction, NaN fraction, min, max, and the three most frequent exact finite values with counts. Numeric vectors record the same statistics separately for each array index. Text, boolean, and categorical fields record null fraction and frequent exact values appropriate to their type.

Do not force mutually exclusive sentinel states. Dictionary fields include `has_fits_mask`, `has_nan`, `documented_sentinel_values_json`, `documented_sentinel_evidence_text`, `documented_sentinel_source`, `documented_sentinel_locator`, `documented_sentinel_source_sha256`, and `candidate_sentinel_values_json`. A field may have both FITS null encoding and numeric sentinels. Documented values require an exact upstream citation. JSON-valued cells use canonical compact JSON arrays with stable ordering; candidate entries carry value, count, non-null fraction, and rule version.

The conservative candidate rule is frozen and recorded in code and the dictionary README: an undocumented finite numeric scalar whose absolute value is exactly an integer `10^k - 1` for integer `k >= 2` (99, 999, 9999, and so on), occurring at least `max(1000, 0.1% of non-null values)` in that scalar field or vector index, and not documented as a valid flag/category value. Candidates are observations only. This deliberately narrow screen is not claimed to discover every possible sentinel.

**Frequency does not establish sentinel-hood and this gate acts on no value.** Legitimately negative position angles, ellipticity components, M20, asymmetry, and Statmorph flag conventions remain untouched. The mirror stores documented and candidate numeric sentinels as source values.

**Validation:**

- [ ] Null-mask and NaN presence are recorded independently for every native field
- [ ] Every documented sentinel carries exact canonicalized source evidence text, source path/reference, locator, and SHA-256
- [ ] The exact `10^k - 1` candidate rule, threshold denominator, per-index behavior, JSON encoding, and rule version are deterministic, unit-tested, and reproduced in `docs/reference/sentinel-candidates-v11.md`
- [ ] Vector profiles are per index; no vector is summarized only by length or as one opaque value
- [ ] The candidates report lists suspect value, frequency, rule trigger, and known physical domain or `unknown`
- [ ] Zero source values were replaced, nulled, or altered during profiling
- [ ] The report visibly separates documented sentinels, candidates, FITS masks, and NaNs

### Deliverable 4: Dictionary seal (gate 3.4)

Freeze the unified dictionary and add `data/dictionary/README.md` defining every field, provenance rule, canonicalization rule, type mapping, identifier mapping, JSON-cell schema and stable ordering, and controlled vocabulary. Add the narrow `.gitignore` exception required to version `data/dictionary/columns-v11.csv`; retain the general CSV and data-directory ignores.

**Validation:**

- [ ] Zero rows are unclassified for column origin or description provenance; every null/sentinel field is populated with a value or explicit empty representation
- [ ] Native master count still equals the gate 3.1 live FITS total; all supplement and spec-z native counts still reconcile to their sources
- [ ] Exactly thirteen metadata rows exist and have `description_status = project_derived`
- [ ] `ssfr_cigale` and every other science-derived field are absent
- [ ] The README defines every dictionary field and all controlled values
- [ ] The CSV parses under a fixed schema with no ragged rows or embedded newlines
- [ ] `git check-ignore` shows the dictionary CSV is tracked-eligible while staging products and other data files remain ignored

### Deliverable 5: Source integrity and standalone-versus-master fidelity (gate 3.5)

Before any extraction or database creation, validate the manifest contract itself: exact five-field ordered header, 155 data rows, unique `(root, relative_path)` keys, no `.git/**` row, no `cigale-seds/**` row, root/path sets equal the sealed 103+52 boundary, and no recorded mismatch. Confirm the `cigale-seds` digest sidecar is present and reproduces from the NVMe full listing. Run the committed manifest tests and read-only verifier. Then compute SHA-256 for every local artifact consumed by the dictionary, extractor, supplement loader, spec-z loader, and master/standalone comparison. Compare each against its exact row in that repaired manifest. A malformed header, missing row, duplicate key, extra path inside a declared artifact boundary, stale Git-internal row, out-of-boundary subtree row, or hash/size mismatch halts the unit. Record the exact fetched Yang v1 artifact hash separately because it is an authorized external reference, not a local manifest input.

Then compare each standalone master-extension file with its master HDU: row count, exact column order and types, and a seeded 5,000-row sample spanning every source column. Only primary photometry has a native `id`; compare that full 784,016-value sequence between its standalone and master representations. For the six ID-less extensions, verify absence of a native ID, preserve master/standalone row order, and validate that generated `source_row` is exactly `0..784015` and injected `id` equals primary photometry's ID at the same ordinal.

The master release's cross-HDU row alignment is an upstream catalog contract, not something the project can independently prove from six keyless extensions. Record that limitation explicitly; do not turn the injected-ID anti-join into purported proof of identity.

**Validation:**

- [ ] The manifest has the exact ordered header, 155 unique data rows, zero `.git/**` rows, zero `cigale-seds/**` rows, and root/path/count sets exactly equal the sealed 103+52 boundary
- [ ] The `cigale-seds` digest sidecar reproduces from the NVMe full listing at 1,185,322 files and 468,554,723,694 bytes
- [ ] Every local input consumed by the unit has an observed SHA-256 and byte count equal to its manifest-declared values before it is read for extraction
- [ ] Any missing row, unexpected path, recorded mismatch, or observed mismatch is reported with path and both values and halts the unit
- [ ] For all seven extensions, standalone row count, column order, names, and source types equal the master HDU
- [ ] Primary photometry's native ID sequence is element-wise identical between standalone and master for all rows
- [ ] Full inventories confirm the other six extensions have no native ID
- [ ] A seeded 5,000-row sample reconciles every native column of every extension with zero mismatches; arrays compare element-wise
- [ ] `source_row` and injected `id` construction pass their full-row checks
- [ ] The verification surface records upstream cross-HDU ordinal alignment as an inherited contract, not an independently proven fact

### Deliverable 6: DDL generation (gate 3.6)

Generate `src/etl/schema_v11.sql` from the sealed dictionary plus the fixed provenance-table contract in gate 3.9. It creates all eleven mirror tables in schema `source`: the seven master-extension tables `photometry_primary`, `photometry_aper`, `lephare`, `cigale`, `ml_morpho`, `bulge_disk`, and `galight_morph`; the three supplement tables `lss_overdensity`, `galaxy_groups`, and `galaxy_group_memberships`; and `specz_compilation`. Their column set is every source-native dictionary row plus exactly the thirteen authorized master-table metadata rows. The twelfth table, `source.provenance`, is project infrastructure rather than a mirrored source and therefore is generated from gate 3.9's explicitly versioned field contract, not disguised as dictionary source rows.

PostgreSQL accepts array bounds in a type declaration without enforcing them. Therefore every vector column gets both its array type and a generated nullable-safe `CHECK` constraint enforcing one dimension and the exact dictionary element count. Primary photometry uses its native `id` as primary key and makes `source_row` unique. Each of the six ID-less master tables uses `source_row` as primary key and makes its injected `id` unique and a foreign key to `photometry_primary(id)`. Supplement and spec-z constraints come only from their pinned source contracts; the executor must not invent keys or metadata fields.

Every mirror column carries a `COMMENT ON COLUMN` generated from its separate description, unit, semantic-note, null-encoding, and sentinel provenance fields. An `undocumented_upstream` column says so in the database rather than appearing merely uncommented. Provenance-table columns carry fixed comments from the gate 3.9 contract. The DDL is generated, never hand-edited. If the DDL is wrong, the dictionary, fixed provenance contract, or generator is wrong.

**Validation:**

- [ ] The DDL creates exactly the eleven declared source tables plus `source.provenance`; no analytical table or view exists
- [ ] Across the eleven mirror tables, the DDL column set equals the dictionary table by table with zero additions and zero omissions; `source.provenance` separately equals gate 3.9's fixed field contract
- [ ] Every mirror and provenance column carries a comment; mirror-comment count equals unified-dictionary row count and provenance-comment count equals its fixed contract
- [ ] Every array column has a nullable-safe dimension-and-length `CHECK` generated from its dictionary element count
- [ ] Primary and injected-ID key constraints match the stated master-table contract; supplement/spec-z constraints cite their pinned sources
- [ ] The DDL and generated constraints execute in an isolated scratch database and the scratch database is then dropped
- [ ] Mutation tests removing one dictionary row and inserting a wrong-length array both fail in the scratch environment

### Deliverable 7: Database creation, master mirror load, and credential handoff (gate 3.7)

Using the existing Doppler-injected `PGSQL01_HOST`, `PGSQL01_PORT`, `PGSQL01_ADMIN_USER`, and `PGSQL01_ADMIN_PASSWORD` only for bootstrap and load, capture a read-only baseline fingerprint of `cosmos2025`, then create `cosmos2025_v11`, its `source` schema, and the seven master tables. Load from the manifest-verified standalone files. FITS null masks and NaN become SQL NULL. Every finite numeric value, including documented and candidate sentinels, is loaded unchanged. No other transformation occurs.

Create login role `cosmos2025_v11_ro` with a cryptographically generated password. Revoke public database and schema privileges that would otherwise permit temporary or created objects; grant this role only `CONNECT` on the database, `USAGE` on `source`, and `SELECT` on current and future `source` tables. It must not inherit the cluster-admin role and must not own any object.

Write the generated handoff to gitignored `internal-files/cosmos2025-v11.env` with mode `0600`, using exactly these names:

- `PGSQL01_HOST`
- `PGSQL01_PORT`
- `PGSQL01_COSMOS2025_V11_DB`
- `PGSQL01_COSMOS2025_V11_USER`
- `PGSQL01_COSMOS2025_V11_PASSWORD`

Set the database value to `cosmos2025_v11` and the user value to `cosmos2025_v11_ro`. Do not copy an admin credential into the file. Never print the generated password or file contents to stdout, logs, worklogs, diffs, tests, or commits. The operator will import this handoff into Doppler after approval.

**Validation:**

- [ ] Startup evidence proves both target database and target role were absent; an existing target caused a stop rather than reuse, drop, or overwrite
- [ ] The pre-load `cosmos2025` baseline records table set, table row counts, schema owners, and database owner
- [ ] All seven master tables equal their source row counts; 784,016 is recorded as the prior expectation rather than forced
- [ ] Every `source_row` is unique, non-null, and covers exactly `0..N-1`; all six injected-ID sequences equal primary photometry at the same ordinal
- [ ] Zero injected-ID FK violations and zero duplicate primary or injected IDs
- [ ] Array dimension and length constraints hold across all rows, and a wrong-length insert is rejected
- [ ] Column count per table equals the dictionary count for that table
- [ ] `cosmos2025_v11_ro` can connect and select but cannot insert, update, delete, create schema/table, create temporary objects, alter, truncate, or grant privileges
- [ ] The handoff file contains exactly the five declared variables, has mode `0600`, is ignored by Git, contains no admin credential, and its secret value appears in no captured output or repository file
- [ ] The post-load `cosmos2025` fingerprint equals the baseline

### Deliverable 8: Supplements and spec-z (gate 3.8)

Load `lss_overdensity`, `galaxy_groups`, `galaxy_group_memberships`, and `specz_compilation` into `source` with every native field represented by the unified dictionary. Do not add a per-row release label: record that the three supplements are v1-release products residing with the v1.1 holdings in their `source.provenance` rows, per readiness-review F4.

Compute and report the `photometry_primary.id_specz_khostovan25` to `specz_compilation` match against the live-side prior of 37,219, but do not materialize the join or create a view. The source schema remains a mirror.

Spec-z quality flags are source data, not an ETL filter. Tabulate every observed value and reproduce the compilation's own exact definitions in the dictionary with citations. Report counts for flags 3 and 4 and for flag 9 separately because those are likely downstream calibration-policy inputs. Do not label any subset `secure`, discard a row, or freeze an analysis policy in ETL; T_A v2 decides usage after seeing the sourced definitions.

**Validation:**

- [ ] All native supplement and spec-z fields are loaded exactly once and reconcile to the unified dictionary; no project metadata column was added
- [ ] Supplement row counts equal their verified source counts; 164,155 / 1,678 / 1,745,652 are recorded as prior expectations rather than forced
- [ ] `specz_compilation` row count equals the gate 2.2 source count recorded by P2R-02
- [ ] The computed join count is reported against 37,219; any discrepancy is stated, not reconciled away, and no join table or view exists
- [ ] The complete quality-flag distribution and exact sourced definitions are recorded; {3,4} and {9} counts are reported without applying a filter
- [ ] Every supplement provenance row records its v1 release status on v1.1 holdings
- [ ] `group_id` in memberships anti-joins empty against `galaxy_groups`, if and only if the pinned source contract defines that relationship
- [ ] Read-only-role grants extend to all four newly loaded tables and no broader privilege is introduced

### Deliverable 9: Provenance (gate 3.9)

Create `source.provenance` with one row per loaded table and these minimum fields: `table_name`, `source_file`, `source_path`, `manifest_sha256`, `observed_sha256`, `source_rows`, `loaded_rows`, `load_timestamp`, `manifest_ref`, `manifest_ref_sha256`, `catalog_version`, `supplement_version`, and `notes`. The manifest value and the freshly computed source-file value remain separate evidence and must be exactly equal before load. Neither may be copied into the other. The recorded manifest-reference hash is freshly computed from the exact CSV used by the run.

Expected row count is eleven: seven master extensions, three supplements, and one spec-z table.

**Validation:**

- [ ] Exactly eleven rows, one per loaded table, and the set of `table_name` values equals the set of tables in `source` excluding `provenance` itself
- [ ] Every row records both manifest-declared and freshly observed source SHA-256 values, and every pair is exactly equal
- [ ] Every provenance path and hash agrees with gate 3.5 evidence; no abbreviated or manually transcribed digest appears
- [ ] Every `loaded_rows` equals the live `COUNT(*)` for its table
- [ ] `manifest_ref_sha256` matches a fresh hash of the on-disk manifest CSV used at load time
- [ ] The three supplement rows carry a non-null `supplement_version`; the other rows use an explicit not-applicable representation

### Deliverable 10: Dictionary-driven conformance tests (gate 3.10)

Generate a test suite from the sealed unified dictionary. For every dictionary row, assert that the database column exists in the right table with the right type, origin, array dimension and length where applicable, and a comment matching the dictionary's separate provenance fields. Also assert the exact eleven mirror tables plus the single fixed-contract provenance table, the thirteen authorized metadata rows, all generated key constraints, provenance-row coverage, and the read-only role's positive and negative permission matrix.

The tests are generated rather than enumerated by hand, so dictionary and database cannot drift without a red test. All destructive mutation tests run only against an isolated scratch database or inside a rolled-back transaction owned by the executor; never corrupt the verified `cosmos2025_v11` instance to prove detection.

**Validation:**

- [ ] The suite contains at least one assertion per unified-dictionary row; its exact assertion and row counts are stated, including native master, supplement, spec-z, and thirteen metadata rows
- [ ] The full suite passes against the verified database
- [ ] The table-boundary, origin-count, constraint, provenance, and role-permission assertions all pass
- [ ] In scratch or rollback isolation, altering one comment and one type causes the intended conformance failure; the verified database is unchanged
- [ ] No mutation test writes to `cosmos2025` or leaves a mutation in `cosmos2025_v11`

### Deliverable 11: Full-coverage value reconciliation (gate 3.11)

Independently of the load path, re-read every source artifact fresh and sample rows rather than columns. Use one recorded seed and one shared 20,000-element `source_row` sample across the seven master tables. For each supplement and the spec-z table, use a separate recorded seed and sample 20,000 source records, or the full source when it has fewer than 20,000 rows. Match supplement and spec-z records by their native key. Verify each candidate key's uniqueness against its own source before relying on it, and record the observed distinct-row count alongside the total. The v1 database exhibits these keys, which are prior expectations to confirm rather than facts to assume: `lss_overdensity` on `id`, `galaxy_groups` on `group_id`, and `galaxy_group_memberships` on the composite `(galid, group_id)`, which was distinct across all 1,745,652 v1 rows. Note that memberships names its source identifier `galid` rather than `id`. Only where a key candidate fails its uniqueness check may the comparison fall back to multiplicities of the complete target-cast native row tuple; record which method each table used and why.

Compare database values against independently target-cast source values for every loaded column, including all thirteen relational metadata fields. Equality is exact after the declared source-to-target cast; do not introduce an executor-chosen numeric tolerance. This is the check that fails when a column is mapped to the wrong source field, which structural validation could miss.

**Validation:**

- [ ] Master, each supplement, and spec-z record the seed, eligible population, sample size, and source-matching method
- [ ] Column coverage is complete: the count of columns reconciled equals the count loaded in every table, and both directions of the set equality are asserted
- [ ] Zero value mismatches, or every mismatch is logged with source locator, table, column, database value, and source value
- [ ] Array columns are compared element-wise after the declared target cast, with no tolerance
- [ ] All seven `source_row` fields and all six injected `id` fields reconcile to their exact construction
- [ ] NULLs reconcile only against FITS masks and NaN; a database NULL where the source carries any finite sentinel value is a failure
- [ ] The verifier re-reads the original artifacts and does not consume extractor staging files, logs, or in-memory state
- [ ] The `cosmos2025` baseline fingerprint and `cosmos2025_v11` verified contents are unchanged by reconciliation

### Deliverable 12: Schema and project documentation (gate 3.12)

Generate `docs/reference/schema-v11.md` from the sealed dictionary and verified live database. For each of the eleven mirror tables, include source artifact and locator, row count, complete column listing, origin, target type, element count, unit, source description and locator, semantic note and source, null encoding, documented sentinels, and candidate sentinels. Document `source.provenance` separately as project infrastructure using its fixed field contract. Include the `undocumented_upstream` gap inventory, array index-to-aperture mapping, identifier mapping, source-row/injected-ID contract and its upstream ordinal limitation, provenance model, and the statement that the eleven mirror tables are lossless representations while cleaned or expanded representations belong to a future `analysis` schema.

Refresh the repo's operational orientation only after the mirror passes gates 3.5 through 3.11:

- `AGENTS.md`: central-queue spec authority, release-driven ETL, v1 read-only status, and the corrected rule that only FITS masks and NaN become SQL NULL in the source mirror.
- `README.md`: current seven-extension v1.1 architecture and supplement/spec-z boundary; replace the stale front-page banner with the operator-supplied `assets/icon.svg`, retain the existing assets, and omit diagrams that still depict the v1 pipeline. Do not author, redraw, or restyle the icon; it is supplied and is committed unchanged.
- `docs/project-state.md`: mirror built and verified, with MetaMCP cutover and T_A v2 still pending operator approval.
- `spec/README.md`: repo-local archive/index role and the central queue as dispatch authority.
- `configs/data_paths.yaml`: add a distinct v1.1 target and dictionary/input paths while retaining the named v1 read-only configuration; runtime v1.1 access uses the database-specific `PGSQL01_COSMOS2025_V11_*` names, while admin variables remain bootstrap-only.

**Validation:**

- [ ] An `information_schema` diff against the schema document's complete listings is empty
- [ ] Every unified-dictionary provenance field is represented in the schema documentation
- [ ] Every `undocumented_upstream` column appears in the gap list
- [ ] The aperture index mapping is present and cites its source
- [ ] AGENTS, README, project state, spec orientation, and runtime config agree on the central-queue lifecycle, source-mirror sentinel rule, v1 read-only boundary, and pending operator cutover
- [ ] No stale README diagram is presented as current architecture; existing non-front-page assets were not deleted
- [ ] Documentation passes the frontmatter checker and writing style guide

### Deliverable 13: Verification surface (gate 3.13)

Create `docs/research/etl-v2-verification.md`. Every finding carries an ID, a one-line statement, evidence with exact numbers, and a closed question answerable yes or no. It reports:

- unified-dictionary coverage for all eleven sources, the separate 1,349-master-column reconciliation, and exactly thirteen relational metadata rows;
- distributions for description status, unit provenance, semantic-note provenance, null encoding, documented sentinels, and candidate sentinels;
- the `undocumented_upstream` inventory and candidate list, with the question of which candidates should become future project cleaning rules after scientific review—not which should be relabeled as upstream-documented;
- source-integrity and standalone-versus-master fidelity, including the inherited cross-HDU ordinal contract;
- load counts, generated constraints, both hashes in each provenance row, and full value-reconciliation coverage;
- the computed but nonmaterialized spec-z join result against 37,219 and complete quality-flag distribution;
- the read-only role permission test and credential-handoff checks without any secret value; and
- confirmation that `cosmos2025` is unmodified.

It closes with the questions T_A v2 inherits, each stated as a closed question with a recommendation and explicitly deferred: the `chi2_ratio` repair, SFR censoring redesign, analysis-sample definition, spec-z calibration/validation allocation, and whether the new morphology tables feed contextual features.

**Validation:**

- [ ] Every claim carries a number and a source (query, file, test, or worklog line)
- [ ] Every finding has an ID and a yes/no closed question
- [ ] Suspected findings are posed as questions to confirm from evidence, never as answers to restate
- [ ] Candidate sentinels remain observed candidates; any recommended cleaning action is explicitly future-project logic
- [ ] Credential evidence names the file, mode, variable set, role, and permission-test result but contains no password or other secret
- [ ] The ordinal-alignment limitation and nonmaterialized spec-z join are explicit
- [ ] The T_A v2 questions are listed as deferred, not answered

### Deliverable 14: Closeout (gate 3.14)

Follow the target repository's per-gate commit contract and run the current `spec-closeout` skill for the final documentation, consistency, worklog, registry, attestation, and central-archive evidence chain. Closeout is evidence packaging, not cutover: do not import the handoff into Doppler and do not redirect MetaMCP.

**Validation:**

- [ ] Branch `task/3-etl-v2-mirror`, no push, no remote operation
- [ ] One commit per gate, each referencing its gate number
- [ ] `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md` uses the current template, is checkpointed per gate, distinguishes actual runtime facts from estimates, and is sealed with every gate SHA
- [ ] Registry indexing and model/runtime fields match that worklog and preserve the current schema, category `astronomy`
- [ ] Final closeout attestation uses the resolving central archive position supplied by `spec-closeout`
- [ ] After its worklog and gate evidence are sealed, this central spec is in its lifecycle month archive and absent from the active queue
- [ ] `internal-files/cosmos2025-v11.env` remains ignored, mode `0600`, absent from Git history/diffs/logs, and its contents were never printed
- [ ] Final status leaves MetaMCP cutover, Doppler import, and T_A v2 dispatch pending operator approval

---

## Human Approval Surface

`docs/research/etl-v2-verification.md`, produced at gate 3.13.

Operator approval of that surface authorizes two things: the MetaMCP redirect to `cosmos2025_v11`, and the dispatch of T_A v2.

---

## Constraints

- **The mirror is lossless across the declared boundary.** Every source-native field in all eleven tables is preserved. Exactly thirteen explicitly labeled relational metadata fields are added to make the seven master extensions joinable and verifiable. If a source field seems useless, that is not an exclusion reason and "no current research consumer" is explicitly not an argument.
- **Never compose a description or unit.** Transcribe from a named source or mark it unknown/undocumented in the appropriate field. Project semantic notes remain separate. A fabricated semantic claim is worse than a visible gap.
- **Never null by inference.** FITS masks and NaN become SQL NULL. Every finite value—including documented and candidate numeric sentinels—is stored unchanged. Candidate status can affect only a future analytical cleaning rule.
- **Never flatten a vector.** Arrays preserve one-to-one correspondence with the source. Each array also has a generated dimensionality-and-length constraint because PostgreSQL's declared bounds are not enforcement. Named scalar expansions belong in a future `analysis` schema.
- **No science-derived columns.** The thirteen declared row/ID metadata fields are relational mechanics, not science derivations. `ssfr_cigale` and every computed scientific value belong to the analytical layer, where formulas can be versioned independently of the mirror.
- **Identifier mapping is deterministic and loss-audited.** Preserve the exact source name in the dictionary, generate the SQL name only by gate 3.1's rule, and halt on collision, reserved-word failure, invalid output, or overlength output.
- **Source hashes are observed, not trusted by transcription.** Freshly hash every consumed local artifact before extraction, keep observed and manifest values separate, and halt on missing or unequal pins.
- **The DDL and tests are generated.** Hand-editing generated schema or enumerating column coverage by hand decouples the database from the dictionary and defeats gates 3.10 and 3.11.
- **Secrets never enter evidence.** Cluster-admin variables are bootstrap-only. The generated read-only password appears only in the mode-`0600`, gitignored handoff file and the database role; it is never logged, committed, or copied into runtime config.
- **`cosmos2025` is not a write target.** Upstream replaced the v1 downloads in place, so the v1 database cannot be rebuilt from source. It is the preserved comparison artifact.
- **Prior findings are verified, not restated.** Every number in this spec, including 1,349, 784,016, 37,219, and the supplement counts, is a claim the executor confirms against the artifact. A disagreement is a finding for the verification surface.

---

## What the Executor May Choose

Chosen by the executor: module decomposition and file naming, iteration and batching strategy, manifest-verified parquet staging versus direct COPY, test organization and framework, cryptographically secure password-generation mechanism, non-contract performance indexes after the mirror is loaded, and worklog prose organization.

Frozen by this spec: the eleven-table boundary; the exact thirteen metadata rows; type and identifier mappings; array preservation and enforcement; separate description, unit, semantic, null-encoding, documented-sentinel, and candidate-sentinel fields; source precedence and the prohibition on composed descriptions; source-mirror null/sentinel behavior; schema and table names; source-derived spec-z flag definitions with no ETL filter; the read-only role and exact five-variable handoff contract; exclusion of science-derived columns and analytical views; fresh source-hash verification; and complete column coverage in gates 3.10 and 3.11.

---

## Execution Order

1. Preflight, including P2R-02c closeout/worklog/manifest-test/registry/central-defect/attestation reconciliation, recorded operator dispositions, source access, capacity, credential, and target-absence checks
2. Gate 3.1 (unified dictionary skeleton)
3. Gate 3.2 (semantic reconciliation)
4. Gate 3.3 (value, null-encoding, and sentinel profiling)
5. Gate 3.4 (dictionary seal)
6. Gate 3.5 (source integrity and standalone-versus-master fidelity) — halts on any missing pin or mismatch
7. Gate 3.6 (eleven-table DDL generation)
8. Gate 3.7 (database creation, master mirror load, role, and handoff)
9. Gate 3.8 (supplements and spec-z)
10. Gate 3.9 (dual-hash provenance)
11. Gate 3.10 (dictionary-driven conformance tests)
12. Gate 3.11 (full-coverage value reconciliation)
13. Gate 3.12 (schema and project documentation)
14. Gate 3.13 (verification surface)
15. Gate 3.14 (central-queue closeout)

---

## Notes

**On why fourteen gates is not a problem.** Duration is not the safety property; reversibility is. Effects created by this unit are bounded to one new database, one new role, one ignored handoff file, and ordinary branch/central-lifecycle changes, each with an explicit reversal. The gate cadence makes an interrupted run resumable with a sealed account of completed work.

**On the dictionary as the spine.** Everything downstream of gate 3.4 is generated or verified from one unified artifact. The dictionary covers every native field in eleven sources, separately proves all 1,349 master fields, and adds only thirteen declared relational metadata rows. That makes review tractable without pretending a human eyeball pass over thousands of cells is coverage: validators prove the sets, while the operator reviews provenance rules, exceptions, and unresolved gaps. A dictionary defect propagates visibly instead of being patched independently in schema, code, and docs.

**On what this unit deliberately does not decide.** The analytical layer, cleaned views, future cleaning rules for candidate sentinels, spec-z allocation, and every tension question are successor work. This unit makes the release boundary permanent and documented so later research refinement changes analysis logic rather than forcing another FITS extraction.
