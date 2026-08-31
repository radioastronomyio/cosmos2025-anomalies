<!--
---
title: "Worklog: Spec-z Linkage Correction and Measurement-Level Mirror (P2R-04)"
description: "Mirrors the measurement-level spec-z compilation, corrects the catalog-to-compilation join path, annotates the defective upstream identifier, and characterizes recovery populations and selection bias"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: astronomy
  - domain: data-engineering
related_documents:
  - "spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md"
  - "docs/research/specz-linkage-evidence.md"
  - "docs/research/etl-v2-verification.md"
---
-->

---
title: "Worklog: Spec-z Linkage Correction and Measurement-Level Mirror (P2R-04)"
description: "Mirrors the measurement-level spec-z compilation, corrects the join path, annotates the defective identifier, characterizes recovery populations"
date: "2026-08-31"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: [astronomy, data-engineering]
# --- Runtime Context (required) ---
agent: glm
runtime: Kilo CLI
runtime_version: unreported
model: kilo/zai-coding/glm-5.3
hostname: ml01
spec_ref: spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md
repo: cosmos2025-anomalies
category: astronomy
duration_seconds: null
# --- Token Usage and Cost ---
token_usage_source: "unavailable"
tokens_total:
tokens_input:
tokens_cached:
tokens_output:
tokens_reasoning:
cost_basis:
cost_usd:
priced_date:
# --- Linkage ---
related_documents:
  - "docs/research/specz-linkage-evidence.md"
  - "docs/research/etl-v2-verification.md"
---

# Worklog: Spec-z Linkage Correction and Measurement-Level Mirror (P2R-04)

## Startup preflight (spec-startup)

Skill resolution: lifecycle skills resolved from
`/opt/agents/repos/local-agent-skills/skills/` (`spec-startup`, `spec-closeout`);
`spec-closeout` carries the ML01 identity (astronomy-coding-bot co-author
trailer, `/opt/agents/repos/work-logs/work-registry.csv` registry path).

Environment observed at startup, not authored:

| Item | Observed value |
|------|----------------|
| Shared venv | `/opt/agents/venv/bin/python` (Python 3.12.3), auto-active |
| Packages | astropy 7.2.0, psycopg2 2.9.11, numpy 2.4.3, PyYAML present |
| Doppler scope in use | `ml01/dev`, read from `configs/data_paths.yaml` and confirmed live; this spec names no config (SD-056 in P2R-03 corrected an authored `prd`) |
| Admin variable names | `PGSQL01_HOST`, `PGSQL01_PORT`, `PGSQL01_ADMIN_USER`, `PGSQL01_ADMIN_PASSWORD` (from `configs/data_paths.yaml`) |

Spec startup prerequisites:

| Prerequisite | Result |
|---|---|
| `main` contains P2R-03 merge | Pass: `e65242a` "merge P2R-03: ETL v2 lossless mirror of COSMOS-Web v1.1" |
| `spec/2026-08/` holds three archived specs | Pass: P2R-01, P2R-02, P2R-03 |
| `cosmos2025_v11.source` twelve relations, counts equal `source.provenance` | Pass: 11 mirrors + `provenance`; all eleven live counts equal provenance `loaded_rows` |
| `docs/research/etl-v2-verification.md` present | Pass |
| speczcompilation checkout clean at pinned HEAD | Pass: worktree clean at `1924f5d0ee6c221b820035c8d3cd7302c02532b0` |
| `..._all.fits` manifest row freshly reproduced | Pass: SHA-256 `30675493d98014b23900d41fbcdd6157f5fc64962be22755a6077658d3068fd3`, 129,343,680 bytes |
| `..._unique.fits` manifest row freshly reproduced | Pass: SHA-256 `6ffd1145ed9caeba6c16f8e4267415682562b1a37549ac07a070ba5eb6336e99`, 70,223,040 bytes |

Principal preflight: the connecting identity is `clusteradmin_pg01`, which is
exactly the role named in the single `source`-schema default-privilege entry
(`cosmos2025_v11_ro=r/clusteradmin_pg01`). New tables created by this identity
inherit the analyst SELECT grant; the grant landing after creation is verified
at gate 4.5 rather than assumed.

