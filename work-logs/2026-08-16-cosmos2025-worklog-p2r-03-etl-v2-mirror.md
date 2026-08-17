---
title: "Worklog: COSMOS-Web ETL v2 Lossless Mirror (P2R-03)"
description: "Per-gate checkpoint log for the COSMOS-Web v1.1 lossless mirror rebuild"
date: "2026-08-17"
version: "0.4"
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
  - "src/etl/profile_values.py"
  - "tests/test_profile_values.py"
  - "docs/reference/sentinel-candidates-v11.md"
  - "src/etl/validate_dictionary_seal.py"
  - "tests/test_dictionary_seal.py"
  - "src/etl/verify_source_fidelity.py"
  - "tests/test_verify_source_fidelity.py"
---

# Worklog: COSMOS-Web ETL v2 Lossless Mirror (P2R-03)

## Summary

| Attribute | Value |
|-----------|-------|
| Status | Partial: Gates 3.1 through 3.5 complete; later gates remain |
| Agent | codex / Codex API / unreported |
| Hostname | ml01 |
| Spec | spec-p2r-03-etl-v2-mirror.md |
| Duration | unknown (not exposed to the executor) |

Objective: Build and seal the unified load dictionary, profile every native
value/null/sentinel state, and prove source integrity plus standalone/master
fidelity for the COSMOS-Web v1.1 lossless mirror.

Outcome: Gates 3.1 through 3.4 generated, validated, and sealed 1,416 dictionary
rows: 1,403 native fields, seven zero-based `source_row` rows, and six `id` rows
injected from primary photometry by matching row ordinal. Native rows carry
separate semantic, type-appropriate profile, null-state, documented-sentinel,
and candidate-sentinel fields. Gate 3.5 then verified the complete immutable
input boundary and exact seven-extension fidelity before extraction. No source
data, PostgreSQL object, sealed artifact, or remote Git state was modified.

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

### Gate 3.3 value, null-encoding, and sentinel profiling

Gate 3.3 profiled every one of the 1,403 native dictionary rows from the eleven
configured live sources. The thirteen project metadata rows use explicit
not-applicable cells: empty `profile_json`, false mask/NaN booleans, empty
documented evidence, and `[]` sentinel arrays. All 1,416 Gate 3.1/3.2 row
prefixes remained byte-value identical through the first 23 CSV fields.

Profile coverage:

| Profile class | Count |
|---------------|------:|
| Native rows | 1,403 |
| Scalar fields | 1,237 |
| Numeric vector fields | 166 |
| Numeric vector-index profiles | 830 |
| Metadata rows, not applicable | 13 |
| Total dictionary rows | 1,416 |

Live source row populations:

| Target table | Source rows |
|--------------|------------:|
| `photometry_primary` | 784,016 |
| `lephare` | 784,016 |
| `photometry_aper` | 784,016 |
| `cigale` | 784,016 |
| `ml_morpho` | 784,016 |
| `bulge_disk` | 784,016 |
| `galight_morph` | 784,016 |
| `lss_overdensity` | 164,155 |
| `galaxy_groups` | 1,678 |
| `galaxy_group_memberships` | 1,745,652 |
| `specz_compilation` | 261,975 |

Independent state distributions:

| State | False/empty fields | True/non-empty fields | Observations |
|-------|-------------------:|----------------------:|-------------:|
| Declared FITS masks | 1,400 | 3 | Per scalar/index counts are in `profile_json` |
| NaNs | 1,098 | 305 | Per scalar/index counts are in `profile_json` |
| Documented sentinels | 1,402 | 1 | One field, value `-999` |
| Conservative candidates | 927 | 476 | 793 scalar/index entries |

The sole documented sentinel is `photometry_primary.id_specz_khostovan25 =
-999`. Its exact canonicalized evidence states `-999 if no specz match`; the
dictionary retains the source, line locator, and exact artifact SHA-256.

Candidate rule version `cosmos_v11_candidate_sentinel_v1` requires an
undocumented finite numeric value whose absolute value is exactly `10^k - 1`
for integer `k >= 2`, with `count >= 1000` and `count * 1000 >=
non_null_count` in that scalar/index, excluding documented valid flag/category
values. Observed candidate-value distribution:

