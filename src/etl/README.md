<!--
---
title: "ETL Pipeline"
description: "COSMOS-Web catalog extraction, load-dictionary, and verification scripts"
author: "VintageDon"
date: "2026-08-18"
version: "2.1"
status: "Active"
tags:
  - type: directory-readme
  - domain: etl
---
-->

# ETL Pipeline

Dictionary-driven FITS/text-to-PostgreSQL pipeline and verification surface for
the verified COSMOS-Web v1.1 source mirror: seven master tables, four
supplement/spec-z tables, and the eleven-row provenance registry.

---

## Files

| File | Description |
|------|-------------|
| `load_dictionary.py` | Builds and validates the ETL v2 structural and semantic dictionary from configured v1.1 source and evidence artifacts |
| `profile_values.py` | Profiles every native scalar/vector index, enriches the dictionary, and generates the sentinel candidate report without changing source values |
| `validate_dictionary_seal.py` | Resolves the configured Gate 3.4 dictionary and validates its formal README, fixed JSON/count contract, and narrow Git ignore exception without live profiling |
| `verify_source_fidelity.py` | Runs the read-only Gate 3.5 manifest/input preflight and exact seven-table standalone/master fidelity comparison with importable structured evidence |
| `generate_schema_v11.py` | Generates the ETL v2 `source` mirror DDL solely from the sealed dictionary and versioned provenance contract; `--check` rejects hand drift |
| `schema_v11.sql` | Generated-only Gate 3.6 DDL for eleven source mirrors plus the fixed provenance table; never edit this artifact directly |
| `verify_schema_v11_scratch.py` | Creates one random prefix-scoped scratch database, verifies catalogs/comments/constraints and mutations, and drops it in `finally` |
| `bootstrap_v11.py` | Performs the guarded, one-time Gate 3.7 master bootstrap and separate post-load verification for `cosmos2025_v11` |
| `load_supplements_v11.py` | Streams and verifies the four Gate 3.8 supplement/spec-z mirrors and supports source-free post-seal administration resume |
| `load_provenance_v11.py` | Registers and verifies the exact eleven-row Gate 3.9 dual-hash provenance set with phase-aware commit classification |
| `generate_conformance_v11.py` | Generates one explicit Gate 3.10 conformance case per sealed dictionary row; `--check` rejects artifact drift |
| `conformance_cases_v11.py` | Generated-only 1,416-case Python contract spanning every mirror column, comment, origin, type, and array check |
| `verify_conformance_v11.py` | Captures one batched catalog snapshot, validates every generated case and security boundary, and runs rollback-isolated scratch mutations |
| `reconciliation_core_v11.py` | Provides pure deterministic sampling, exact target-cast/IEEE canonicalization, and protected complete mismatch-ledger primitives for Gate 3.11 |
| `reconcile_values_v11.py` | Performs the one-pass, source-fresh Gate 3.11 value reconciliation against one read-only PostgreSQL snapshot and runs its disposable full-pipeline proof |
| `generate_schema_docs_v11.py` | Generates and byte-checks the Gate 3.12 schema reference from the sealed dictionary plus one bounded read-only live catalog snapshot |
| `extract_catalog.py` | Main ETL script. Reads 8.4GB FITS (6 extensions), extracts 4 parquet files, loads into PostgreSQL via COPY FROM |
| `verify_catalog.py` | Post-ETL verification. Runs 13 check sections (row counts, sentinel residuals, unit validation, O1 readiness), writes Markdown + HTML reports with embedded charts |
| `create_schema.sql` | DDL for the `catalog` schema. Creates all 7 tables with correct column types, constraints, and indexes |
| `profile_master_catalog.py` | Diagnostic script. Profiles the master catalog FITS file structure (column counts, types, array shapes per extension) |

---

## Gate 3.6 DDL generation and scratch verification

Generate or reproduce-check the tracked SQL from the sealed dictionary:

```bash
python src/etl/generate_schema_v11.py
python src/etl/generate_schema_v11.py --check
```

Run the live disposable validation only with the corrected ML01 development
credential scope. The verifier refuses `cosmos2025`, `cosmos2025_v11`, and any
database name outside its configured random scratch prefix.

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/verify_schema_v11_scratch.py
```

The live verifier performs no load and creates no target database or role.

---

## Gate 3.7 persistent master bootstrap

The create/load mode is deliberately non-idempotent. It requires the fixed
database, analyst role, and ignored handoff to be absent, fingerprints the v1
baseline, checks PostgreSQL volume capacity, reruns source integrity, executes
the reviewed generated DDL, and loads only the seven master mirrors. Every
table is freshly size/SHA-pinned before FITS access and commits as one
transaction. A failure reverses only resources marked as created by that
process.

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/bootstrap_v11.py --create-load
```

