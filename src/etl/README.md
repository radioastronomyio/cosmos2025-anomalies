<!--
---
title: "ETL Pipeline"
description: "COSMOS-Web catalog extraction, load-dictionary, and verification scripts"
author: "VintageDon"
date: "2026-04-05"
version: "1.9"
status: "Active"
tags:
  - type: directory-readme
  - domain: etl
---
-->

# ETL Pipeline

FITS-to-PostgreSQL pipeline for the COSMOS-Web DR1 master catalog. Phase 1 is complete — 784,016 sources loaded across 4 catalog tables plus 3 supplementary tables.

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

## Related

| Directory | Relationship |
|-----------|--------------|
| [src/](../) | Parent directory |
| [configs/](../../configs/) | `data_paths.yaml` provides input/output paths and DB connection config |
| [docs/verification-report.md](../../docs/verification-report.md) | Output of `verify_catalog.py` |
| [docs/reference/data-manifest-v1.1.md](../../docs/reference/data-manifest-v1.1.md) | Immutable source boundary validated before any fidelity comparison |
