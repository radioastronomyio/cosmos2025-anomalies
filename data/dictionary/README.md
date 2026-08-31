<!--
---
title: "ETL v2 Unified Dictionary Seal"
description: "Frozen structural, semantic, profile, null-state, and sentinel contract for the COSMOS-Web v1.1 source mirror"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: etl
related_documents:
  - "[Dictionary Builder](../../src/etl/load_dictionary.py)"
  - "[Value Profiler](../../src/etl/profile_values.py)"
  - "[Sentinel Candidate Report](../../docs/reference/sentinel-candidates-v11.md)"
  - "[Data Path Configuration](../../configs/data_paths.yaml)"
---
-->

# ETL v2 Unified Dictionary Seal

This directory contains the sealed load dictionary for the COSMOS-Web v1.1
lossless source mirror. The contract covers 1,416 rows and 32 fields: 1,403
native source fields, seven generated source-row fields, and six injected
identifiers. It freezes the reviewed Gate 3.1 structural mapping, Gate 3.2
semantics, and Gate 3.3 profiles without authorizing DDL, loading, source-value
changes, or new science-derived fields.

Profiling records observations. It is not proof that a frequent value is a
sentinel, and it does not change a source value. Units and descriptions are
never inferred from column names. Source descriptions are whitespace
canonicalized for the CSV, but the original text remains recoverable from the
exact source locator and SHA-256 digest.

---

## 1. Contents

```
dictionary/
├── columns-v11.csv     # Sealed 1,416-row, 32-field load dictionary
└── README.md           # Formal dictionary and serialization contract
```

---

## 2. Files

| File | Description | Status |
|------|-------------|--------|
| [columns-v11.csv](columns-v11.csv) | One fixed-schema row per native or authorized metadata field | Sealed |

## 3. Fixed CSV Fields

The CSV header order is normative. An empty cell means the empty string, with
no whitespace. JSON empty arrays are the two characters `[]`. Boolean cells
are the case-sensitive strings `True` and `False`. The field-specific rules
below are exhaustive.