Branch: `task/4-specz-linkage-correction` off `main`, base commit
`e65242a7802422cc86ed47d96945e2a86e0b27a3`. Worktree clean at branch creation.
Manifest CSV SHA-256 observed this session:
`5941abbbcde4e27d706ec1a49456482cb779f9c77e6cf573b7313a0450ee4c7e`.

---

## Gate checkpoints

### Gate 4.1 — Reproduce the linkage evidence

Committed script: `src/etl/verify_specz_linkage_v11.py` (read-only: one
`default_transaction_read_only=on` transaction; no database writes; no linkage
inferred, repaired, or materialized). Evidence JSON (gitignored staging):
`staging/specz-linkage-g41-evidence.json`. The investigation probe's output was
not consulted; its sentinel rules were read for comparability and re-derived
independently in the script.

Prior-observation reproduction (prior | observed | agree):

| Observation | Prior | Observed | Agree |
|---|---:|---:|---|
| Non-sentinel `id_specz_khostovan25` values, all distinct | 37,219 | 37,219 (distinct == count) | Yes |
| Resolving against galaxy-level by `Id_specz` | 24,364 | 24,364 | Yes |
| Not resolving | 12,855 | 12,855 | Yes |
| Range of stored link values | 223–165,312 | 223–165,312 | Yes |
| Compilation `Id_specz` range, measurement level | 1–487,666 | 1–487,666 | Yes |
| Measurement rows; galaxy rows | 482,579; 261,975 | 482,579; 261,975 | Yes |
| Galaxy set == measurement rows at `Priority = 1` | full equality | full equality (see below) | Yes |
| `ra_COSMOS25`/`dec_COSMOS25` vs mirror at that id | zero, all rows | zero, all rows (max 0.0 both surfaces) | Yes |
| Compilation crossmatch separation | median 0.084", ceiling 0.998" | median 0.0840", max 0.9983" (n=92,359) | Yes |
| Defective-path separation median | 4,054" | 4,467.3" (n=24,364) | **No — finding F-06** |
| Distinct sources, galaxy level | 45,007 | 45,007 | Yes |
| Distinct sources, measurement level | 46,039 | 46,039 | Yes |
| Usable non-sentinel redshift sources, galaxy level | 39,165 | 39,165 (rule: finite `specz > -90`) | Yes |
| Catalog-flagged absent from galaxy surface | 3,062 | 3,062 | Yes |
| Catalog-flagged absent from measurement surface | 2,378 | 2,378 | Yes |
| Multiply-named catalog sources, galaxy level | 185 groups / 371 rows | 185 / 371 | Yes |

Establishments:

1. **Identifier semantics.** `Id_specz` is unique at measurement level
   (482,579 distinct of 482,579) and galaxy level (261,975 of 261,975). Both
   artifacts carry 32 columns with identical names. The galaxy-level table
   equals the measurement-level rows at `Priority = 1` by column-set equality
   and positional per-column value equality including mask equality (NaN-aware
   for floats); no keyed fallback was needed.
2. **Namespace validity.** Separation between stored `ra_COSMOS25`/
   `dec_COSMOS25` and `photometry_primary.ra`/`dec` at `Id_COSMOS25`:
   min/median/p90/p99/max all exactly 0.0 arcsec at both surfaces
   (measurement: n=92,359 of 482,579; galaxy: n=45,193 of 261,975). Excluded
   rows: 390,220 (measurement) and 216,782 (galaxy) for sentinel `Id_COSMOS25`
   (-999); zero rows excluded for invalid coordinates after a valid id.
3. **Defective-path geometry.** Compilation crossmatch (measurement rows with
   valid id and valid corrected coordinates vs the catalog source):
   min 0.00013", median 0.0840", p90 0.2322", p99 0.6381", max 0.9983"
   (n=92,359; excluded 390,220 sentinel-id rows). Defective path (24,364
   resolving stored values joined to galaxy-level `Id_specz`, corrected
   coordinates): min 45.59", median 4,467.3", p90 6,047.6", p99 7,121.9",
   max 8,727.4". One crossmatch, one broken pointer.