Successful bootstrap leaves `cosmos2025_v11`, `cosmos2025_v11_ro`, and the
mode-0600 ignored handoff at `internal-files/cosmos2025-v11.env` for the
operator and later gates. It does not load supplements, spec-z, or provenance.
The administrator password and generated analyst password remain in memory or
the exact handoff only; neither appears in command arguments or output.

Rerun the separate verifier without attempting database or role creation:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/bootstrap_v11.py --verify-only
```

The verifier repeats catalog, count, source-row, injected-ID, array, sentinel,
owner, role, analyst-permission, handoff/Git, and v1 fingerprint checks. The
documented `ml01/prd` scope is stale for this rebuild; Gate 3.7 uses the
operator-corrected `ml01/dev` scope without changing Doppler.

For this run, all database operations authenticated as `clusteradmin_pg01`.
The permission matrix changed the effective PostgreSQL identity to
`cosmos2025_v11_ro` with session authorization, so privilege enforcement ran
as the analyst while the network transport remained the admin connection.
Direct analyst authentication from ML01 was not exercised. The operator
accepted this as nonblocking and requires a later SCRAM HBA rule for direct
`cosmos2025_v11_ro` access; neither this CLI nor the gate changed or reloaded
HBA policy.

Operational review also found that the gate's blanket cleanup behavior was too
broad for post-load verifier-code defects after all seven transactional table
loads had already passed. Repeated imports caused avoidable wall time and NVMe
I/O. The approved phase-aware lifecycle now removes an incomplete database only
before all seven load commits are sealed. A later admin/verifier failure retains
the database and revokes/drops only role/handoff artifacts created by that run.

Resume that exact incomplete-admin state without source FITS access or COPY:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/bootstrap_v11.py --finalize-admin
```

Finalization requires `cosmos2025_v11` present, the role and handoff absent,
and exact retained schema including 1,429 nullability entries and 192 canonical
constraint definitions, counts, source-row, ID/FK, owner, unloaded-table, and
v1 evidence. It refuses a missing/drifted target or an
existing role/handoff. It then runs the existing role, admin, analyst matrix,
default privilege, handoff, v1, and Git-secret pipeline with zero source reads
and zero COPY operations. Use `--verify-only` after successful finalization.

Interrupted handoff writes remove only the exact inode opened by that call,
and both lifecycle boundaries treat dangling symlinks as pre-existing
artifacts. Direct CLI failures preserve allowlisted lifecycle diagnostics but
reduce unexpected failures to exception class and SQLSTATE. Create/load also
executes the immutable DDL bytes returned by preflight identity review rather
than reopening the path after review.

---

## Gate 3.8 supplements and spec-z

The guarded load requires all four mirror tables and provenance to be empty,
freshly pins the configured inputs, and streams only the 54 native dictionary
fields. Each table commits independently. Provenance stays empty until Gate
3.9.

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/load_supplements_v11.py --load
```

The lifecycle seals after all four committed counts and pins validate.
Pre-seal failure truncates only this gate's preflight-zero cleanup candidates.
Post-seal administration or verifier failure retains all four tables and
revokes only SELECT grants proven absent before the run. Resume that exact
retained state without source reads, COPY, or TRUNCATE:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/load_supplements_v11.py --finalize-admin
```

Run the separate source-pinned, read-only verification after successful load
or finalization:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/load_supplements_v11.py --verify-only
```

Analyst checks use the operator-approved admin connection with session
authorization. Four supplement SELECTs and twenty-four per-table write/DDL/
grant denials extend the unchanged Gate 3.7 matrix. Direct analyst HBA access
from ML01 remains an operator infrastructure action and is not claimed.

---

## Gate 3.9 provenance registration

The non-idempotent load requires all eleven mirrors exact and
`source.provenance` empty. It freshly hashes every configured source against
the Gate 3.5 manifest, guards one stable manifest identity across declared-pin
reads, rechecks physical and live counts plus each table's single load
transaction `xmin`, and verifies schema, role, handoff, analyst ACLs, and v1
identity before one transaction:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/load_provenance_v11.py --load
```

That transaction applies the generated provenance-contract 1.0.1 COMMENT and
inserts exactly eleven rows. `load_timestamp` is the shared PostgreSQL
`transaction_timestamp()` of this provenance-registration transaction after
mirror verification; it is not a reconstructed historical table-load commit
time. Each note preserves the exact table-load `xmin` and states that the
actual commit timestamp is unavailable because `track_commit_timestamp` was
off. No extension was installed and no timestamp was approximated.