| Value | Candidate entries |
|------:|------------------:|
| `-999` | 451 |
| `999` | 318 |
| `-99` | 23 |
| `99` | 1 |
| **Total** | **793** |

Candidate table distribution:

| Target table | Candidate entries |
|--------------|------------------:|
| `photometry_aper` | 370 |
| `bulge_disk` | 265 |
| `photometry_primary` | 86 |
| `galight_morph` | 44 |
| `specz_compilation` | 19 |
| `lephare` | 9 |

`docs/reference/sentinel-candidates-v11.md` is generated from dictionary cells.
It contains separate FITS-mask, NaN, documented-sentinel, and candidate
sections, plus one row for each of the 793 candidate observations. Every row
includes exact count, non-null denominator/fraction, scalar or vector index,
rule trigger/version, and sourced semantics or literal `unknown`.

Strict TDD evidence:

| Cycle | RED evidence | GREEN evidence |
|-------|--------------|----------------|
| Numeric scalar/vector profiles | Tests failed because the profiler module did not exist | Masks, NaNs, finite summaries, deterministic top-three ties, and per-index vectors passed |
| Candidate rule and JSON | Four tests failed on missing APIs | Exact pattern/threshold/denominator, exclusions, stable JSON, and evidence validation passed |
| Typed rows and null encodings | Four tests failed on missing typed/profile-field APIs | Text/boolean types, finite sentinel retention, declared TNULL-only masking, and metadata N/A passed |
| Profile validator/artifact | Validator APIs and nine profile CSV fields were absent | Vector/index/population/candidate validation and full tracked coverage passed |
| Direct CLI regression | `--help` failed with `ModuleNotFoundError: src` | Package-aware local/module imports passed direct execution |
| Generated report | Report renderer was absent | Every dictionary candidate and all four state classes reconciled in generated Markdown |
| Exact large integer | A literal `10^k - 1` integer above float precision was rejected after float coercion | Integer candidates retain exact arithmetic and ordering without float conversion |
| State-summary mutation | The validator accepted `has_nan` drift from per-index counts | Mask and NaN summary booleans reconcile to their independent profile counts |
| Generated report claims | Source-table scope was a literal and candidate rows omitted the explicit trigger | Scope counts derive from validated rows and all 793 candidates carry trigger and version |

The first successful live profile completed with internal profiling duration
1,918.074 seconds. `/usr/bin/time -v` measured 32:02.13 elapsed, 1,835.27 user
seconds, 88.54 system seconds, 100% CPU, and maximum resident set size
5,734,188 KiB (5,599.793 MiB). FITS inputs were memory-mapped and processed one
scalar/vector index at a time. The 1,745,652-row memberships table was streamed
in 50,000-row chunks through temporary disk-backed exact-frequency tables; the
table was never materialized as a full in-memory copy.

An independent live `python src/etl/load_dictionary.py --check` returned both
`dictionary check PASSED: 1416 profiled rows reproduce byte-identical` and
`candidate report check PASSED: content reproduces byte-identical`. Its
internal profile took 1,892.321 seconds; `/usr/bin/time -v` measured 31:36.33
elapsed, 1,811.86 user seconds, 86.12 system seconds, and 5,733,600 KiB
(5,599.219 MiB) maximum RSS.

Final focused Gate 3.3 verification returned `15 passed in 0.55s`. Prior-gate
dictionary verification excluding the deliberately expensive default live
check returned `19 passed, 1 deselected in 16.56s`. The fresh full repository
suite returned `55 passed in 2156.06s (0:35:56)` and included both the
production manifest verifier and current-code live dictionary/report
reproduction. `/usr/bin/time -v pytest -v` measured 35:56.29 elapsed and
5,731,928 KiB maximum RSS. Final Ruff and formatting checks passed, as did
individual frontmatter checks for all six changed/new HTML-comment Markdown
files and `git diff --check`. The repository-wide frontmatter checker retains
four base-commit violations described below.

### Gate 3.4 unified dictionary seal

