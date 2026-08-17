<!--
---
title: "Repository Test Suites"
description: "Discriminating tests for v1.1 provenance and ETL structural contracts"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "3.4"
status: "Active"
tags:
  - type: directory-readme
  - domain: testing
related_documents:
  - "[Data Manifest v1.1](../docs/reference/data-manifest-v1.1.md)"
  - "[Builder](../src/inspection/build_data_manifest.py)"
  - "[Load Dictionary](../data/dictionary/README.md)"
---
-->

# Repository Test Suites

## Load dictionary

`test_load_dictionary.py` proves the ETL v2 Gate 3.1 structural contract:

- literal FITS scalar, string, and vector mappings;
- deterministic PostgreSQL identifier generation;
- named mutation diagnostics for wrong `D` mapping, collision, and
  overlength identifiers;
- all eleven configured source tables and thirteen authorized metadata rows;
- live `TFIELDS`, native-ID, vector-count, and Toni `ID` to `id` reconciliation;
- byte-identical regeneration of `data/dictionary/columns-v11.csv`.

Run the focused suite and production reproducibility check:

```bash
pytest tests/test_load_dictionary.py -v
python src/etl/load_dictionary.py --check
```

`test_load_dictionary_semantics.py` proves the Gate 3.2 semantic contract:

- canonical source-description whitespace and evidence hashes;
- exact status precedence, including thirteen project-derived rows and
  upstream gaps;
- the 204-row asymmetric Yang Table 1 expansion and rejection of a 208-row
  mutation;
- independently cited units and separation of LePhare/CIGALE semantic notes;
- fixed-width CSV serialization with no embedded newlines.

Run both dictionary gates together:

```bash
pytest tests/test_load_dictionary.py tests/test_load_dictionary_semantics.py -v
```

`test_profile_values.py` proves the Gate 3.3 value-profile contract:

- FITS masks and NaNs remain independent;
- finite documented/candidate values remain finite source observations;
- vectors retain one complete profile per index;
- exact top-three tie ordering and compact JSON are deterministic;
- the frozen denominator, integer threshold comparison, pattern, per-index
  rule, documented/category exclusions, and rule version are discriminating;
- unsupported documented-sentinel evidence and incomplete candidates fail;
- all 1,403 native rows and 830 vector indices are present in the tracked
  artifact, while thirteen metadata rows use explicit not-applicable cells;
- the generated candidate report reconciles every dictionary candidate.

Run the focused profiler tests without a fresh 32-minute live pass:

```bash
pytest tests/test_profile_values.py -v
```

`python src/etl/load_dictionary.py --check` performs the full live profile and
byte-identical dictionary/report check.

`test_dictionary_seal.py` proves the Gate 3.4 frozen contract from the tracked
artifact without live profiling:

- all 32 CSV fields and every controlled vocabulary/schema are documented;
- the default artifact follows `dictionary.columns_v11` from config;
- exact native, metadata, source-family, target-table, status, and provenance
  counts remain fixed;
- ragged records, embedded newlines, empty origins, unauthorized fields, and
  first-23-field drift fail;
- canonical profile and sentinel JSON schemas, entry order, per-index
  cardinality, documented/candidate disjointness, and candidate rule version
  remain sealed;
- the dictionary CSV/README are tracked while arbitrary CSV, staging,
  profiler-temporary, and other data products remain ignored; a temporary Git
  fixture proves removal of the exact negation fails.

Run the fast seal suite and production validator:

```bash
pytest tests/test_dictionary_seal.py -v
python src/etl/validate_dictionary_seal.py
```

## Source integrity and FITS fidelity

`test_verify_source_fidelity.py` proves the Gate 3.5 read-only preflight and
standalone/master comparison contract:

- exact manifest header, root/count boundary, unique keys, and explicit
  rejection of undeclared, duplicate, `.git/**`, and `cigale-seds/**` rows;
- absent consumed inputs and separate declared/observed SHA-256 or byte-count
  drift halt with named diagnostics;
- the CIGALE-SED subtree/root metadata and row-block digest retain the exact
  full-listing boundary and CRLF serialization;
- the consumed-input enumeration remains the exact configured 16-name/path set;
- the shared ordinal sample is seeded, deterministic, sorted, distinct, and
  the exact requested size;
- standalone/master row, ordered name, and FITS TFORM drift fail separately;
- scalar, vector-element, FITS-mask-position, and NaN-position mismatches are
  independent exact counts;
- complete primary-ID equality, native-ID presence/absence, zero-based
  `source_row`, and injected-ID construction cover their full populations.

Run the focused mutations and the live verifier:

```bash
pytest tests/test_verify_source_fidelity.py -v
python src/etl/verify_source_fidelity.py
```

## Manifest validator

`test_build_data_manifest.py` proves the manifest machine contract in two layers.

## Isolated fixture tests

A passing temporary control (small root + its exact manifest) is mutated one
property at a time; each test asserts a nonzero exit and the named diagnostic:

| Mutation | Diagnostic |
|----------|------------|
| Missing header | `Header mismatch` |
| Renamed header field | `Header mismatch` |
| Reordered header | `Header mismatch` |
| Duplicate key | `Duplicate key` |
| Added `.git/config` row | `Git-internal path` |
| Manifest-only row missing on disk | `Manifest row missing on disk` |
| Disk-only file | `Disk file missing from manifest` |
| Hash-only drift | `Hash mismatch` (only) |
| Size-only drift | `Size mismatch` (only) |
| Mtime-only drift | `Mtime mismatch` (only) |

## Production tests

- The committed CSV is byte-for-byte the serialized `0f3e31d` baseline minus
  its 29 `.git/**` records (CRLF convention, order, and final newline included).
- Structure: exact ordered header, 155 data rows, 103 root-1 / 52 root-2,
  unique `(root, relative_path)` keys, zero `.git/**` paths.
- Full read-only production verify over both configured roots (integration;
  hashes ~131 GB, allow several minutes).

## Running

```bash
pytest tests/test_build_data_manifest.py -v              # full suite
python src/inspection/build_data_manifest.py --verify    # production verify
python src/inspection/build_data_manifest.py --verify \
  --csv <csv> --root <dir> [--root <dir>:git]            # isolated target
```