4. **Value-range incompatibility.** Stored link values span 223–165,312
   against the compilation's `Id_specz` span 1–487,666: 33.85% of the range;
   zero stored values exceed the compilation maximum.

Mutation test: perturbing one stored `ra_COSMOS25` by +0.5 arcsec in a scratch
copy yields a reported separation of 0.49977" — the zero is measured, not
structural.

Finding F-06 (prior disagreement, does not halt): the defective-path median
prior of 4,054" was not reproducible exactly. Observed 4,467.3" on the stated
basis (resolving values, galaxy-level corrected coordinates). Diagnostic
variants: unique/original coordinates 4,467.3" (identical to corrected on this
subset); all 37,219 values against measurement-level corrected coordinates
4,300.4"; unique-table stored `ra_COSMOS25` basis covers only 3,141 rows
(median 1,351.6") because galaxy-level `-999` coordinate sentinels dominate.
The prior's precise basis is not reconstructible; the qualitative conclusion
(field-scale ~1.2 deg median versus sub-arcsecond crossmatch) holds under
every variant.

No linkage was inferred, repaired, or written. Gate 4.1 commit: see SHA table
at close.

### Gate 4.2 — Dictionary extension

Extended the sealed dictionary from 1,416 to 1,448 rows by adding source
coverage to the existing pipeline (`load_dictionary.py`), not a second one.
Full rebuild re-profiled all 12 source tables (2,031 s, peak RSS 5,594 MiB).

| Check | Result |
|---|---|
| Native rows for `specz_compilation_all` | 32, equal to live TFIELDS 32 |
| Metadata `column_origin` rows in the new table | 0 (no `source_row`, no injected `id`) |
| Semantic fields | 3 verified with locator + SHA-256 (flag, Confidence_level, survey); 29 `undocumented_upstream` with empty description |
| Renamed rows (`specz_compilation` → `specz_compilation_unique`) | 32; field-level diff against the pre-change CSV shows exactly `target_table` changed |
| `id_specz_khostovan25` row | upstream `description_text`, `description_source`, `description_source_sha256` byte-identical; new content in `semantic_note` sourced to the committed gate 4.1 command (SHA-256 `46a7b827...`, frozen at 6d30e24) with the review surface named by path |
| New seal hashes | CSV `a20457c8c5c1785ebce0442a17c1fa06bdef9c1300c199d21776f7c0d22cfcd5`; first-23-field prefix `42a8a9cac318884385914e759aea1d29817a2bd22994fa02b99ecd9b8126487a` |
| Dictionary seal validator | PASSED: 1,448 rows (1,435 native, 13 metadata); README fields 32/32 |
| Mutation test | `test_validator_rejects_duplicate_identifier_within_specz_all` duplicates one `specz_compilation_all` target identifier and requires the validator to fail with `Identifier collision` |

Generated-artifact chain updated in the same pass (regeneration + byte-check
both green): `schema_v11.sql` (12 mirrors, 1,448 mirror columns, 166 array
checks, PRIMARY KEY `id_specz` on the new table from the gate 4.1 uniqueness
proof), `conformance_cases_v11.py` (1,448 cases),
`docs/reference/sentinel-candidates-v11.md` (812 candidate observations across
494 fields).

Boundary updates to existing modules so the extended dictionary flows through
the sealed pipeline: `profile_values.py` (1,435/13/1,448),
`validate_dictionary_seal.py` (tables, origins 1,435, statuses 1,153/78,
seal hashes), `generate_schema_v11.py` (12-table order, 1,448, specz PK),
`generate_conformance_v11.py`/`verify_conformance_v11.py` (1,448 cases,
specz_native 64, 193 constraints, 12 provenance rows),
`generate_schema_docs_v11.py` (1,448 contract, 78 undocumented, sealed rows
hash), `load_provenance_v11.py` (twelve-table boundary incl. `all_fits` path),
`reconcile_values_v11.py` + `reconciliation_core_v11.py` (galaxy-level rename;
historical eleven-table case filter; unchanged Gate 3.11 totals),
`load_supplements_v11.py` (galaxy-level table rename only).

Finding F-07 (pre-existing defect, repaired): the P2R-03 verification-surface
generator sealed five inputs that P2R-04 legitimately regenerated, so
`--check` could no longer reproduce the frozen operator document, and two of
its tests asserted the retired active-queue spec path (broken since the
closeout archive move). Repaired without touching the sealed document or the
module's offline property: the four regenerated inputs now fall back to
P2R-03-committed bytes (`e65242a`) through an injectable, seal-checked
historical-bytes provider (module source contains no subprocess; the provider
is installed by the test fixture from the local git object store), and the two
stale tests now assert the durable post-closeout archive state. The
`etl-v2-verification.md` document is byte-unchanged.

New modules this gate (for gates 4.4-4.6): `rename_specz_unique_v11.py`,
`load_specz_all_v11.py`, `reconcile_specz_all_v11.py` (recorded sampling seed
12,006,315,477,097,142,501, derivation
`sha256_uint64_seed_plus_zero_based_ordinal_lowest_rank_v1`).

Test suite: all groups green (dictionary seal, semantics, load, supplements,
provenance, schema, scratch, conformance, docs, verification surface,
reconciliation, bootstrap); the slow live dictionary byte-identity check
re-runs the full rebuild and is recorded at close. Gate 4.2 commit: see SHA
table at close.

### Gate 4.3 — DDL generation and scratch verification

`schema_v11.sql` was regenerated from the extended dictionary in the gate 4.2
pass (12 mirrors + provenance = 13 relations, no view). The live disposable
scratch verification ran under Doppler `ml01/dev` on PostgreSQL 16.15:

| Observation | Value |
|---|---|
| Relations created in scratch `source` | 13 tables, 0 views |
| Mirror columns / provenance columns | 1,448 / 13 |
| Comments | 1,461 (1,448 dictionary + 13 provenance contract) |
| Array-shape checks / constraints | 166 / 193 (includes `specz_compilation_all_id_specz` PRIMARY KEY) |
| Column-set assertion | dictionary-to-DDL equality asserted in both directions by tuple comparison |
| New-table primary key | `Id_specz`, present because gate 4.1 measured 482,579 distinct of 482,579; no other key invented |
| Mutation: wrong array cardinality | rejected (`photometry_primary_flux_aper_hst_f814w_array_shape_...`) |
| Mutation: NULL arrays | 7 dependency rows accepted |
| Mutation: one dictionary row removed | fails with `expected 1448, observed 1447` |
| Cleanup | scratch database dropped; 0 remaining; sealed databases and analyst role unchanged |

Boundary repair recorded: `_assert_protected_precondition` in
`verify_schema_v11_scratch.py` still asserted Gate 3.6 pre-creation absence of
`cosmos2025_v11` and the analyst role, which is false for every post-seal run.
It now asserts presence-plus-identity (both sealed databases and the role
present and unchanged across the run), and the summary keys report
`sealed_databases_unchanged`/`analyst_role_unchanged`. Gate 4.3 commit: see
SHA table at close.

### Gate 4.4 — Rename and re-verify the galaxy-level table

`doppler run --project ml01 --config dev -- python
src/etl/rename_specz_unique_v11.py --rename` executed one transaction
(ALTER TABLE RENAME plus exactly one provenance `table_name` UPDATE) and
re-verified in the same run; `--verify-only` re-verifies the post state
repeatably (comments compared against the dictionary-generated contract).

| Check | Result |
|---|---|
| `source.specz_compilation` exists | No |
| `source.specz_compilation_unique` row count | 261,975, equal to provenance before and after |
| Seeded row-level digest (seed modulus 977, offset 3; 269 sampled rows) | identical before/after (`a40bb411c768ae047e6005ecd534287e`) |
| Column comments | 32 survive; full comparison against pre-rename values and, on re-verify, against the dictionary contract — zero differences |
| Constraints | preserved (the table carries none by contract) |
| Provenance row | `table_name` updated; every other field unchanged (field-exact diff) |
| Analyst SELECT | effective through session authorization: 261,975 rows |
| Other relations | no name, owner, or row-count change; all ten others agree with provenance |
| Live inventory | 12 relations, zero views, owner `clusteradmin_pg01` throughout |

Gate 4.4 commit: see SHA table at close.

### Gate 4.5 — Load the measurement-level mirror and declare the seal

`doppler run --project ml01 --config dev -- python src/etl/load_specz_all_v11.py
--load` under principal `clusteradmin_pg01` (verified equal to the
default-privilege owner before any DDL).

| Check | Result |
|---|---|
| Source pin | manifest SHA-256 `30675493d98014b23900d41fbcdd6157f5fc64962be22755a6077658d3068fd3` == freshly observed; bytes 129,343,680 == observed |
| DDL | tracked `schema_v11.sql` byte-checked against fresh generation first; 33 extracted statements (1 CREATE + 32 COMMENT) executed inside the load transaction |
| Loaded rows | 482,579 == source rows (prior 482,579 recorded as expectation, not forced) |
| `Id_specz` | 482,579 non-null and distinct (gate 4.1 property) |
| Columns / comments | 32 / 32, equal to dictionary count; comments compared against the dictionary-generated contract |
| Analyst grant | `has_table_privilege` true AND effective session-authorized SELECT of 482,579 rows — verified, not assumed from default privileges |
| Protected tables | seven masters + three supplements + renamed galaxy-level table unchanged by row count and seeded digest (seed modulus 977, offset 3) |

Independent value reconciliation (`reconcile_specz_all_v11.py`, load path not
reused): source re-read fresh once; 20,000-row seeded row sample (seed
12,006,315,477,097,142,501, derivation
`sha256_uint64_seed_plus_zero_based_ordinal_lowest_rank_v1`, sample digest
`737021a2d756d60e5146acbb35d8e0e4b54c104c4016f20f0da3c9fc67457326`); every one
of the 32 columns fetched and compared in both directions from one
repeatable-read read-only snapshot; 640,000 row-column comparisons; **zero
mismatches**; no ledger created. NULLs reconcile only against FITS masks and
NaN by the canonical-cell machinery, so a database NULL against a finite
sentinel would have been a mismatch.

**LOAD SEAL (declared per spec Reversal section):** `source.specz_compilation_all`
has passed row-count, key-uniqueness, null-encoding, and full-coverage value
reconciliation checks, and `specz_compilation_unique` passed post-rename
re-verification at gate 4.4. From this point the loaded data is validated
work: reversal of administrative, documentation, conformance-generation, or
verifier-code failure is repair in place; dropping or reloading the sealed
table requires explicit operator authorization. Destructive-retry budget
remains 2 of 2 (none used). Gate 4.5 commit: see SHA table at close.

### Gate 4.6 — Provenance

`--register-provenance` under Doppler `ml01/dev`:

| Check | Result |
|---|---|
| Provenance rows | 12; `table_name` set equals the live `source` relations minus `provenance` |
| New row dual hashes | manifest `30675493d98014b2...` and observed `30675493d98014b2...` both present and equal, computed independently (declared from the manifest CSV row; observed from a fresh file read inside `pin_manifest_input`) |
| `loaded_rows` | 482,579 == live count |
| `manifest_ref_sha256` | `5941abbbcde4e27d706ec1a49456482cb779f9c77e6cf573b7313a0450ee4c7e`, equal to the session's fresh hash of the on-disk manifest CSV |
| `load_timestamp` | database `transaction_timestamp()` of the registration transaction |
| Load transaction xmin | 11273678, single distinct xmin across all 482,579 rows |
| Pre-existing rows | field-exact unchanged (the only prior change is the gate 4.4 `table_name`) |

Authorized administrative action recorded: the live
`photometry_primary.id_specz_khostovan25` column comment still carried the
P2R-03 text after the gate 4.2 semantic note extended the dictionary contract.
`--sync-link-comment` proved the live mirrors differed from the dictionary
contract in exactly that one comment, applied the tracked-DDL statement, and
re-verified zero differences across all 1,448 mirror comments. This is the
single `photometry_primary` change the spec authorizes.

Live conformance surface over the completed mirror (gate 4.6 post-state):
1,448 case assertions, 13 objects, 1,461 columns, 193 constraints, 12
provenance rows; all analyst matrices green (SELECT allowed; 78 denials at
SQLSTATE 42501 across masters, supplements, and provenance); v1 fingerprint
unchanged (`82fb7e09...`); handoff security intact; direct analyst network
authentication remains a pending operator action and is not claimed.
Gate 4.6 commit: see SHA table at close.

### Gate 4.7 — Characterize the linkage, decide nothing

Committed read-only script `src/etl/characterize_specz_linkage_v11.py`; full
per-source enumeration in
`staging/specz-linkage-g47-characterization.json`. The script re-reads the
sealed mirror fresh (two read-only connections) and consumes no staging
state. Post-state verified after the run: zero `source` views or materialized
views, no `analysis` schema, twelve provenance rows, zero rows written.

Corrected path (both surfaces via `Id_COSMOS25`): 45,007 galaxy-level and
46,039 measurement-level distinct catalog sources; galaxy-level is a subset of
measurement-level. Galaxy multiplicity: 44,822×1, 184×2, 1×3. Measurement
multiplicity: 25,430 singletons; 21 distinct multiplicities up to 25 entries
on one source (DESI repeats). Usable-redshift rule stated explicitly as
finite `specz > -90` with no confidence threshold: 39,165 galaxy-level
sources; by the compilation's own confidence value: -99→1, 0→732, 50→9,021,
80→7,430, 85→1,358, 95→4,201, 97→16,498.

Recovery population A (measurement-only catalog sources): 1,032 sources over
1,559 entries, every entry `Priority = 0` (verified, not assumed). Entries per
source: 716×1, 213×2, 58×3, ..., 2×12. Entry-to-catalog separation: median
0.130", p90 0.380", max 0.982" — these are real sub-arcsecond crossmatches.
Confidence distribution across entries: 0→415, 50→387, 80→303, 85→80, 95→157,
97→217. Representative destination (nearest `Priority = 1` entry by
corrected-coordinate separation within 5", a compilation self-crossmatch):
found for 694; **every one of the 694 names a different catalog source** (0
name the same source), at entry-to-representative separation median 0.873"
(max 4.98") and catalog-source-to-destination separation median 1.167", p90
4.143", max 5.756". 338 sources have no `Priority = 1` entry within 5" of any
of their entries. **The neighbour-promotion hypothesis is supported by the
measurement for the 694**: the deduplication's chosen representative for the
same spectroscopic source was attached to a neighbouring catalog source
1-6 arcsec away, so the demoted entry's source lost its galaxy-level row. It
is not supported as a complete account: the 338 without a nearby
representative need a separate explanation the evidence does not determine.

Recovery population B (multiply-named galaxy sources): 185 sources over 371
entries (184 pairs, 1 triple). Per-source tables carry each entry's redshift,
flag, confidence, survey, and separation (median 0.202", max 0.977"). Redshift
rule: sentinels excluded by finite `specz > -90`, 58 entries excluded, no
arbitrary duplicate selection — per-group reporting. 132 groups carry two or
more usable redshifts; 75 agree within |Δz| ≤ 0.005; median max-|Δz| 0.0028,
p90 0.832, max 4.105 — a real disagreement tail the policy unit must own.

Selection function of `id_specz_khostovan25` (resolving = distinct
non-sentinel value present in galaxy-level `Id_specz`): 24,364 of 37,219
flagged sources resolve; 12,855 do not. Treated as a boolean flag against the
corrected path — against the galaxy-level surface: TP 34,157, FP 3,062, FN
10,850, precision 0.9177, recall 0.7589 (positive denominator 45,007 =
galaxy-level-reachable sources); against the measurement-level surface: TP
34,841, FP 2,378, FN 11,198, precision 0.9361, recall 0.7568 (positive
denominator 46,039). Full corrected-path-attached galaxy-entry flag and
confidence distributions reported for both buckets (not means): resolving
sources' entries carry confidence 97→8,693, 95→2,711, 80→3,167, 50→2,719,
0→3,778; non-resolving sources' entries carry 97→5,915, 95→1,033, 80→1,845,
50→1,484, 0→1,743. Flagged sources with no corrected-path galaxy entry at
all: 2,760 resolving, 302 non-resolving. Every figure above names the surface
it was computed against. Gate 4.7 commit: see SHA table at close.
