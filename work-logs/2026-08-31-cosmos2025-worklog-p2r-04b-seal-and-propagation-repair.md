<!--
---
title: "Worklog: P2R-04b Seal Reconciliation and Propagation Repair"
description: "Re-seal the corrected gate 4.1 verifier, propagate corrected separation statistics into every artifact the defective number reached, repair the unmet A1.1 and A1.2 validations, reconcile the defect register, and close out P2R-04a"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
# --- Runtime Context (required) ---
agent: "cc"
runtime: "Claude Code"
runtime_version: ""
model: "claude-opus-5[1m]"
hostname: "ml01"
spec_ref: "spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04b-seal-and-propagation-repair.md"
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
  - "docs/research/specz-linkage-propagation-inventory.md"
  - "docs/research/specz-linkage-evidence.md"
---
-->

# Worklog: P2R-04b Seal Reconciliation and Propagation Repair

## Summary

| Attribute | Value |
|-----------|-------|
| Status | 🔄 in progress |
| Agent | cc / Claude Code / claude-opus-5[1m] |
| Hostname | ml01 |
| Spec | `2026-08-31-cosmos2025-spec-p2r-04b-seal-and-propagation-repair.md` |
| Branch | `task/4-specz-linkage-correction` |
| Starting branch | `task/4-specz-linkage-correction` |
| Base commit | `4f98e490a07ccd1ea16a147e6930b108a6ca24d1` |
| Duration | in progress |

Objective: re-seal the corrected gate 4.1 verifier together with the
artifacts it generates, propagate the corrected separation statistics into
every artifact the superseded number reached including the live column
comment, repair the unmet A1.1 and A1.2 validations by new commits,
reconcile the central defect register, and close out the dangling P2R-04a
unit as `partial`.

Outcome: in progress.

---

## 0. Preflight

`spec-startup` plus the spec's own startup prerequisites. Every check
agreed; no disagreement, so no stop before the first write.

Skill resolution: `spec-startup` and `spec-closeout` resolve from
`/opt/agents/repos/local-agent-skills/skills/`. The resolved `spec-closeout`
carries the ML01 identity (`astronomy-coding-bot <astronomy-coding-bot@radioastronomy.site>`
and `/opt/agents/repos/work-logs/work-registry.csv`), so this is the correct
estate.

Environment: shared venv active, `/opt/agents/venv/bin/python`, Python
3.12.3. Credentials resolve through `doppler run --project ml01 --config dev`
per `AGENTS.md` and `configs/data_paths.yaml`.

| Prerequisite | Prior | Observed | Agrees |
|---|---|---|---|
| Branch and tree | clean at `4f98e49` | `4f98e490a07ccd1ea16a147e6930b108a6ca24d1`, `git status --short` empty | Yes |
| `main` | `e65242a` | `e65242a7802422cc86ed47d96945e2a86e0b27a3`, also the merge base | Yes |
| Parent gate commits | ten, intact and linear | `6d30e24` through `04b42e1`, subjects `gate 4.1` to `gate 4.10` in order | Yes |
| A1 commits | four, intact and linear | `35e95de`, `f9feada`, `d45f068`, `4f98e49` | Yes |
| `source` relations | thirteen | thirteen | Yes |
| Row counts | 482,579 / 261,975 / 784,016 | `specz_compilation_all` 482,579; `specz_compilation_unique` 261,975; the seven master tables and `photometry_aper` 784,016 | Yes |
| Provenance rows | twelve | twelve; digest `b2d26832dcb2a5ea9ad08f409a9d5d36` | Yes |
| Source column comments | 1,461 | 1,461 | Yes |
| `spec/spec-defect-register.md` | present with SD-068 | present, SD-068 at line 1892, digest `ff4e1153540afcc929d8807a07a1b8fe7bd8ddd663a79473a103fd9cd370a066` | Yes |
| P2R-04 archive positions | both, byte-identical | central and repository copies, `cmp` clean, both `a3bbdcdb...` at 37,257 bytes | Yes |
| P2R-04a | active central queue, worklog `in-progress`, no registry row | present in the active queue; worklog status `in-progress`; registry holds one P2R-04 row (110) and no P2R-04a row | Yes |
| Remote branch | none | `git branch -r` lists `origin/main` and `origin/task/2a-provenance-closeout-amendment` only | Yes |

Views 0, materialized views 0, `analysis` schema absent.

