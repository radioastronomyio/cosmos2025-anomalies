---
title: "Worklog: COSMOS-Web ETL v2 Lossless Mirror (P2R-03)"
description: "Per-gate checkpoint log for the COSMOS-Web v1.1 lossless mirror rebuild"
date: "2026-08-17"
version: "0.1"
status: "partial"
tags:
  - type: worklog
  - domain: work-logs
  - domain: cosmos-web
  - domain: etl
# --- Runtime Context (required) ---
agent: "codex"
runtime: "Codex API"
runtime_version: "unreported"
model: "unreported"
hostname: "ml01"
spec_ref: ../spec/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md
repo: "cosmos2025-anomalies"
category: "astronomy"
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
  - "data/dictionary/columns-v11.csv"
  - "src/etl/load_dictionary.py"
  - "tests/test_load_dictionary.py"
  - "tests/test_load_dictionary_semantics.py"
---

# Worklog: COSMOS-Web ETL v2 Lossless Mirror (P2R-03)

## Summary

| Attribute | Value |
|-----------|-------|
| Status | Partial: Gates 3.1 and 3.2 complete; later gates remain |
| Agent | codex / Codex API / unreported |
| Hostname | ml01 |
| Spec | spec-p2r-03-etl-v2-mirror.md |
| Duration | unknown (not exposed to the executor) |

Objective: Build the unified load-dictionary skeleton and reconcile its source
descriptions, units, provenance status, and project semantic notes for the
COSMOS-Web v1.1 lossless mirror.

Outcome: Gates 3.1 and 3.2 generated and validated 1,416 dictionary rows: 1,403
native fields, seven zero-based `source_row` rows, and six `id` rows injected
from primary photometry by matching row ordinal. All rows now carry separate
description, unit, and semantic-note evidence fields. No source data,
PostgreSQL object, or remote Git state was modified.

Starting branch and base: startup began on `main` at
`d2e51479f5ec108688d2da44333988dd0c9c7709`; execution uses
`task/3-etl-v2-mirror` at the same base.

Startup checks: repository path and branch matched the gate brief; HEAD matched
the required base commit; the worktree was clean; all configured source paths
used by Gate 3.1 existed. PostgreSQL was not contacted.

---

## 1. Work Completed

| Task | Description | Result |
|------|-------------|--------|
| Gate 3.1 dictionary builder | Added a config-driven, read-only builder for seven master extensions, Hatamnia `OVERDENSITY`, both Toni text tables, and the unique spec-z FITS table | Complete |
| Type and identifier contract | Preserved exact source names; mapped FITS types and vectors; applied lowercase/punctuation/reserved-word rules; halted on collisions, invalid names, empty target types, and identifiers over 63 bytes | Complete |
| Relational metadata | Added one zero-based `source_row` to every master target and injected primary-photometry `id` into the other six targets | Complete: 7 + 6 rows |
| Artifact and regeneration | Generated `data/dictionary/columns-v11.csv`; added narrow Git ignore exception and `--check` byte-reproduction mode | Complete: 1,416 rows, 284 KiB |
| TDD and validation | Captured RED then GREEN for identifier rules, FITS mapping, three named validator mutations, live inventory build, config-driven CLI output, and tracked regeneration | Complete |

### Gate 3.1 source reconciliation

| Target table | Native fields |
|--------------|--------------:|
| `photometry_primary` | 287 |
| `lephare` | 43 |
| `photometry_aper` | 148 |
| `cigale` | 56 |
| `ml_morpho` | 150 |
| `bulge_disk` | 461 |
| `galight_morph` | 204 |
| `lss_overdensity` | 4 |
| `galaxy_groups` | 14 |
| `galaxy_group_memberships` | 4 |
| `specz_compilation` | 32 |
| **Total** | **1,403** |

The seven live master `TFIELDS` values sum to 1,349, equal to the prior 1,349
expectation (difference 0). Only `photometry_primary` has a native exact `id`.
The Toni group and membership headers retain exact source name `ID`, which
deterministically maps to target identifier `id` rather than `group_id`.

Every vector row records its live element count. The inventory contains 18
`5D` fields mapped to `double precision[]` with element count 5 and 148 `5E`
fields mapped to `real[]` with element count 5. No vector was flattened.

### TDD evidence

| Cycle | RED evidence | GREEN evidence |
|-------|--------------|----------------|
| Identifier normalization | Focused test failed because `src.etl.load_dictionary` did not exist | Focused test passed after deterministic normalization and reserved-word prefixing |
| FITS type mapping | Focused test failed because no type-mapping behavior existed | Scalar, string-width, `5D`, and `5E` literal mappings passed |
| Wrong `D` mutation | Validator test failed because no validator existed | Mutated `D -> real` raised `Type mapping mismatch` |
| Collision mutation | Test failed because the validator accepted two sources targeting `flux_a` | Mutation raised `Identifier collision` |
| Overlength mutation | Test failed because a 64-byte identifier was accepted | Mutation raised `Identifier over 63 bytes` |
| Live inventory | Test failed because no live builder existed | All eleven native counts, 1,349 `TFIELDS`, and 13 metadata rows reconciled |
| Configured CSV CLI | Test failed because the script produced no output file | Temporary configured output contained 1,416 rows and Toni `ID -> id` |
| Tracked reproduction | `--check` failed with missing dictionary config | Configured artifact regenerated byte-identically |