| Field | Purpose | Allowed value and empty representation | Provenance or serialization |
|-------|---------|----------------------------------------|-----------------------------|
| `source_family` | Groups fields by upstream product family. | One controlled value from section 4. Never empty. | Identifies the product family, not a target schema. |
| `source_file` | Locates the exact source artifact used for the field. | Config-resolved absolute path. Never empty. | Immutable source locator; no source content is copied or modified by the seal. |
| `source_locator` | Locates the table or header inside `source_file`. | FITS HDU locator, text-header locator, or the primary-HDU locator used by injected metadata. Never empty. | Read with `source_file` to recover structural origin. |
| `source_column` | Preserves the exact upstream field name or authorized metadata name. | Exact case-sensitive source name, `source_row`, or injected `id`. Never empty. | Hyphens and other punctuation remain unchanged here. |
| `source_type` | Records the exact FITS TFORM, text inference, or metadata construction type. | One mapping input from section 6. Never empty. | Strings retain their fixed source width here even though PostgreSQL uses `text`. |
| `element_count` | Records structural elements per source row. | Base-10 integer greater than zero. Never empty. | Scalar numeric/logical fields use `1`; `nA` strings use character width `n`; numeric `nD`/`nE` vectors use vector length `n`. |
| `target_table` | Names the future source-mirror table. | One controlled value from section 4. Never empty. | This seal does not create the table. |
| `target_identifier` | Names the future PostgreSQL column. | Normalized unquoted identifier from section 5. Never empty. | Must be unique within `target_table` and at most 63 UTF-8 bytes. |
| `target_type` | Preserves the lossless PostgreSQL type mapping. | One controlled mapping output from section 6. Never empty. | Numeric vectors remain arrays; strings map to `text`. |
| `column_origin` | Distinguishes native and authorized metadata rows. | `source_native`, `source_row_metadata`, or `id_injected`. Never empty. | Exact origin counts are fixed in section 4. |
| `description_text` | Stores the canonical source definition or authorized project metadata definition. | Canonicalized sourced/project text, or empty only for `undocumented_upstream`. | Its provenance group is the next three fields. It never contains an inferred unit or semantic note. |
| `description_source` | Identifies the description evidence artifact. | Exact path/reference when `description_text` is populated; otherwise empty. | All three description-provenance cells are populated together or empty together. |
| `description_locator` | Locates the definition inside `description_source`. | Exact section, line, table-pattern, or spec locator when populated; otherwise empty. | Completes the description provenance group. |
| `description_source_sha256` | Pins the exact description evidence bytes. | Exactly 64 lowercase hexadecimal characters when populated; otherwise empty. | Makes canonicalized source prose recoverable with source and locator. |
| `description_status` | States how the description was established. | One controlled value from section 7. Never empty. | Status determines the description and provenance requirements. |
| `unit` | Records only an explicitly sourced unit. | One controlled literal from section 7, including `unknown`. Never empty. | `unknown` is explicit and has an empty unit-provenance group. |
| `unit_source` | Identifies the exact unit evidence artifact. | Exact path/reference for a known unit; empty for `unknown`. | All three unit-provenance cells are populated together or empty together. |
| `unit_locator` | Locates the unit evidence. | Exact source locator for a known unit; empty for `unknown`. | May differ from `description_locator`, such as a separate Units column. |
| `unit_source_sha256` | Pins the exact unit evidence bytes. | Exactly 64 lowercase hexadecimal characters for a known unit; empty for `unknown`. | Completes the independent unit provenance group. |
| `semantic_note` | Records a project interpretation that must remain separate from source prose. | Exact note text when authorized; otherwise empty. | Current notes state only the reviewed LePhare log10 and CIGALE linear conventions. |
| `semantic_note_source` | Identifies semantic-note evidence. | Exact path/reference when `semantic_note` is populated; otherwise empty. | All three note-provenance cells are populated together or empty together. |
| `semantic_note_locator` | Locates the semantic-note evidence. | Exact locator when populated; otherwise empty. | Never substitutes for description or unit provenance. |
| `semantic_note_source_sha256` | Pins semantic-note evidence bytes. | Exactly 64 lowercase hexadecimal characters when populated; otherwise empty. | Completes the independent semantic-note provenance group. |
| `profile_json` | Stores the type-appropriate source-value profile. | Canonical compact JSON for every `source_native` row; empty for the 13 metadata rows. | Exact schemas and ordering are defined in section 8. |
| `has_fits_mask` | Summarizes whether any scalar/index has a declared FITS-mask observation. | `True` or `False`; metadata rows use `False`. Never empty. | Independent of NaNs and finite sentinel values. |
| `has_nan` | Summarizes whether any unmasked numeric scalar/index contains NaN. | `True` or `False`; metadata rows use `False`. Never empty. | Independent of FITS masks and finite sentinel values. |
| `documented_sentinel_values_json` | Lists finite sentinel values supported by exact upstream evidence. | Canonical compact numeric JSON array; `[]` means none and is never an empty cell. | Values remain source values. Evidence uses the next four fields. |
| `documented_sentinel_evidence_text` | Stores the canonical source block containing every documented value token. | Canonicalized evidence when the value array is nonempty; otherwise empty. | Must contain each claimed numeric token exactly. |
| `documented_sentinel_source` | Identifies documented-sentinel evidence. | Exact path/reference when the value array is nonempty; otherwise empty. | All four documented-evidence cells are populated together or empty together. |
| `documented_sentinel_locator` | Locates documented-sentinel evidence. | Exact locator when the value array is nonempty; otherwise empty. | Completes exact evidence recovery. |
| `documented_sentinel_source_sha256` | Pins documented-sentinel evidence bytes. | Exactly 64 lowercase hexadecimal characters when the value array is nonempty; otherwise empty. | Completes the documented-sentinel provenance group. |
| `candidate_sentinel_values_json` | Stores conservative finite candidate observations. | Canonical compact array of candidate objects; `[]` means none and is never an empty cell. | Exact schema, rule, arithmetic, and ordering are defined in section 9. |

## 4. Controlled Structural Vocabularies

### Source families

| Controlled value | Meaning |
|------------------|---------|
| `master_catalog` | Seven COSMOS-Web master-catalog FITS tables and their 13 metadata rows |
| `hatamnia_lss` | Hatamnia `OVERDENSITY` FITS table |
| `toni_groups` | Toni group text table |
| `toni_memberships` | Toni membership text table |
| `specz_compilation` | Unique spec-z FITS table |

