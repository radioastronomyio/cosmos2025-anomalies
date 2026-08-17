<!--
---
title: "ETL v2 Load Dictionary"
description: "Structural and semantic dictionary for the COSMOS-Web v1.1 lossless mirror"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "0.3"
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

# ETL v2 Load Dictionary

Gate 3.1 structural skeleton, Gate 3.2 semantic reconciliation, and Gate 3.3
value profiling for the COSMOS-Web v1.1 lossless mirror. The CSV records native
source fields, thirteen authorized metadata rows, canonical semantics,
type-appropriate profiles, independent null states, and separate documented and
candidate sentinel evidence. Gate 3.4 remains responsible for the formal
dictionary seal.

---

## 1. Contents

```
dictionary/
├── columns-v11.csv     # Generated structural and semantic mapping
└── README.md           # Scope and regeneration contract
```

---

## 2. Files

| File | Description | Status |
|------|-------------|--------|
| [columns-v11.csv](columns-v11.csv) | One row per native field plus seven `source_row` and six injected `id` rows, enriched through Gate 3.3 | Active, not yet sealed |

## 3. Gate 3.3 Profile Fields

| Field | Contract |
|-------|----------|
| `profile_json` | Compact, key-sorted type-appropriate payload; empty means not applicable for the thirteen metadata rows |
| `has_fits_mask` | Explicit boolean; true when any array index contains a value masked by declared FITS null metadata |
| `has_nan` | Explicit boolean; true when any unmasked numeric scalar/index contains a NaN |
| `documented_sentinel_values_json` | Compact numeric array in stable numeric order; `[]` means no exact upstream definition was found |
| `documented_sentinel_evidence_text` | Exact Gate 3.2 whitespace-canonicalized source block that defines the sentinel |
| `documented_sentinel_source` | Exact source path or reference for documented sentinel evidence |
| `documented_sentinel_locator` | Exact evidence locator within the source |
| `documented_sentinel_source_sha256` | SHA-256 of the exact evidence artifact |
| `candidate_sentinel_values_json` | Compact candidate-entry array ordered by index then numeric value |

`profile_json` always has `kind` and `profiles`. Numeric scalar profiles contain
one entry with `index=null`. Numeric vector profiles contain one entry for each
zero-based index in dictionary element-count order. Each numeric entry records
source rows, non-null population, independent FITS-mask and NaN counts and
fractions, finite min/max, and the top three exact finite values with counts.
Text and boolean profiles record source rows, non-null population, FITS-mask
counts and fractions, and deterministic exact frequent values. Ties use exact
value order. Fractions use source row count except candidate fraction, whose
denominator is the scalar/index non-null population. JSON contains no NaN or
Infinity token.

The explicit metadata convention is empty `profile_json`, false mask/NaN
booleans, `[]` for both sentinel arrays, and empty documented-evidence fields.
These cells do not claim that constructed metadata was observed in a source.

### Candidate rule

Rule version `cosmos_v11_candidate_sentinel_v1` selects an undocumented finite
numeric value when all of these conditions hold:

1. `abs(value)` is exactly `10^k - 1` for integer `k >= 2`.
2. `count >= 1000` and `count * 1000 >= non_null_count` for that scalar or
   vector index.
3. The value is not documented as a valid flag or category value.

Each entry records value, exact count, non-null fraction, vector index or the
explicit scalar marker, and rule version. The integer comparison avoids
threshold rounding. Candidates are observations only; profiling changes no
source value.

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Parent](../README.md) | Repository data-product directory |
| [Dictionary Builder](../../src/etl/load_dictionary.py) | Regenerates and validates the CSV |
| [Value Profiler](../../src/etl/profile_values.py) | Reads every native value and enriches the CSV |
| [Candidate Report](../../docs/reference/sentinel-candidates-v11.md) | Generated mask, NaN, documented, and candidate observations |

## 5. Regeneration

```bash
python src/etl/load_dictionary.py
python src/etl/load_dictionary.py --check
```

Both commands read paths from `configs/data_paths.yaml`. The check exits
nonzero if the tracked CSV or candidate report differs from a fresh live
profile. A full exact profile takes tens of minutes on ML01.
