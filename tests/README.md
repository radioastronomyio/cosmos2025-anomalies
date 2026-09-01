<!--
---
title: "Repository Test Suites"
description: "Discriminating tests for v1.1 provenance and ETL structural contracts"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "4.0"
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
- all twelve configured source tables and thirteen authorized metadata rows;
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

## Generated DDL and disposable PostgreSQL validation

`test_generate_schema_v11.py` proves the Gate 3.6 static contract:

- exact ordered twelve-table and 1,448-column mirror boundary;
- literal sealed `target_type` passthrough and identifier quoting;
- 166 nullable-safe, one-dimensional, exact-cardinality array checks;
- collision-resistant constraint names within PostgreSQL's 63-byte limit;
- exact master PK/UNIQUE/FK constraints, no supplement keys, and the
gate-4.1-established `Id_specz` primary key on `specz_compilation_all`;
- importable provenance contract version 1.0.1 with thirteen fields and the
  amended post-verification registration-time semantics;
- 1,448 mirror and thirteen provenance comments with safe prose escaping;
- generated byte identity and rejection of one-byte hand drift.

`test_verify_schema_v11_scratch.py` is unauthenticated. It proves narrow
scratch-name guards, config-to-environment resolution, protected maintenance
database refusal, exact bidirectional column comparison, and a removed-row
mutation. The dedicated CLI performs the authenticated disposable lifecycle.

```bash
pytest tests/test_generate_schema_v11.py \
  tests/test_verify_schema_v11_scratch.py -v
python src/etl/generate_schema_v11.py --check
doppler run --project ml01 --config dev -- \
  python src/etl/verify_schema_v11_scratch.py
```

The live command must finish with zero matching scratch databases. It never
creates or drops `cosmos2025_v11`, creates `cosmos2025_v11_ro`, or connects to
the read-only `cosmos2025` baseline.

## Persistent bootstrap and post-load verification

`test_bootstrap_v11.py` proves the Gate 3.7 contract without authenticating:

- fixed database, role, handoff, and cleanup targets;
- deterministic v1 fingerprint serialization and byte/hash comparison;
- scalar and vector FITS masks, IEEE NaNs, infinities, signed zero,
  float32/float64 round trips, finite sentinels, and exact metadata injection;
- PostgreSQL CSV escaping for tabs, newlines, backslashes, quotes, empty text,
  arrays, per-element NULL, and a collision-guarded explicit NULL marker;
- exact analyst attributes, grants, negative matrix, and default privileges;
- exclusive mode-0600 five-line handoff creation, name/public-value checks,
  Git ignore/tracking evidence, and secret-output exclusion;
- transactional table evidence, source-row bounds/gaps, injected-ID/FK
  alignment, array shape/NULL counts, and unloaded-table boundaries;
- scalar NULL verification excludes array fields, joined extension-ID
  aggregates qualify the extension alias, and direct-file entry occurs only
  after every validation definition;
- redaction-safe lifecycle diagnostics expose only stage, exception class,
  safe SQLSTATE, and exact reversed-resource names;
- phase-aware pre-seal database cleanup versus post-seal database retention,
  including exact retained-role grant reversal without `DROP OWNED`;
- separate create/load, administration-finalization, and verify-only phase sets;
- guarded finalization requires an exact retained load and proves source,
  manifest, FITS-load, and COPY paths are unreachable.

```bash
pytest tests/test_bootstrap_v11.py -v
```

Database mutation rehearsals use only random
`cosmos2025_v11_scratch_<pid>_<token>` databases and must prove cleanup. The
one persistent run is invoked separately under Doppler `ml01/dev`; the final
repository suite never reruns `--create-load`.

Authenticated rehearsals use production functions in disposable databases.
The final ten-row parity executed the production-generated mirror DDL,
all seven aligned master tables, the complete admin verifier (including the
wrong-array mutation), exact role/privilege observation, the 1-positive and
11-negative session-authorization matrix, and default privileges. Direct
analyst network authentication is not a test claim; ML01 analyst HBA coverage
remains an operator infrastructure action.