**Deviation from the spec's stated database preference, recorded rather than
worked around.** The spec prefers `cosmos2025_v11_ro`. That role is refused
at connection time by `pg_hba.conf` for host 10.25.20.10, which is the
pending operator infrastructure action `AGENTS.md` already records. Every
read-only session in this unit therefore uses the admin identity with
`default_transaction_read_only=on` set in the connection options, which is
the fallback the spec names. Per-session identity is recorded at each gate.

**Archive-convention inconsistency, recorded for later triage, not
normalized here.** The repository archive `spec/2026-08/` carries two
filename conventions: P2R-01 through P2R-03 use a stripped form
(`spec-p2r-01-reentry-v11-inspection.md`), while P2R-04 uses the full central
filename (`2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md`).
Renaming an archived record is an edit to a closed artifact. P2R-04a and
P2R-04b archive under the full central filename, matching P2R-04.

---

## 0.1 Execution-order deviation, declared

**The spec's execution order strands its own seal. Gates A2.4 and A2.5 are
executed before A2.2 and A2.3. No deliverable moves between gates.**

The spec's Execution Order runs A2.2 (re-seal and regenerate) and A2.3 (apply
the corrected database comments) before A2.5 (restore the catalog contiguity
and order guard). Gate A2.5 changes `src/etl/verify_specz_linkage_v11.py`.
That file's SHA-256 *is* the value
`EXPECTED_SEMANTIC_HASHES["specz_linkage_gate41"]` pins, and it is also the
`semantic_note_source_sha256` carried by the dictionary row, the generated
DDL, the conformance case, the schema reference, and the live column comment.

Executing in the stated order therefore produces exactly the failure this
unit exists to repair:

1. A2.2 seals bytes that A2.5 is about to change, so the seal asserts a
   provenance that stops being true three gates later, and the suite goes red
   again at A2.5 with no gate left to fix it.
2. A2.3 writes a database comment carrying a digest that A2.5 invalidates,
   and A2.3's own constraint ("a separately opened writable session at gate
   A2.3 only") makes a second comment application illegal. The live column
   comment would be left stale by this unit's own hand, which is defect 3 of
   "Why This Exists" reproduced rather than repaired.

The spec's constraints resolve this rather than permitting it: "The seal and
the regeneration move together. Updating the digest without regenerating
asserts a provenance that never existed. Either both or neither." The only
order in which that constraint and every gate validation can all hold is one
where the verifier reaches its final bytes before the seal is pinned.

What was chosen, and what was not:

- **Chosen:** run the gates as `A2.1, A2.4, A2.5, A2.2, A2.3, A2.6, A2.7,
  A2.8`. Every gate keeps its own deliverable, its own validations, and its
  own commit naming its own `A2.n` number. Git history is therefore
  non-monotonic in gate number, deliberately and visibly.
- **Rejected:** folding the guard restoration into A2.2. That would move a
  deliverable between gates and would put the A1.2 repair in a commit whose
  message does not name gate A1.2, breaking an A2.5 validation.
- **Rejected:** running the stated order and re-sealing again at A2.5. That
  costs a second full profiling pass and still leaves the database comment
  stale, because the single-write-session constraint forbids re-applying it.

Execution order is not in the spec's "Frozen" list, which covers the seal
being updated rather than bypassed, regeneration and re-seal sharing a gate,
the inventory-bounded diff, the enumerated column set and comment-contract
path, SD-068 being corrected rather than deleted, re-derived classifications,
earlier-gate repairs being new commits, P2R-04a closing `partial`, the
archive precedence, and the inherited prohibitions. Every one of those holds
under this order.

This is recorded as an authoring defect against P2R-04b at gate A2.6.

---

## 1. Gate checkpoints

### Gate A2.1: Map the propagation

Deliverable: `docs/research/specz-linkage-propagation-inventory.md`. No
pre-existing file and no database object changed.

Search covered both surfaces exhaustively. The repository tree was searched
with `git grep` once per superseded value in comma-grouped and bare forms,
plus phrase searches on the semantic note, the phrase "field-scale", and the
sealed verifier digest. `pg_description` was read in full under schema
`source` in one read-only session and searched for the same tokens. Both
methods, with their exact commands, are recorded in the inventory §2.

Result: twelve occurrences across seven artifacts, and nine recorded
negative searches. Ten occurrences are the repository chain from the two
authored edits in `src/etl/load_dictionary.py` through the four generated
artifacts. One is the live column comment on
`source.photometry_primary.id_specz_khostovan25`. One is SD-068 in the
central defect register.