Gate 3.4 freezes the reviewed artifact at 1,416 rows and 32 fields. The exact
scope remains 1,403 native rows plus 13 project metadata rows. The native rows
contain 1,349 master fields, 4 Hatamnia fields, 18 Toni fields, and 32 spec-z
fields. The metadata contract remains seven `source_row_metadata` rows and six
`id_injected` rows. All 13 and only those 13 rows have `project_derived`
descriptions.

The formal dictionary README now defines every header field by exact name,
purpose, allowed/empty representation, provenance, and serialization. It also
records the exact source-family, target-table, origin, description-status,
unit, FITS/source-type, PostgreSQL target-type, boolean, profile-kind, JSON,
and sentinel-rule vocabularies. Source-description whitespace canonicalization,
separate description/unit/note provenance, metadata not-applicable values,
numeric scalar/vector, text, boolean and categorical top-value payloads, and
the future mirror NULL policy are explicit. The README states that profiling
is observation rather than proof and that finite sentinels remain source
values.

The fast production seal validator composes the existing Gate 3.1 structural,
Gate 3.2 semantic, and Gate 3.3 profile validators. It independently checks the
32-field README coverage, exact source/native/metadata/status counts, complete
provenance groups, null/sentinel representations, exact JSON schemas and
ordering, vector cardinality, the first 23 fields, unauthorized derived-field
absence, rectangular physical-line CSV, and the narrow Git ignore exception.
The sealed CSV SHA-256 is
`623e98f82f435c2ee5112af2d07d4553864f665a82a895c175a47d3edfa883cf`;
the canonical first-23-field projection SHA-256 is
`8d9eec917a7e51ef4aa02c0660549b8e80481c34fb5e9e7fbe6a58894a8f1218`.

Strict TDD evidence:

| Cycle | RED evidence | GREEN evidence |
|-------|--------------|----------------|
| README field coverage | Existing README documented only 9 of the 32 tracked header fields | Formal field table covers exactly 32/32 fields |
| Executable seal | Focused CLI test failed because the production validator did not exist | Tracked artifact validates in under one second with exact audited counts |
| Mutation target selection | Three temporary-artifact mutations passed because the CLI ignored supplied validation paths | Empty origin, candidate schema/order drift, and first-23-field drift fail with named diagnostics |
| Controlled README vocabulary | Removing `toni_groups` from a temporary README did not fail validation | Missing controlled values/schema keys/empty representations halt validation |
| Config-driven seal path | `--config` was unrecognized and a configured artifact relocation could not select the default target | Default artifact resolves from `dictionary.columns_v11`; explicit mutation overrides remain available |
| Documented/candidate exclusion | A correctly counted documented `-999` also passed as a candidate in mutation mode | Any candidate value present in the row's documented-sentinel array halts validation |
| Narrow ignore negation | Tracked-file `git check-ignore` queries could not detect removal of the negation rule | A temporary Git repository proves `--no-index` selects the exact `!data/dictionary/columns-v11.csv` rule and fails when removed |

No mutation test changed the tracked CSV. Temporary CSVs were written only
under pytest temporary directories. After independent review fixes, the fast
Gate 3.4 suite returned `12 passed in 2.56s`. The fresh repository suite
excluding only the intentional live byte-reproduction test returned `66
passed, 1 deselected in 122.75s (0:02:02)`.

The pre-review exact live suite, `/usr/bin/time -v pytest -v`, returned `64
passed in 2149.88s (0:35:49)`. The timed process exited 0 after 35:50.12 wall
time, 2,020.00 user seconds, 128.77 system seconds, and 5,724,576 KiB maximum
RSS. It included byte-identical regeneration of both the 1,416-row dictionary
and the candidate report.

The post-review final exact live suite, `/usr/bin/time -v pytest -v`, returned
`67 passed in 2154.14s (0:35:54)`. The timed process exited 0 after 35:54.38
wall time, 2,031.86 user seconds, 126.51 system seconds, and 5,728,892 KiB
maximum RSS. This run includes all three independent-review regressions and
the live byte-identical dictionary/candidate-report reproduction.

Git ignore evidence:

- `git check-ignore data/dictionary/columns-v11.csv` returned 1 with no output;
- `git check-ignore -v data/dictionary/columns-v11.csv` returned 1 with no output;
- `git check-ignore -v --no-index data/dictionary/columns-v11.csv` selected the
  exact `!data/dictionary/columns-v11.csv` negation rule;
- `git ls-files --error-unmatch` found both the sealed CSV and interior README;
- arbitrary `data/arbitrary.csv`, `data/staging/profile-temp.csv`,
  `data/interim/staging.parquet`, and
  `data/dictionary/profiler-temp.csv` remain ignored by their existing rules.

Ruff check and format verification passed for the new validator and test.
Individual frontmatter checks passed for the three changed HTML-comment
Markdown files. `git diff --check` passed. The repository-wide inherited
frontmatter exception remains recorded in section 3.

### Gate 3.5 source integrity and standalone/master fidelity

Gate 3.5 added a reusable read-only verifier that returns structured evidence
and prints a deterministic JSON summary. Source and provenance-pin paths resolve
from `configs/data_paths.yaml`. The verifier composes the established manifest
validator rather than defining a second disk-boundary implementation.

The production manifest preflight observed the exact five-field header, 155
unique data rows, 103 NVMe rows, 52 pinned spec-z rows, zero `.git/**` rows,
zero `cigale-seds/**` rows, and complete live path/hash/size/mtime agreement.
The committed manifest suite returned `17 passed in 104.57s (0:01:44)` with
1,052,384 KiB maximum RSS. The independently invoked production verifier
returned `Manifest validation PASSED` in 1:42.30 with 35,840 KiB maximum RSS.

The CIGALE-SED aggregate reproduced only from the sealed full listing. The
full-listing SHA-256 was
`7eef8f1198ddb61a2c5aaa57fe9dd0bcaa0401cd97f9e434cb0f146645ff7fa9`.
The reproduced boundary was 1,185,322 files, 468,554,723,694 bytes, and row
digest `ff3cefd0b0086ad4a6ff861430c371cdfdd065df2c64ef338e4029e7c65b9810`.
No SED file was walked or opened.

Exactly 16 manifest-bounded consumed inputs were enumerated: the future master
extraction source, seven standalone products, Hatamnia catalog and README,
two Toni tables, the spec-z unique FITS and two READMEs, and the detailed master
description file. Every declared and freshly observed byte count and SHA-256
matched. The Git-controlled unit-conventions input matched its dictionary hash
`8a4d3a724ba435fe5668260e50be45c41f067214567a8723d27d004d3df9ca4a`.
The operator-controlled ETL spec matched
`6f627d9941843f2d8643eca5227aced1d8bc9216310079dc0fed25352cd09b16`.
The external Yang artifact remained outside the local manifest and matched the
authorized `arXiv:2606.14869v1` facts: 5,310,696 bytes and SHA-256
`f4d369c1f3c093dc5990895ac7f95ceecead318339e9fe1b8b823fb51675f0bc`.

Live standalone/master evidence:

| Target | Rows | Native columns | Ordered names/TFORM |
|--------|-----:|---------------:|---------------------|
| `photometry_primary` | 784,016 | 287 | Exact |
| `lephare` | 784,016 | 43 | Exact |
| `photometry_aper` | 784,016 | 148 | Exact |
| `cigale` | 784,016 | 56 | Exact |
| `ml_morpho` | 784,016 | 150 | Exact |
| `bulge_disk` | 784,016 | 461 | Exact |
| `galight_morph` | 784,016 | 204 | Exact |

One shared sample used seed `20260817`: 5,000 distinct sorted ordinals from
the observed 784,016-row population. Its little-endian int64 ordinal digest was
`2d3717fe97dcbdc265c0f48c9d8c49b0d89fcb7c89d71e4905942cffa4ffe0e5`.
All 1,349 native fields were compared (1,183 scalar and 166 vector fields).
Scalar, vector-element, FITS-mask-position, and NaN-position mismatch totals
were all zero. The complete 784,016-value native primary-ID sequences matched.
One primary native ID, six keyless native-ID absences, seven complete zero-based
`source_row` constructions, and six complete injected-ID constructions passed.