The real disposable failure/resume proof injects a post-role administration
failure after a seven-table aligned load, proves the database retained with the
scratch role/handoff absent, then invokes the production `--finalize-admin`
path. The resumed run completes both matrices, default privileges, handoff,
and v1 identity with zero source reads and zero COPY operations before exact
scratch cleanup.

Independent-review regressions additionally require exact retained nullability
and canonical key/reference/CHECK definitions, reject same-named cardinality
drift and dangling handoff symlinks, remove exact-inode partial handoffs after
interrupted `fsync`, redact unexpected CLI exception text in all three modes,
and execute the immutable DDL bytes returned by identity review.

## Supplement and spec-z loading

`test_load_supplements_v11.py` proves the Gate 3.8 boundary without mutating
the persistent catalog:

- exact config/dictionary selection of 54 native fields and no metadata;
- bounded FITS/text COPY conversion with finite sentinels preserved;
- per-table source pin/count transactions and preflight-zero guards;
- complete spec-z flags, sourced definitions, `{3,4}`/`{9}` summaries, and
  reported nonmaterialized primary join;
- exact four-table SELECT grants plus four positive and twenty-four negative
  analyst operations, including deterministic ADMIN OPTION denial;
- pre-seal row cleanup versus post-seal row retention and selective grant
  reversal;
- source-free `--finalize-admin` orchestration with no COPY or TRUNCATE path;
- exact retained schema/null/sentinel/flag/join/master/provenance/v1 checks;
- fixed-path/config-bound handoff security and CLI error redaction.

```bash
pytest tests/test_load_supplements_v11.py -v
```

Authenticated proof uses only random disposable PostgreSQL databases. The
production-function failure/resume proof loads all four pinned sources,
injects a post-seal analyst failure, retains every row, revokes only four
scratch-applied grants, and completes source-free finalization before exact
scratch cleanup. Persistent loading and verify-only are separate operator
commands and are never invoked by the repository suite.

## Provenance registration

`test_load_provenance_v11.py` proves the Gate 3.9 registrar without touching
the persistent catalog:

- exact twelve-table set, configured full paths/basenames, independently
  declared and observed SHA-256 values, source/live counts, manifest reference,
  catalog version, three `v1` supplement versions, eight explicit
  `not_applicable` values, and per-table load `xmin` notes;
- one database `transaction_timestamp()` shared by all rows and the
  generated contract-1.0.1 COMMENT in the same transaction;
- rejection of hash, path, count, version, timestamp, XID, and table-set drift;
- exact old/amended pre-registration schema-comment allowance with every other
  object, column, comment, nullability, and constraint unchanged;
- stable manifest identity across the declared-pin window;
- precommit rollback, exact zero/twelve ambiguous-commit classification,
  postcommit retention, verify-only nonmutation, and redaction-safe lifecycle
  reporting;
- provenance SELECT plus six denied write/DDL/grant operations, alongside the
  inherited Gate 3.8 and master matrices in authenticated scratch proof.

```bash
pytest tests/test_load_provenance_v11.py -v
```

The authenticated disposable proof uses the exact generated twelve-table
schema, aligned rows in all mirrors, a simulated successful commit with
an interrupted return, all seven mutation classes under rollback, and exact
scratch absence. Persistent `--load` and `--verify-only` remain separate
operator commands and are never invoked by the repository suite.

## Dictionary-driven conformance

`test_generate_conformance_v11.py` proves deterministic generation from the
sealed dictionary: 1,448 unique explicit cases, the exact
1,349/22/32/13 source split, the 1,403/7/6 origin split, 166 named array
dimension/cardinality contracts, importable tracked output, and `--check` byte
identity. Removed rows, duplicate identifiers, and hand-edited output fail.

`test_verify_conformance_v11.py` exercises the production batched snapshot and
local validator. It requires exact twelve-table, 1,429-column, 192-constraint,
twelve-row provenance, all-table SELECT-only ACL, and per-case type/comment/
origin/array coverage. Focused mutations independently fail type, comment,
object, constraint, provenance, ACL, origin, and array element-count checks.
The query-budget regression fixes catalog capture at five batched queries rather
than one query per dictionary row.