The enumerated database column set is exactly one column, prior comment
SHA-256 `2fd8394b6397c0b4321e5a3dc0ffd4d340f91696f8d58832a8ba5ec8e5132e18`,
2,114 bytes, of which two of ten lines change. The enumerated dictionary row
set is exactly one row, `photometry_primary.id_specz_khostovan25`, of which
exactly two fields change: `semantic_note` and `semantic_note_source_sha256`.
Row count stays at 1,448.

Four artifacts are closed records and are inventoried out of scope with a
stated reason: the P2R-04 worklog at four locations, and the archived parent
spec at both positions. A superseded number inside a sealed historical record
stays.

Fresh evidence run of the corrected gate 4.1 verifier, read-only:

```bash
doppler run --project ml01 --config dev -- \
  /opt/agents/venv/bin/python src/etl/verify_specz_linkage_v11.py
```

Result: both manifest pins matched SHA-256 and byte count; all 20 prior
checks agreed, 0 disagreements; all-links geometry n=37,219, min 0.00489569,
median 4054.34155589, p90 5956.72268231, p99 7219.43263425, max
9085.01889381 arcsec; independent cross-check median 4054.341555895 arcsec,
1.44e-09 arcsec from the primary route; the untouched compilation-crossmatch
control retained n=92,359, median 0.08404811, max 0.99833504 arcsec. Runtime
2.5 s.

Database session for both the verifier and the `pg_description` capture:
database `cosmos2025_v11`, current user and session user
`clusteradmin_pg01`, `default_transaction_read_only=on` and
`transaction_read_only=on`, enforced at connection time through the
connection `options` string. Zero database objects created, altered, or
dropped; zero rows written. Statement classes issued: `SELECT` only.

`pg_description` capture: 1,461 column comments, manifest digest
`f4f4892fb07bceb4581304d7663bb47867760827b12f0840db319aea301e7c2e`, written
to the gitignored `staging/a21-pg-description-capture.json` as the gate A2.3
reversal pre-image.

Preflight confirmation the spec asked for: the comment contract helper is
`column_comment_contract()` in `src/etl/generate_schema_v11.py` at line 405.
The spec's expected name is correct.

Scope reading recorded at inventory §3.1: the Modify restriction on
`src/etl/load_dictionary.py` to "the `specz_linkage_gate41` seal entry" is
read as covering the seal constant and the semantic-note literal that seal
binds, because gate A2.2's own validation requires corrected statistics in
the regenerated semantic notes, which no regeneration can produce while the
literal is frozen. No other line of that module changes.

Gate diff, asserted against `4f98e49`: `git diff --stat 4f98e49` lists
exactly two paths, `docs/research/specz-linkage-propagation-inventory.md` and
this worklog, both additions, and no other path. An exact insertion count is
not recorded here for the same reason a commit cannot contain its own SHA:
this file's own line count is part of the number.

### Gate A2.4: Repair the A1.1 test discriminators

Repairs gate A1.1 of P2R-04a in a new commit. `35e95de` is not rewritten.

A1.1 required the D1 test to assert direct association rather than a number,
and the D2 tests to derive the observed categories and independently count
the fixture. Neither held at `4f98e49`: D1 ultimately asserted
`geometry.defective_path.median == 0.0`, and D2 hardcoded bucket literals and
compared `bucket_sum`, `attached_entry_total`, and `independent_entry_count`
against each other, three fields the generator computes from one
intermediate and sets equal by construction.

**D1 now asserts association.** The tests call the real production pairing
`verify.pair_catalog_link_carriers` and render its output as a link-value to
catalog-identifier map, then compare it against a mapping derived from the
fixture by a plain Python loop that shares no code with the pairing. The
fixture's catalog identifiers are unordered and non-contiguous, link value 20
collides with catalog identifier 20, and link value 21 matches no catalog
identifier at all: the collision catches a pairing that selects by
identifier, the absence catches one that silently drops what it cannot
address that way. No D1 assertion is written against a distance.

**D2 now derives its expectations.** `expected_attached()` recomputes the
resolution rule, the bucket split, and the entry counts from the fixture
tuples. Every equality in `check_rendered_distribution()` has one side from
the fixture reduction and one from the generator. The only assertions without
a fixture side are `reconciled is True` and a non-empty `population_scope`,
neither of which is a comparison between two generator values.