The six keyless extensions cannot independently prove cross-HDU object
identity. Their `source_row` and injected-ID alignment relies on the upstream
catalog's cross-HDU ordinal contract. Equal counts and ordinal construction are
not described as an independent identity proof.

Strict TDD began with `25 failed in 0.35s`, all at the missing production
verifier. The same focused suite returned `25 passed in 0.35s` after the
minimal implementation. Its synthetic mutations cover manifest boundaries,
consumed pins, SED serialization, sample construction, FITS structure/TFORM,
scalar/vector/mask/NaN values, full primary IDs, native-ID inventories, and
complete metadata constructions. The first successful live verifier completed
in 3:00.32 with 23,590,708 KiB maximum RSS and zero mismatches.

Independent review found no critical or correctness-blocking issue. Two minor
contract hardenings were accepted before final verification. A fresh RED run
returned two expected failures because mutated SED sidecar `subtree`/`root`
metadata did not halt; the exact consumed 16-input enumeration characterization
already passed. The minimal metadata checks produced `3 passed` for the review
targets, and the expanded focused suite returned `28 passed in 0.35s`. The
23,590,708 KiB live peak was retained as a measured host-capacity fact rather
than changing verified FITS traversal behavior in this gate.

The hardened production verifier rerun returned the same manifest, 16-input,
SED, 1,349-field, zero-mismatch, and 784,016-ID evidence in 2:42.59. Maximum
RSS was 23,591,808 KiB. This run proves the production sidecar's literal
`cigale-seds` subtree and NVMe root metadata also match the sealed listing.

The near-full exact-tree regression returned `91 passed, 1 deselected in
119.96s (0:01:59)`. The only deselection was the intentional 36-minute
`test_default_check_reproduces_tracked_dictionary_byte_identical` integration;
the final full suite included it and returned `95 passed in 2151.88s
(0:35:51)`. The timed invocation completed in 35:52.13 with 5,730,012 KiB
maximum RSS, no swaps, and exit status zero. Changed-file Ruff and format
checks passed, as did `git diff --check`. Individual frontmatter checks passed
for all four changed/new HTML-comment Markdown files, including the ignored
report. The repository-wide checker retained the four inherited violations
already listed in section 3. Repository-wide Ruff retained fifteen unrelated
base-tree errors; the two Gate 3.5 Python files pass independently.

---

## 2. Files Changed

| File | Change |
|------|--------|
| [.gitignore](../.gitignore) | Added the narrow tracked-CSV exception |
| [configs/data_paths.yaml](../configs/data_paths.yaml) | Added dictionary, semantic-evidence, and Gate 3.5 provenance-pin paths |
| [configs/README.md](../configs/README.md) | Documented dictionary, report, semantic-source, and provenance-pin roles |
| [data/README.md](../data/README.md) | Added the required interior data-product index |
| [data/dictionary/README.md](../data/dictionary/README.md) | Expanded the 32-field formal seal, all controlled vocabularies, provenance, profile/JSON schemas, sentinels, and ignore contract |
| [data/dictionary/columns-v11.csv](../data/dictionary/columns-v11.csv) | Added generated structural, semantic, profile, null-state, and sentinel fields |
| [docs/reference/sentinel-candidates-v11.md](../docs/reference/sentinel-candidates-v11.md) | Added the generated Gate 3.3 state and candidate report |
| [docs/reference/README.md](../docs/reference/README.md) | Indexed the candidate report |
| [src/etl/load_dictionary.py](../src/etl/load_dictionary.py) | Added structural/semantic build support and delegated default generation/check to the full profiler |
| [src/etl/profile_values.py](../src/etl/profile_values.py) | Added memory-bounded live profiling, validation, deterministic JSON, candidate rule, and report generation |
| [src/etl/README.md](../src/etl/README.md) | Listed the ETL v2 builder, profiler, seal validator, and source-fidelity verifier |
| [src/etl/validate_dictionary_seal.py](../src/etl/validate_dictionary_seal.py) | Added the fast composed Gate 3.4 artifact/documentation/ignore validator |
| [src/etl/verify_source_fidelity.py](../src/etl/verify_source_fidelity.py) | Added the Gate 3.5 immutable-input and standalone/master verifier |
| [tests/test_load_dictionary.py](../tests/test_load_dictionary.py) | Added discriminating unit, mutation, live integration, and artifact tests |
| [tests/test_load_dictionary_semantics.py](../tests/test_load_dictionary_semantics.py) | Added Gate 3.2 canonicalization, provenance, asymmetry, mutation, unit, semantic-note, and serialization tests |
| [tests/test_profile_values.py](../tests/test_profile_values.py) | Added Gate 3.3 profile, candidate, evidence, artifact, CLI, and report tests |
| [tests/test_dictionary_seal.py](../tests/test_dictionary_seal.py) | Added Gate 3.4 field-coverage, mutation, CSV-shape, and ignore tests |
| [tests/test_verify_source_fidelity.py](../tests/test_verify_source_fidelity.py) | Added Gate 3.5 manifest, hash, sample, value, and ID mutation tests |
| [tests/README.md](../tests/README.md) | Documented the dictionary, profiler, seal, manifest, and fidelity suites |
| [work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md](2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md) | Created this per-gate checkpoint log |