The lifecycle tests cover the read-only live orchestration, class/SQLSTATE-only
CLI diagnostics, exact random scratch-name guards, ambiguous CREATE cleanup,
separate comment/type rollback detection, exact-resource drop, and protected
identity equality. The authenticated mutation proof is an explicit CLI action;
normal pytest never changes either persistent database.

```bash
pytest tests/test_generate_conformance_v11.py \
  tests/test_verify_conformance_v11.py -v
python src/etl/generate_conformance_v11.py --check
```

## Source-fresh value reconciliation

`test_reconciliation_core_v11.py` fixes the Gate 3.11 sampling, target-cast,
IEEE, NULL, array, and protected-ledger semantics. It rejects invalid sampling
boundaries, integer overflow, wrong scalar/array shapes, non-FITS NULL
inference, unsafe ledger destinations, inode replacement, and incomplete
mismatch records.

`test_reconcile_values_v11.py` covers generated source contracts, historical
versus live key names, full source uniqueness and tuple fallback, one logical
source open per table, 500/2,000-row DB batching, exact all-column comparison,
element-indexed mismatches, runtime-derived success totals, hash-only pinning,
redacted CLI output, and before/after identity on source-open, fetch, ledger-
write, transaction-close, count-drift, cleanup, and identity failures.

The authenticated `--scratch-proof` is intentionally separate from pytest. It
builds all historical synthetic sources and the exact generated target schema,
passes the production reconciler, detects eight rollback-isolated mutations,
round-trips finite float4/float8 rounding plus masks/IEEE/sentinel/integer/
array edges through PostgreSQL, and proves exact scratch absence. Normal tests
never access the persistent target or immutable source holdings.

```bash
pytest tests/test_generate_conformance_v11.py \
  tests/test_reconciliation_core_v11.py \
  tests/test_reconcile_values_v11.py -v
python src/etl/generate_conformance_v11.py --check
```

## Generated schema reference

`test_generate_schema_docs_v11.py` proves that Gate 3.12 maps every one of the
32 dictionary fields, renders all 1,448 mirror columns and the fixed provenance
contract deterministically, validates the bounded live snapshot, and rejects
unsafe or drifted output paths. It also freezes every file under `assets/`
byte-for-byte, including the supplied icon, while checking the repository's
current operational orientation.

```bash
pytest tests/test_generate_schema_docs_v11.py -v
```

## Generated ETL v2 verification surface

`test_generate_verification_surface_v11.py` proves exact configured input
seals, full dictionary-to-conformance and manifest-to-provenance joins, all 14
findings, complete 49/793/11/17 appendices, 261,975 quality-flag rows, deferred
T_A questions, blank operator dispositions, atomic output classification, CLI
redaction, the no-source/no-database call graph, and the exact active-to-archive
central-spec transition. The transition accepts one regular sealed inode at
the active or durable archive path and rejects duplicate, absent, linked, or
redirected states.

The Gate 3.14 post-archive simulation additionally proves that archive-only
central-spec bytes reproduce all sealed dictionary semantic rows without
changing the 13 historical provenance locators, while the schema, conformance,
and verification-surface check functions remain byte-identical.

```bash
pytest tests/test_generate_verification_surface_v11.py -v
python src/etl/generate_verification_surface_v11.py --check
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

## P2R-04 spec-z linkage tests

`test_dictionary_seal.py` gains the gate 4.2 mutation proof: duplicating one
`specz_compilation_all` target identifier must fail the dictionary validator
with `Identifier collision`. The renamed galaxy-level table and the
twelve-table/twelve-row boundaries flow through every existing suite; the
Gate 3.11 reconciler suite pins its historical eleven-table case filter; the
Gate 3.13 verification-surface suite installs a seal-checked historical-bytes
provider from the local git object store (ref `e65242a`) so the frozen
operator document regenerates while the compiler stays offline. The slow
`test_default_check_reproduces_tracked_dictionary_byte_identical` re-profiles
every source (~34 minutes on ML01) and asserts the 1,448-row byte-identical
reproduction.