**Both families carry negative controls in the suite itself**, so the
assertions are shown to be capable of failing rather than merely passing.

Discriminator proof. Each case reverts one property in the production code
and runs the real repaired test, requiring RED:

| Mutation | Result | Failure text |
|---|---|---|
| Production pairing reverted to index arithmetic | RED | `link 20 paired with catalog source 20 (row 2, ra=10.0) but is carried by catalog source 10 (row 1, ra=0.0); link 21 paired with no catalog source but is carried by catalog source 30 (row 0, ra=30.0)` |
| Production pairing made position-dependent | RED | `link 20 paired with catalog source 30 (row 0, ra=30.0) but is carried by catalog source 10 (row 1, ra=0.0); link 21 paired with catalog source 10 (row 1, ra=0.0) but is carried by catalog source 30 (row 0, ra=30.0)` |
| Same, against the permuted-catalog fixture | RED | `link 20 paired with catalog source 30 (row 3, ra=30.0) but is carried by catalog source 10 (row 2, ra=0.0); link 21 paired with catalog source 10 (row 2, ra=0.0) but is carried by catalog source 30 (row 3, ra=30.0)` |
| Unmutated production pairing (control) | GREEN | passes as required |
| Generator drops confidence category 85 | RED | `rendered distribution dropped categories ['85']` |
| Generator perturbs a stated total | RED | `stated attached_entry_total 4 is not the fixture population 3` |

Five of five mutations discriminate, and every D1 failure names the link
value and both candidate catalog sources without reporting a separation. The
proof harness is `scratchpad/a24_mutation_demo.py`, run outside the
repository and not committed.

Focused suite:

```bash
/opt/agents/venv/bin/python -m pytest \
  tests/test_specz_linkage_evidence_regressions.py -q
```

Result: `11 passed in 0.44s`, up from 7.

Established suite at this gate:

```bash
/opt/agents/venv/bin/python -m pytest -q \
  -k 'not test_default_check_reproduces_tracked_dictionary_byte_identical'
```

Result: `4 failed, 440 passed, 1 deselected, 8 errors in 124.67s`. The
failure and error set is byte-identical to the startup baseline recorded
before any edit (`4 failed, 436 passed, 1 deselected, 8 errors in 124.88s`);
all twelve still halt at `src/etl/load_dictionary.py:712` on the stale
`specz_linkage_gate41` seal, which gate A2.2 repairs. The four additional
passes are this gate's net new tests. No new failure was introduced.

`35e95de`, `f9feada`, `d45f068`, and `4f98e49` are unchanged, verified by
subject and tree digest: `15d87463`, `b26d87a7`, `6a3f497c`, `8748829c`.

Files changed: `tests/test_specz_linkage_evidence_regressions.py` and this
worklog. No generator, no database object, and no other tracked file changed
at this gate.

---

## 2. Files Changed

| File | Change |
|------|--------|
| [docs/research/specz-linkage-propagation-inventory.md](../docs/research/specz-linkage-propagation-inventory.md) | Created (gate A2.1) |
| [work-logs/2026-08-31-cosmos2025-worklog-p2r-04b-seal-and-propagation-repair.md](2026-08-31-cosmos2025-worklog-p2r-04b-seal-and-propagation-repair.md) | Created (gate A2.1) |
| [tests/test_specz_linkage_evidence_regressions.py](../tests/test_specz_linkage_evidence_regressions.py) | Updated (gate A2.4, repairs gate A1.1) |

---

## 3. Issues Encountered

| Issue | Resolution |
|-------|------------|
| `cosmos2025_v11_ro` refused by `pg_hba.conf` from ML01 | Recorded, not worked around. Fell back to the spec's named alternative: admin identity with `default_transaction_read_only=on` at connection time. The HBA gap is a pending operator action already recorded in `AGENTS.md`. |
| Repository spec archive carries two filename conventions | Recorded for later triage per the spec's Archive Precedence section. Not normalized: renaming an archived record edits a closed artifact. |
| P2R-04b's execution order seals and propagates bytes that its own gate A2.5 changes | Gates A2.4 and A2.5 executed before A2.2 and A2.3. No deliverable moved between gates. Reasoning in §0.1; recorded as an authoring defect at A2.6. |

---

## 4. Next Steps

In progress. Gates A2.2 through A2.8 remain.