Focused verification: `pytest tests/test_load_dictionary.py -v` returned
`10 passed in 12.17s`. Style verification returned `All checks passed!` and
`2 files already formatted` for the new Python files. Fresh full verification,
`pytest -v`, returned `30 passed in 122.49s (0:02:02)`, including the production
manifest verifier and all Gate 3.1 tests.

### Fix round 2: exact declared mirror-table names

A controller cross-gate review found four target tables named after source
configuration keys rather than Deliverable 6's declared mirror tables. The
structural mappings are now exact:

| Configured source | Corrected target table |
|-------------------|------------------------|
| `photom_secondary` | `photometry_aper` |
| `ml_morph` | `ml_morpho` |
| `bulgedisk` | `bulge_disk` |
| unique spec-z FITS | `specz_compilation` |

Strict TDD evidence: the new literal eleven-table-set test failed before the
implementation with the four obsolete extras (`photometry_secondary`,
`ml_morph`, `bulgedisk`, `specz_unique`) and the four required names missing.
After only the four production mappings changed, the same test passed.

Fresh verification after regeneration:

- focused: `11 passed in 16.34s`;
- full repository: `31 passed in 125.58s (0:02:05)`;
- reproduction: `dictionary check PASSED: 1416 rows reproduce byte-identical`;
- CSV scope: 797 rows changed only in `target_table`; all other fields remained
  identical by row;
- Toni native source columns remained exact: both `ID` fields still map to
  target identifier `id`.

### Gate 3.2 semantic reconciliation

Gate 3.2 adds thirteen semantic fields to the fixed CSV schema. Every row now
has a description status, explicit unit value or `unknown`, and separate
description, unit, and semantic-note provenance fields. Whitespace in source
descriptions is limited to trimming ends and collapsing internal runs to one
ASCII space. The resulting CSV has 23 columns, 1,416 data rows, no ragged rows,
and no embedded newlines.

Description status reconciliation:

| Status | Rows | Evidence basis |
|--------|-----:|----------------|
| `verified` | 1,150 | 1,143 detailed master definitions, four Hatamnia definitions, and three exact spec-z repository definitions |
| `pattern_expanded` | 204 | Yang et al. 2026, exact `arXiv:2606.14869v1` Table 1 |
| `undocumented_upstream` | 49 | Two CIGALE, eighteen Toni, and twenty-nine spec-z native fields without exact definitions |
| `project_derived` | 13 | Seven `source_row` and six injected `id` rows authorized by the central spec |

The two CIGALE gaps are exactly `ebv_stars` and `ebv_stars_err`; both retain an
empty description and unit `unknown`. Toni headers establish names and table
shape but contain no field definitions, so all eighteen Toni fields remain
undocumented. The pinned spec-z repository provides exact native semantics for
`flag`, `Confidence_level`, and `survey`; the other twenty-nine fields remain
undocumented rather than receiving prose inferred from their names.

The GALIGHT evidence cache is outside the repository at its configured path.
The fetched PDF is 5,310,696 bytes and has SHA-256
`f4d369c1f3c093dc5990895ac7f95ceecead318339e9fe1b8b823fb51675f0bc`.
Each of the four filters has 51 live fields:

| Table 1 category | Per filter | Total |
|------------------|-----------:|------:|
| Single-Sersic | 10 | 40 |
| Bulge-disk parameters | 10 | 40 |
| Bulge-disk errors | 8 | 32 |
| Point-source | 11 | 44 |
| Fit statistics | 6 | 24 |
| Statmorph | 6 | 24 |

No bulge or disk `nsersic` error pattern exists. The validator rejects a
deliberate 208-row mutation that adds one absent symmetric error pattern per
filter. Every accepted GALIGHT row records the exact Table 1 pattern, filter,
page, arXiv v1 reference, category, and observed PDF digest.

Observed semantic source hashes:

| Source | SHA-256 |
|--------|---------|
| Detailed master descriptions | `3e7dde1db9d541ce8593b12cbf0690130422e746ce7db78cc238f27ed724366b` |
| Yang v1 PDF | `f4d369c1f3c093dc5990895ac7f95ceecead318339e9fe1b8b823fb51675f0bc` |
| Hatamnia README | `e40402a510cad8e3d7069de759514090a16602ea7eb5f46715d13d64d1487e97` |
| speczcompilation root README | `1aee693918c3e8deb8ac9ce273468a37935987f53f2903eb47420dcfbfe90a23` |
| speczcompilation schema README | `43992cf6a30d5893d9421dd1d0b837e1f8dc4975a92e8372ba8cb3b7be78d0c1` |
| Unit conventions | `8a4d3a724ba435fe5668260e50be45c41f067214567a8723d27d004d3df9ca4a` |
| Central ETL v2 spec | `6f627d9941843f2d8643eca5227aced1d8bc9216310079dc0fed25352cd09b16` |