---

## 3. Issues Encountered

| Issue | Resolution |
|-------|------------|
| Startup instructions and repository docs name Doppler `ml01/prd`, but the operator corrected the active config to `ml01/dev` | Recorded for eventual defect registration. Gate 3.1 made no PostgreSQL connection, so no credential config was consumed or changed |
| Ruff reported test import `E402` after the repository root was inserted into `sys.path` | Matched the existing test-suite pattern with a narrow `# noqa: E402`; rerun passed |
| Toni headers and twenty-nine spec-z native field names lack exact field definitions in their pinned documentation | Preserved them as `undocumented_upstream` with empty descriptions; no prose or units were inferred from names |
| Direct execution of the new profiler initially could not import the repository namespace | Added and passed a direct-CLI regression test, then used package-aware module/local imports |
| Expanding the CSV schema initially made the Gate 3.2 validator demand Gate 3.3 fields before profiling | Separated the frozen Gate 3.2 semantic field list from later CSV fields; the existing semantic integration test passed |
| The first exact profile required 32:02 elapsed and reached 5,599.793 MiB RSS | Recorded measured runtime/memory; retained exact per-index/top-three behavior and bounded the largest text table with chunking plus temporary disk aggregation |
| The seal brief requests categorical payload documentation while the reviewed artifact contains only `numeric`, `text`, and `boolean` profile kinds | Documented categorical distributions as the exact `top_values` component within those three frozen kinds; no new kind or profile decision was introduced |
| Independent review found a hardcoded artifact default, a tracked-file ignore blind spot, and missing documented/candidate disjointness | Added strict RED/GREEN regressions and repaired all three without changing the sealed CSV or science/profile decisions |
| The first live Gate 3.5 verifier retained the large full-listing and memory-mapped FITS working sets, reaching 23,590,708 KiB maximum RSS | Recorded the measured resource fact; the run stayed read-only, completed in 3:00.32, and remained within ML01 capacity |
| Repository-wide Ruff reports fifteen errors in unchanged Phase 1/inspection files | Preserved unrelated base code; focused Ruff and format checks for both Gate 3.5 Python files pass |
| The repository-wide frontmatter checker reports four violations already present at base `fa262ff`: two invalid tags in an unchanged recycle-bin document and raw-YAML frontmatter in the P2R-02 and cumulative P2R-03 worklogs | Preserved the mandated central lifecycle worklog template; all six changed/new HTML-comment Markdown files pass individually |

---

## 4. Next Steps

Handoff: Gate 3.5 has verified the source boundary and exact seven-table
standalone/master fidelity. Later gates may consume the sealed dictionary and
machine-readable verifier evidence but may not change source science, profiles,
values, or mappings without new authorization.

1. Register the `ml01/dev` versus stale `ml01/prd` documentation defect at the
   spec-authorized defect-registration gate.
2. Preserve the frozen structural, semantic, profile, null-state, and sentinel
   mappings during later DDL/load work.

<!-- Agent: codex, Runtime: Codex API, Model: unreported, Session: interactive -->