### Target tables

The exact controlled values are `photometry_primary`, `photometry_aper`,
`lephare`, `cigale`, `ml_morpho`, `bulge_disk`, `galight_morph`,
`lss_overdensity`, `galaxy_groups`, `galaxy_group_memberships`, and
`specz_compilation`. No alias is accepted.

### Column origins and fixed counts

| Controlled value | Rows | Contract |
|------------------|-----:|----------|
| `source_native` | 1,403 | One row for every upstream field: 1,349 master, 4 Hatamnia, 18 Toni, and 32 spec-z fields |
| `source_row_metadata` | 7 | One zero-based `source_row` for each master target table |
| `id_injected` | 6 | Primary-photometry `id` injected by equal zero-based row ordinal into the six other master tables |

Only the 13 non-native rows are project-derived. The master native total of
1,349 is the Gate 3.1 live `TFIELDS` total. The 54 non-master native fields are
4 Hatamnia supplement fields, 18 Toni supplement fields, and 32 spec-z fields.
There are 1,416 rows in total.

## 5. Target Identifier Contract

Normalization is deterministic:

1. Lowercase the exact `source_column`.
2. Replace every run of characters outside `[a-z0-9_]` with one underscore.
3. Prefix `c_` if the result does not begin with `[a-z_]` or equals a
   PostgreSQL Appendix C reserved word.
4. Halt on an invalid result, a duplicate `(target_table, target_identifier)`,
   or an identifier longer than 63 UTF-8 bytes. PostgreSQL truncation and
   collision repair are forbidden.

`source_row_metadata` and `id_injected` use their explicit authorized target
names. The Toni source name `ID` normalizes to `id`; it is not renamed by
context.

## 6. Type and Element-Count Contract

| Source type | PostgreSQL target type | `element_count` |
|-------------|------------------------|----------------:|
| `D` | `double precision` | 1 |
| `E` | `real` | 1 |
| `K` | `bigint` | 1 |
| `J` | `integer` | 1 |
| `I` | `smallint` | 1 |
| `L` | `boolean` | 1 |
| `nA`, including observed `3A`, `4A`, and `20A` | `text` | Fixed character width `n` |
| `nD`, including observed `5D` | `double precision[]` | Vector length `n` |
| `nE`, including observed `5E` | `real[]` | Vector length `n` |
| `text integer` | `bigint` | 1 |
| `text decimal` | `double precision` | 1 |
| `text string` | `text` | 1 |
| `generated zero-based row ordinal` | `bigint` | 1 |

Repeated non-string FITS types other than `D` and `E` are outside this seal and
halt validation. String width is not an array cardinality: `20A` is one text
value with source width 20. Numeric `5D` and `5E` fields are five-element
vectors, retain PostgreSQL array types, and have five per-index profiles.

## 7. Semantic and Provenance Contract

### Description status and precedence

| Controlled value | Rows | Required representation |
|------------------|-----:|-------------------------|
| `verified` | 1,150 | Exact source definition, canonicalized, with complete description provenance |
| `pattern_expanded` | 204 | Exact reviewed Yang Table 1 pattern applied only to the observed GALIGHT columns, with complete provenance |
| `undocumented_upstream` | 49 | Empty description text/provenance and unit `unknown` unless a separate exact unit source exists |
| `project_derived` | 13 | Authorized metadata definition and complete central-spec provenance; never allowed on a native row |

For native rows, an exact field definition takes precedence over an applicable
reviewed pattern; the reviewed GALIGHT pattern is used only for its exact
observed set; otherwise the row is `undocumented_upstream`. `project_derived`
is reserved for the seven `source_row_metadata` and six `id_injected` rows.
Column names are never expanded into prose.

Source description/evidence canonicalization trims both ends and replaces each
internal Unicode whitespace run, including CR, LF, and tab, with one ASCII
space. It does not paraphrase, compose, correct, or infer content. The exact
source path/reference, locator, and SHA-256 make the pre-canonical source block
recoverable.