Units are populated only where a cited block states one. The dictionary has 15
sourced semantic notes: nine LePhare mass/SFR/sSFR and quantile fields record
the log10 convention; six native CIGALE mass/SFR value and error fields record
the linear convention. These facts occur only in `semantic_note`. The retired
derived `ssfr_cigale` field remains absent.

Strict TDD evidence:

| Cycle | RED evidence | GREEN evidence |
|-------|--------------|----------------|
| Canonicalization | Focused test failed because no canonicalizer existed | CRLF, newline, tab, repeated-space, and end trimming produced one literal expected string |
| Status and provenance | Live rows lacked the thirteen required semantic fields | Exact 1,150/204/49/13 counts and complete sourced evidence passed |
| Negative mutations | No semantic validator existed | Composed undocumented prose, native project status, and missing hashes raised named diagnostics |
| GALIGHT asymmetry | Category evidence was absent | Exact 204-row expansion passed and the 208-row mutation raised `GALIGHT pattern set mismatch` |
| Units and notes | Rows had no independent unit fields | Explicit units and exact 15-row parameter-space coverage passed |
| CSV schema | Serialization retained the 10-column Gate 3.1 header | Fixed 23-column rectangular output with no embedded newlines passed |

The Gate 3.2 focused suite returned `8 passed in 4.27s`. The combined Gate 3.1
and 3.2 suites returned `19 passed in 20.42s`; regeneration returned
`dictionary check PASSED: 1416 rows reproduce byte-identical`. Fresh full
repository verification after implementation returned `39 passed in 129.19s
(0:02:09)`.

---

## 2. Files Changed

| File | Change |
|------|--------|
| [.gitignore](../.gitignore) | Added the narrow tracked-CSV exception |
| [configs/data_paths.yaml](../configs/data_paths.yaml) | Added the dictionary output path and Gate 3.2 semantic evidence paths |
| [configs/README.md](../configs/README.md) | Documented the dictionary and semantic source roles |
| [data/README.md](../data/README.md) | Added the required interior data-product index |
| [data/dictionary/README.md](../data/dictionary/README.md) | Documented the Gate 3.1 structure, Gate 3.2 semantics, and regeneration contract without claiming the Gate 3.4 seal |
| [data/dictionary/columns-v11.csv](../data/dictionary/columns-v11.csv) | Added the generated structural dictionary and Gate 3.2 semantic fields |
| [src/etl/load_dictionary.py](../src/etl/load_dictionary.py) | Added structural inspection, semantic reconciliation, validation, CSV, and check-mode implementation |
| [src/etl/README.md](../src/etl/README.md) | Listed the ETL v2 dictionary builder |
| [tests/test_load_dictionary.py](../tests/test_load_dictionary.py) | Added discriminating unit, mutation, live integration, and artifact tests |
| [tests/test_load_dictionary_semantics.py](../tests/test_load_dictionary_semantics.py) | Added Gate 3.2 canonicalization, provenance, asymmetry, mutation, unit, semantic-note, and serialization tests |
| [tests/README.md](../tests/README.md) | Documented the new focused suite |
| [work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md](2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md) | Created this per-gate checkpoint log |

---

## 3. Issues Encountered

| Issue | Resolution |
|-------|------------|
| Startup instructions and repository docs name Doppler `ml01/prd`, but the operator corrected the active config to `ml01/dev` | Recorded for eventual defect registration. Gate 3.1 made no PostgreSQL connection, so no credential config was consumed or changed |
| Ruff reported test import `E402` after the repository root was inserted into `sys.path` | Matched the existing test-suite pattern with a narrow `# noqa: E402`; rerun passed |
| Toni headers and twenty-nine spec-z native field names lack exact field definitions in their pinned documentation | Preserved them as `undocumented_upstream` with empty descriptions; no prose or units were inferred from names |

---

## 4. Next Steps

Handoff: Gate 3.3 can consume the structurally and semantically reconciled
dictionary. Gate 3.4 remains responsible for the formally sealed dictionary
documentation; the current interior README states that boundary explicitly.

1. Register the `ml01/dev` versus stale `ml01/prd` documentation defect at the
   spec-authorized defect-registration gate.
2. Preserve the frozen structural and semantic mappings while adding only the
   Gate 3.3 profiling fields authorized by the spec.

<!-- Agent: codex, Runtime: Codex API, Model: unreported, Session: interactive -->