Precommit failure rolls back both COMMENT and rows. An ambiguous commit or
connection-close result reconnects and accepts only exact zero with an
authorized old/amended comment or exact eleven with the amended comment and
field-perfect rows. Postcommit verifier failure retains the eleven rows for
the separate read-only verification path; it never deletes or reloads mirror
data.

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/load_provenance_v11.py --verify-only
```

Analyst checks continue to use operator-approved clusteradmin session
authorization. Direct analyst network authentication remains unexercised and
the SCRAM HBA correction for ML01 remains an operator infrastructure action.

---

## Gate 3.10 dictionary-driven conformance

Regenerate or byte-check the explicit 1,416-case module from the sealed
dictionary:

```bash
python src/etl/generate_conformance_v11.py
python src/etl/generate_conformance_v11.py --check
```

Each generated case carries the exact table and column, canonical PostgreSQL
type, column origin, full evidence-separated generated comment, element count,
and the named dimension/cardinality CHECK for arrays. The split is 1,349
master-native, 22 supplement-native, 32 spec-z-native, and 13 metadata cases.

Run the persistent verifier read-only through the approved clusteradmin
transport:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/verify_conformance_v11.py --live
```

The verifier collects objects, 1,429 columns/comments, 192 exact constraints,
eleven provenance rows, and all table ACLs in five batched queries on one target
connection. It evaluates the 1,416 cases locally, then runs the existing master,
Gate 3.8, and provenance admin-session analyst matrices. Direct analyst network
authentication is not claimed; the pending ML01 HBA correction is unchanged.

The destructive detection proof is restricted to one random configured-prefix
scratch database:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/verify_conformance_v11.py --scratch-mutations
```

It executes byte-reviewed generated DDL, proves baseline conformance, alters one
comment and one type in separate transactions, requires the intended failures,
rolls both back, drops only its exact scratch database, and compares protected
database, role, v1, catalog, and handoff identity before and after. It never
writes to `cosmos2025_v11` or `cosmos2025`.

---

## Gate 3.11 source-fresh value reconciliation

`generate_conformance_v11.py` also emits the exact source family, configured
file, locator, source column/type, mask/NaN facts, and sealed source population
for every case. Regenerate or byte-check this tracked input exactly as in Gate
3.10.

The live reconciler is a read-only, single-use evidence command:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/reconcile_values_v11.py --live
```

It first hashes and manifest-pins the eleven configured artifacts without a
second record extraction. It then opens each source exactly once, checks full
source-key uniqueness, retains the lowest SHA-256-ranked 20,000 source
ordinals (or the complete smaller source), fetches every generated target
column in bounded batches, and compares exact target-cast tokens. Float4 and
float8 use IEEE bytes; FITS masks and NaNs alone become NULL; arrays retain
order, element NULLs, and exact cardinality. Success output contains no source
or database row values.

The current dictionary maps Toni `ID` to live `galaxy_groups.id` and
`(GALID, ID)` to live `galaxy_group_memberships.(galid, id)`. The historical
v1 wording `group_id` is preserved only as evidence and is never queried.

Every mismatch is written without truncation to the configured ignored
mode-0600 JSONL ledger, including zero-based array element indices and exact
fallback tuple locators. Unexpected failures print only allowlisted stage,
exception class, and SQLSTATE metadata. The disposable proof is separate:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/reconcile_values_v11.py --scratch-proof
```

It creates only one random configured-prefix database, exercises all 1,416
cases plus PostgreSQL float rounding, signed zero, infinities, FITS masks,
finite sentinels, integer edges, arrays, and eight intended mutations, then
drops the exact database. Both modes bracket every exit with protected target,
v1, role, handoff, count, and transaction-ID identity observations.

The persistent verification transport remains the operator-approved
clusteradmin session authorization. Direct analyst network authentication was
not exercised, and the ML01 analyst SCRAM HBA correction remains a pending
operator infrastructure action.

---

## Gate 3.12 generated schema reference

`generate_schema_docs_v11.py` renders `docs/reference/schema-v11.md` from all
1,416 sealed dictionary rows plus the fixed provenance contract. Its default
mode takes one bounded read-only PostgreSQL snapshot, verifies the live catalog
and row counts, writes atomically, and rereads the exact bytes. `--check`
compares generated bytes without writing. Neither mode reads the immutable
FITS or supplement sources.

---

## Gate 3.13 verification surface

`generate_verification_surface_v11.py` compiles the sealed dictionary,
generated contracts, manifest, cumulative Gate 3.5 through Gate 3.12 evidence,
and configured policy documents into
`docs/research/etl-v2-verification.md`. Default mode writes atomically;
`--check` is read-only and requires byte identity. Both modes report zero
source reads, zero database queries, and no persistent mutation. The generated
MetaMCP and T_A v2 disposition cells remain blank for the operator.

---

## Related

| Directory | Relationship |
|-----------|--------------|
| [src/](../) | Parent directory |
| [configs/](../../configs/) | `data_paths.yaml` provides input/output paths and DB connection config |
| [docs/verification-report.md](../../docs/verification-report.md) | Output of `verify_catalog.py` |
| [docs/reference/data-manifest-v1.1.md](../../docs/reference/data-manifest-v1.1.md) | Immutable source boundary validated before any fidelity comparison |