Description, unit, and semantic-note evidence are three separate provenance
groups. A nonempty fact requires its own source, locator, and SHA-256; partial
groups are invalid. Known units are copied only from exact evidence. The exact
unit vocabulary present in the sealed CSV is `unknown`, `microJy`, `AB mag`,
`arcsecond`, `Myr`, `1/yr`, `deg`, `Msol`, `Msol yr-1`, `yr-1`,
`dimensionless`, `M_sol`, `M_sol/yr`, `yr`, `degrees`, and `dex/Myr`.
`unknown` is a literal controlled value, not an empty cell, and requires all
three unit provenance fields to be empty.

An empty `semantic_note` requires empty note provenance. A populated note
requires all three note provenance fields. Notes never modify
`description_text`. The retired science-derived `ssfr_cigale` field and all
other non-source science fields are excluded from the dictionary.

## 8. Profile JSON Contract

### Canonical JSON

All JSON cells use UTF-8 JSON with no ASCII escaping requirement, compact
separators (`,` and `:` with no surrounding whitespace), and recursively
lexicographically sorted object keys. Arrays preserve the entry order defined
below. Numbers are JSON integers or finite JSON floats; counts are nonnegative
integers and fractions are finite numbers in `[0,1]`. `NaN`, `Infinity`, and
`-Infinity` tokens are rejected. JSON booleans are used only as observed
boolean values inside `top_values`; CSV summary booleans remain `True` or
`False` strings.

Every native `profile_json` is an object with exactly these keys:

```json
{"kind":"numeric|text|boolean","profiles":[]}
```

There is no standalone `categorical` kind. Exact categorical observations for
numeric, text, and boolean sources use the `top_values` array described below.

### Numeric scalar and vector/per-index payloads

A numeric scalar contains exactly one profile with `index:null`. A numeric
vector contains exactly `element_count` profiles ordered by zero-based integer
`index` from 0 through `element_count - 1`. Each numeric profile has exactly:

```json
{"finite_max":0,"finite_min":0,"fits_mask_count":0,"fits_mask_fraction":0.0,"index":null,"nan_count":0,"nan_fraction":0.0,"non_null_count":0,"non_null_fraction":0.0,"row_count":0,"top_values":[]}
```

`row_count` is the number of source rows for the table/index.
`fits_mask_count` counts values masked only by declared FITS null metadata.
`nan_count` counts unmasked NaNs. `non_null_count` excludes masks and NaNs, so
`fits_mask_count + nan_count + non_null_count = row_count`. Each fraction uses
`row_count` as denominator, with `0.0` for a zero denominator.

`finite_min` and `finite_max` summarize unmasked, non-NaN finite values and are
finite JSON numbers; both are `null` when no finite value exists. Positive or
negative infinities may contribute to `non_null_count` but never appear in
finite extrema, top values, candidate values, or JSON tokens.

### Text, boolean, and categorical payloads

Text uses `kind:"text"`; boolean uses `kind:"boolean"`. Both are scalar in
this seal, contain one profile with `index:null`, and use exactly:

```json
{"fits_mask_count":0,"fits_mask_fraction":0.0,"index":null,"non_null_count":0,"non_null_fraction":0.0,"row_count":0,"top_values":[]}
```

For text and boolean data, `fits_mask_count + non_null_count = row_count`.
Fractions use `row_count`, with `0.0` for a zero denominator. Text `value`
members are exact JSON strings; boolean values are JSON `true` or `false`.

For every kind, `top_values` is a categorical array of at most three objects,
each with exactly `count` and `value`. Entries are ordered by descending count,
then ascending exact typed value. Numeric top values include only finite
values. Counts are positive integers and may not exceed `non_null_count`.

`has_fits_mask` is `True` exactly when any scalar/index has a positive
`fits_mask_count`. `has_nan` is `True` exactly when any numeric scalar/index has
a positive `nan_count`. These states are independent: a field can have both,
either, or neither.

### Metadata not-applicable representation

Every `source_row_metadata` and `id_injected` row uses this exact profile state:

| Field | Literal value |
|-------|---------------|
| `profile_json` | empty cell |
| `has_fits_mask` | `False` |
| `has_nan` | `False` |
| `documented_sentinel_values_json` | `[]` |
| `documented_sentinel_evidence_text` | empty cell |
| `documented_sentinel_source` | empty cell |
| `documented_sentinel_locator` | empty cell |
| `documented_sentinel_source_sha256` | empty cell |
| `candidate_sentinel_values_json` | `[]` |

These values mean not applicable, not that constructed metadata was profiled
from source rows.

## 9. Sentinel Contracts

### Documented sentinels

`documented_sentinel_values_json` is a numeric array ordered by ascending
numeric value. A nonempty array requires all four evidence cells and every
numeric token must occur exactly in the canonical evidence text. The evidence
text follows the whitespace rule in section 7. The sealed artifact has one
documented field: `photometry_primary.id_specz_khostovan25`, value `-999`.
`[]` plus four empty evidence cells means that no exact upstream sentinel
definition was established; it does not prove there is no sentinel.

### Conservative candidates

Each candidate object has exactly these recursively key-sorted members:

```json
{"count":1000,"index":null,"non_null_fraction":0.001,"rule_version":"cosmos_v11_candidate_sentinel_v1","value":999}
```

`index:null` is the explicit scalar marker. Vectors use a zero-based integer
index valid for that field. Entries are ordered first by profile index, with a
scalar's `null` as its only index, then by ascending numeric value within that
index.

Rule version `cosmos_v11_candidate_sentinel_v1` selects a value only when all
of these conditions hold:

1. The value is an undocumented finite integer-valued numeric observation and
   `abs(value)` equals exactly `10^k - 1` for an integer `k >= 2`.
2. Its exact per-scalar or per-index count satisfies `count >= 1000`.
3. Its exact prevalence satisfies `count * 1000 >= non_null_count`. Integer
   multiplication is used instead of rounded floating-point comparison.
4. It is not a documented sentinel and is not documented as a valid flag or
   category value.

`non_null_fraction` is exactly `count / non_null_count`, with the same
per-scalar or per-index denominator. Every count is positive and cannot exceed
that denominator. Candidate frequency is an observation, not a semantic
classification.

### Future mirror null policy

Declared FITS masks and NaNs may become SQL `NULL` in a future source mirror.
Every finite documented sentinel and every finite candidate sentinel remains
the exact source value. Gate 3.4 does not authorize sentinel-to-NULL conversion,
filtering, correction, or relabeling.

## 10. Seal Invariants

The fast seal validator reads the tracked CSV and README without re-profiling.
It composes the existing structural, semantic, and profile validators, then
checks the frozen counts, controlled vocabularies, exact 32-field header,
rectangular line-oriented CSV, JSON schemas/order/version, vector cardinality,
unauthorized-field absence, and the sealed first-23-field projection.

The fixed native counts are:

| Target table | Native rows |
|--------------|------------:|
| `photometry_primary` | 287 |
| `photometry_aper` | 148 |
| `lephare` | 43 |
| `cigale` | 56 |
| `ml_morpho` | 150 |
| `bulge_disk` | 461 |
| `galight_morph` | 204 |
| `lss_overdensity` | 4 |
| `galaxy_groups` | 14 |
| `galaxy_group_memberships` | 4 |
| `specz_compilation` | 32 |
| **Total** | **1,403** |

The CSV contains no embedded CR/LF cell and exactly one physical line per
header/data record. General `data/` and `*.csv` ignore rules remain active.
Only `data/dictionary/columns-v11.csv` has the narrow tracked-CSV exception;
arbitrary CSV, parquet, staging, profiler temporary, and other data artifacts
remain ignored.

## 11. Regeneration and Validation

Fast seal validation does not open the live source products:

```bash
python src/etl/validate_dictionary_seal.py
pytest tests/test_dictionary_seal.py -v
```

The live byte-reproduction check remains the final source-integrity check and
can take tens of minutes on ML01:

```bash
python src/etl/load_dictionary.py --check
```

All source and output paths come from `configs/data_paths.yaml`.

## 12. Related

| Document | Relationship |
|----------|--------------|
| [Parent](../README.md) | Repository data-product directory |
| [Dictionary Builder](../../src/etl/load_dictionary.py) | Regenerates and validates structural and semantic rows |
| [Value Profiler](../../src/etl/profile_values.py) | Regenerates profiles and sentinel observations |
| [Candidate Report](../../docs/reference/sentinel-candidates-v11.md) | Reports mask, NaN, documented, and candidate observations |
