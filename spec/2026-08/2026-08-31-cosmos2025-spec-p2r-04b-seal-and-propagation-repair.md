<!--
---
title: "Phase 2 Restart Unit 4b: Seal Reconciliation and Propagation Repair"
description: "Re-seal the corrected gate 4.1 verifier, propagate the corrected separation statistics into the database comments they reached, repair the unmet A1.1 and A1.2 validations, reconcile the defect register, and close out the blocked P2R-04a unit"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.1"
status: "Active"
amends: "spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md"
tags:
  - type: specification
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
  - tech: python
  - tech: postgresql
---
-->

# Spec P2R-04b: Seal Reconciliation and Propagation Repair

**Second amendment to P2R-04.** Gates: A2.1 through A2.8.

Parent: `spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md`, archived, write-once.

Preceding amendment: P2R-04a, which reached gate A1.4 and blocked at A1.5 on a contradiction it could not legally resolve. Its four commits `35e95de`, `f9feada`, `d45f068`, `4f98e49` stand and are not rewritten. Its audit is at `.superpowers/sdd/2026-08-31-cosmos2025-spec-p2r-04a-evidence-layer-correction/task-5-report.md`. **P2R-04a is an unclosed unit and this spec closes it out at gate A2.7**; that is not a reopening of a closed record but the completion of one that never closed.

**All defects this unit repairs are the spec author's.** P2R-04a required an outcome whose precondition it forbade, locked a register it had not read, scoped a correction to a layer the defective output had already left, and left no legal repair path for an earlier gate's unmet validation. The executor blocked correctly rather than forcing a green closeout, and self-reported its own unmet validations. Both are what the process wants.

**Mode: repo-mode work dispatched from the central queue.** Target `/opt/agents/repos/cosmos2025-anomalies`. The repository's `AGENTS.md` "Executing a Work Spec" section is the procedure and governs where its terms and the lifecycle skills differ; see Archive Precedence below.

**Branch: `task/4-specz-linkage-correction`.** It exists, is unmerged, and continues to carry the amendment chain. Additive commits only. No rewrite, rebase, squash, or amend of any commit from `e65242a` forward.

**There is no remote branch and no pull request.** No `origin/task/4-specz-linkage-correction` ref exists. The executor performs no remote operation of any kind, asserts nothing about remote or PR state, and hands the branch to the operator, who owns push, PR creation, and merge. Any startup check that would require observing remote state is out of scope by construction.

**Startup prerequisites.** Branch clean at `4f98e49`. `main` at `e65242a`. The ten parent gate commits and four A1 commits intact and linear. `cosmos2025_v11.source` at thirteen relations, 482,579 / 261,975 / 784,016 rows, twelve provenance rows, 1,461 source column comments. `spec/spec-defect-register.md` present with SD-068. P2R-04 present at both archive positions and byte-identical between them. P2R-04a present in the active central queue with its worklog `in-progress` and no registry row. A disagreement on any of these stops before the first write.

---

## Objective

At completion the established test suite passes, including the byte-identity dictionary check. `EXPECTED_SEMANTIC_HASHES["specz_linkage_gate41"]` names the corrected verifier, and the tracked dictionary and every generated artifact are consistent with the code that produced them. Every artifact that carried a superseded separation statistic carries the corrected one, including the database column comments the defective number reached. The A1.1 test discriminators assert what A1.1 required, and every catalog-indexing path carries the contiguity guard. The defect register records the new authoring defects with re-derived classifications and no longer asserts a disproved claim in SD-068. P2R-04a is closed out as a `partial` unit with its own worklog seal, registry row, and archive.

The branch is then a clean local history the operator can review, push, and merge as one PR carrying P2R-04, P2R-04a, and P2R-04b.

---

## Why This Exists

### Defect 1: a required outcome whose precondition was forbidden

`src/etl/load_dictionary.py` pins the SHA-256 of `src/etl/verify_specz_linkage_v11.py` in `EXPECTED_SEMANTIC_HASHES["specz_linkage_gate41"]`, and `_semantic_source_context()` rejects a changed source before dictionary profiling or generation.

P2R-04a gate A1.2 required changing that verifier. Gate A1.5 required the full suite green. Its Modify list excluded the dictionary loader and its do-not-touch list froze parent gates 4.2 through 4.6 and their outputs. Four failures and eight errors stop at `load_dictionary.py:712`, expected `46a7b827…` against observed `2db4890d…`. There was no legal move.

**The repair is to re-seal, not to add a fallback.** The P2R-04a report proposes a pinned historical binding analogous to the P2R-03 evidence provider. That is the wrong instrument. The P2R-03 provider pins a historical surface that must not change; the gate 4.1 evidence is current and was wrong, and pinning its old bytes would make the defect permanent and reproducible. The seal binds generated artifacts to the code that produced them, so the designed operation when a generator is corrected is regenerate-and-re-seal.

Re-sealing without regenerating would be a lie in the same shape as the defect: the seal would assert the tracked dictionary came from code that never produced it. The two move in one gate, with the diff bounded in advance.

### Defect 2: a register locked without being read

P2R-04a validated that `spec/spec-defect-register.md` is unchanged, written without opening the file. SD-068 is in it, attributed to the spec author, asserting the 4,054 arcsec prior "did not reproduce on any recoverable basis" and citing 4,467.3, 4,300.4, and 1,351.6 as the bases tried. All three came out of the defective pairing code. The row is an artifact of the bug it was written to excuse.

### Defect 3: the correction was scoped to a layer the defective output had already left

`source.photometry_primary.id_specz_khostovan25` carries a column comment reading "field-scale median separation of 4,467.3 arcsec." That number is wrong, it is in the sealed mirror, and it is the artifact most likely to be read by someone who never opens the review surface.

P2R-04a was scoped evidence-layer-only with structurally read-only sessions and zero write authority, and that scoping was hardened in review. The defective number had already propagated through the dictionary into the database at P2R-04. The read-only posture that looked like discipline is what guaranteed the wrong number stayed in the mirror.

**A correction is scoped by where the defective output went, not by where the defect was found.** Tracing that is a gate, not an assumption, which is why A2.1 runs first.

### Defect 4: no legal repair for an earlier gate's unmet validation

P2R-04a required additive commits with no rewrite and, separately, per-gate validations. Its own A1.5 review found three earlier validations unmet: the D1 test ultimately asserts only a median, which A1.1 explicitly forbade; the D2 tests hardcode buckets and compare generator self-fields rather than deriving and independently counting the fixture; and A1.2 removed the catalog contiguity and order guard while an unchanged compilation control path still direct-indexes catalog arrays. `tests/README.md` was also left without the new regression suite.

The executor had no legal move, because repairing them meant rewriting sealed gate commits. An earlier gate's unmet validation is repaired by a **new** commit naming the gate it repairs. This unit says so and does it.

The guard item is not cosmetic. A control path that direct-indexes catalog arrays without the contiguity guard is the same latent-error class this amendment chain exists to correct.

---

## Constraints Withdrawn From P2R-04a

| Withdrawn | Why it was wrong |
|---|---|
| Every database object frozen; zero write authority; sessions structurally read-only | The defective statistic had already reached a column comment. Freezing the database froze the defect in the artifact most likely to be read as fact. Write authority is restored **narrowly**: comment application only, on columns enumerated at A2.1, through the comment contract. |
| `spec/spec-defect-register.md` is unchanged | Asserted without reading the file. SD-068 records a claim this unit disproves, and new authoring defects are owed. |
| The dictionary loader is outside Modify; parent gate 4.2–4.6 outputs are frozen | The seal lives in the loader and binds the file A1.2 was required to change. Lifted **only** for the `specz_linkage_gate41` entry, the dictionary rows enumerated at A2.1, and the artifacts regenerated from them. |
| Additive commits only, with no stated path for an unmet earlier validation | Correct as a history rule, incomplete as a recovery rule. An earlier gate's unmet validation is repaired by a new commit whose message names the gate it repairs. History is never rewritten. |
| P2R-04a's worklog and registry row are untouched | Correct for a *closed* unit. P2R-04a never closed. Leaving it dangling makes the queue and registry unable to say what is owed, which is the failure the amendment convention exists to prevent. A2.7 closes it as `partial`. |

Everything else in P2R-04 and P2R-04a stands, including the prohibitions on inferred linkage, promoting demoted measurements, applying confidence thresholds, and creating the `analysis` schema, any view, any materialized join, or any selection rule.

---

## Archive Precedence

`spec-closeout` archives a central-queue spec into `/opt/agents/repos/spec/YYYY-MM/`. The repository `AGENTS.md` says completed central specs archive to the repository `spec/YYYY-MM/` index. These read as a conflict; observed practice resolves it, and both are satisfied.

P2R-04 currently exists at both `/opt/agents/repos/spec/2026-08/` and `cosmos2025-anomalies/spec/2026-08/`, byte-identical at 37,257 bytes. That is the contract this unit follows and states as a frozen decision:

- The **central** month folder holds the authoritative archive; the `spec-closeout` move puts it there and the attestation `Spec:` trailer names that path.
- The **repository** `spec/YYYY-MM/` holds a byte-identical index copy, committed as part of the authorized closeout, per `AGENTS.md`.
- The two must be byte-identical, proven by `cmp`, not by inspection.

The repository archive currently carries two filename conventions: P2R-01 through P2R-03 use a stripped form, P2R-04 uses the full central filename. Do not normalize either; renaming an archived record is an edit to a closed artifact. Record the inconsistency in the worklog for later triage.

---

## Execution Environment

Deltas only. The Doppler project and config are read from `AGENTS.md` and `configs/data_paths.yaml` at startup; this spec names neither.

| Item | Value |
|------|-------|
| Agent runtime | Claude Code |
| Executor requirement | `box-required`. Reads pinned FITS and the live mirror on ML01. |
| Seat | Must not be the occupant that executed P2R-04 or P2R-04a. |
| Reasoning effort | High on A2.1 and A2.2. Standard elsewhere. |
| Runtime budget | A2.2 runs `test_default_check_reproduces_tracked_dictionary_byte_identical`, roughly 34 minutes. It is not a hang. Budget for it; do not deselect it. |

Claude Code has full filesystem access unless a rule constrains it, so the Do-not-touch list is load-bearing rather than advisory. Read it before the first write.

### Database access

Read-only for all evidence and verification work, enforced at connection time: prefer `cosmos2025_v11_ro`, otherwise the admin identity with `default_transaction_read_only = on` in the connection options.

Write authority is a **separate, explicitly opened session at gate A2.3 only**, issuing `COMMENT ON COLUMN` statements on the columns enumerated at A2.1 and no other statement of any kind. Record the identity, the enforcement mechanism, and the exact statement list per session in the worklog.

**The generator CLI writes or checks the complete schema DDL, including `CREATE SCHEMA` and `CREATE TABLE`.** A2.3 must generate only the enumerated comment statements through the column comment contract helper in the schema generator (expected entry point `column_comment_contract()`; confirm its actual name at preflight) and execute only those statements. Applying `schema_v11.sql`, invoking the bootstrap path, or running the generator's write mode against the live database is prohibited and would be a destructive action against a sealed mirror.

---

## Reversal

| Effect | Class | The undo |
|---|---|---|
| Loader seal constant, tracked dictionary, generated artifacts, tests, docs, repository archive copy | `repo` | Drop the amendment commits. |
| Database column comments | `data-mutation`, derived layer | Regenerate from the pre-change dictionary and re-apply. A2.1 captures prior comment text and digest, so this is a replay, not a reconstruction. |
| `spec/spec-defect-register.md` and the central spec archive | `platform-state` | The central spec tree is **not a git repository**, so there is no commit to drop. Capture a pre-image copy and digest of the register before editing, retain it on the recycle surface per `spec-closeout`, and restore from it. Never delete. |
| Central work-registry rows | `platform-state` | Same: pre-image and digest before append, restore from pre-image. |

No effect falls into the `provenance` or `publication` classes. `source.provenance` rows are untouched, the manifest is not re-pinned, and the gate 4.5 load seal stands.

**Destructive-retry budget: zero.** No table is dropped, reloaded, renamed, or truncated. If a repair appears to require one, that is the finding: stop and signal at `staging/BLOCKED-p2r-04.md`.

---

## Scope

### Modify

- `src/etl/load_dictionary.py`, restricted to the `specz_linkage_gate41` seal entry
- `data/dictionary/columns-v11.csv`, restricted to the rows enumerated at A2.1
- Artifacts regenerating from those rows: `src/etl/schema_v11.sql`, conformance cases, `docs/reference/schema-v11.md`
- `src/etl/verify_specz_linkage_v11.py` and `src/etl/characterize_specz_linkage_v11.py`, for the guard restoration only
- `tests/`, `tests/README.md`
- `docs/research/specz-linkage-evidence.md`, for statistics superseded by A2.1 and the broken parent-spec link
- `docs/research/specz-linkage-propagation-inventory.md` (new, the A2.1 deliverable)
- `spec/spec-defect-register.md` (central)
- `work-logs/2026-08-31-cosmos2025-worklog-p2r-04a-evidence-layer-correction.md`, for the A2.7 `partial` seal only
- `work-logs/2026-08-31-cosmos2025-worklog-p2r-04b-seal-and-propagation-repair.md` (new, this unit's own)
- Central registry rows: one for P2R-04a, one for this unit
- Database column comments on the columns enumerated at A2.1
- The P2R-04a spec's archive move, and this spec's, at their respective closeouts
- Repository `spec/2026-08/` index copies for P2R-04a and this spec
- Interior READMEs and indexes the docs pass makes stale

### Do not touch

The parent's and P2R-04a's do-not-touch lists remain in force except where withdrawn. This unit adds:

- **Loaded data.** No table dropped, reloaded, renamed, truncated, inserted into, updated, or deleted from. Comments only.
- **`source.provenance`**, the manifest, and the pinned checkouts. Read and hash only.
- **`schema_v11.sql` applied to the live database, and the bootstrap path.** Generation only.
- **The P2R-03 pinned evidence provider and the F-07 regeneration architecture.** Reserved for their own unit.
- **Any commit's history from `e65242a` forward.** No rewrite, rebase, squash, amend, or force.
- **Remote git state.** No fetch, push, PR, or any operation requiring the network.
- **The archived P2R-04 spec, its worklog, and its registry row.** Closed and final.
- **P2R-04a's four commits and its A1.1–A1.4 content**, except through the additive repairs at A2.4 and A2.5.
- **Archived spec filenames.** Do not normalize the repository archive's mixed conventions.
- **Findings F-02, F-04, F-05, F-07, F-09, F-11, F-12, F-13**, byte-unchanged.

---

## Deliverables

One additive commit per gate, referencing its gate number, with a worklog checkpoint.

### Deliverable 1: Map the propagation (gate A2.1)

Trace every artifact carrying a separation statistic produced by the defective pairing code, and enumerate it in `docs/research/specz-linkage-propagation-inventory.md`. **No pre-existing file and no database object is modified at this gate**; the commit carries the new inventory document and the worklog checkpoint.

Search the repository tree and `pg_description` for the superseded values (4,467.3, 4,300.4, 1,351.6, 45.59, 8,727.4) and for any other statistic the corrected A1.2 computation supersedes. Cover at minimum the dictionary's semantic-note fields, generated DDL and comments, the live database comments, `docs/reference/schema-v11.md`, the review surface, the P2R-04 worklog, and the central defect register.

For each occurrence record artifact, locator, current text, prior digest, and whether it is in scope. Closed records (the P2R-04 worklog, the archived parent spec) are inventoried and marked out of scope: a superseded number inside a sealed historical record stays, because the record is what was believed at the time.

**Validation:**

- [ ] Every occurrence of each superseded value is located with its locator, or the search is shown to return none for that value
- [ ] The inventory distinguishes in-scope artifacts from closed records with a stated reason for each
- [ ] The database columns whose comments will change are enumerated exactly, with prior text and digest captured for A2.3's reversal
- [ ] The dictionary rows that will change are enumerated exactly by row key
- [ ] The search method is recorded, reproducible, and covers both the repository tree and `pg_description`
- [ ] The only files added or changed are the inventory document and the worklog; `git diff --stat` against `4f98e49` shows no other path
- [ ] Zero database objects changed

### Deliverable 2: Re-seal and regenerate together (gate A2.2)

Update `EXPECTED_SEMANTIC_HASHES["specz_linkage_gate41"]` to the corrected verifier's digest, update the dictionary rows enumerated at A2.1, and regenerate every artifact deriving from them, in one gate. Separating the seal from the regeneration produces a seal asserting a false provenance.

The diff is bounded by A2.1's inventory. A regenerated artifact differing anywhere the inventory did not predict halts the gate; an unpredicted diff is evidence the inventory was incomplete.

**Validation:**

- [ ] Exactly one `EXPECTED_SEMANTIC_HASHES` entry changes, and its new value equals a freshly computed `sha256sum` of the corrected verifier
- [ ] The regenerated dictionary differs from the tracked copy only in rows enumerated at A2.1, asserted by row-level diff in both directions
- [ ] Regenerated DDL, conformance cases, and schema reference differ only where the changed rows require, asserted against A2.1's inventory
- [ ] Corrected statistics in the regenerated semantic notes name their population and coordinate basis
- [ ] `test_default_check_reproduces_tracked_dictionary_byte_identical` is run and passes against the newly tracked dictionary; it is not deselected
- [ ] The established suite passes with zero failures and zero errors, command and output recorded
- [ ] A mutation reverting the seal entry alone reproduces the `load_dictionary.py:712` rejection, proving the seal still discriminates
- [ ] No database object changed

### Deliverable 3: Propagate corrected comments to the database (gate A2.3)

Apply the regenerated comments to exactly the columns enumerated at A2.1, through the comment contract helper, in a separately opened writable session.

**Validation:**

- [ ] Only `COMMENT ON COLUMN` statements were issued; the full statement list is recorded in the worklog
- [ ] The statements were generated through the comment contract helper; `schema_v11.sql` was not applied and the bootstrap path was not invoked
- [ ] The set of columns whose comment changed equals A2.1's enumeration exactly, asserted in both directions
- [ ] Total source column comment count is unchanged at 1,461
- [ ] Every comment outside the enumeration is byte-unchanged, asserted by digest against A2.1's capture
- [ ] No superseded separation value remains in any `pg_description` row under `source`
- [ ] Relation list, per-table row counts, and the provenance digest equal their startup values
- [ ] `cosmos2025_v11_ro` can still select from every relation
- [ ] The writable session was opened for this gate only and closed at its end

### Deliverable 4: Repair the A1.1 test discriminators (gate A2.4)

A1.1 required the D1 test to assert direct association rather than a number, and the D2 tests to derive the observed categories and independently count the fixture. Neither holds at `4f98e49`. Repair both in a new commit whose message names gate A1.1 as the gate it repairs. Do not rewrite `35e95de`.

**Validation:**

- [ ] The D1 test fails when the pairing is reverted to index arithmetic, and the failure names the mismatched source rather than a numeric difference
- [ ] The D1 test passes under a permuted-catalog fixture and fails if the pairing is made position-dependent
- [ ] The D2 tests fail when a category is dropped from the rendered distribution and, separately, when a stated total is perturbed
- [ ] No D2 assertion compares two values both originating from the generator under test
- [ ] The commit message names gate A1.1 as the gate it repairs
- [ ] `35e95de`, `f9feada`, `d45f068`, `4f98e49` are unchanged

### Deliverable 5: Restore the contiguity guard and repair documentation (gate A2.5)

Restore the catalog contiguity and order guard on every path indexing a catalog array by position, including the compilation control, in a new commit naming gate A1.2. Direct indexing is sound only while `id` is contiguous and zero-based; an unguarded path is the same latent-error class this chain exists to correct.

**Validation:**

- [ ] Every catalog-array indexing site in both generators is enumerated, and each is guarded or converted to explicit lookup
- [ ] A test fails when the guard is removed and the catalog is presented non-contiguous
- [ ] The compilation-crossmatch control distribution is byte-unchanged, confirming the guard restored correctness without altering a correct result
- [ ] `tests/README.md` documents the amendment regression suite
- [ ] The review surface's parent-spec link resolves; the pre-existing depth error is corrected
- [ ] The commit message names gate A1.2 as the gate it repairs

### Deliverable 6: Reconcile the defect register (gate A2.6)

Capture a pre-image and digest of `spec/spec-defect-register.md` before editing, then follow the register's own entry procedure.

Correct SD-068. Its claim that the 4,054 arcsec prior did not reproduce on any recoverable basis is disproved: it reproduces to 4054.34 arcsec on the all-links population against `specz_compilation_all.ra_corrected`/`dec_corrected`, confirmed by two Astropy routes and one PostgreSQL route. The three bases it cites were all produced by the defective pairing code. Correct or supersede in place per the procedure; **do not delete it.** The record that the row was written, and why, is itself evidence.

Append the authoring defects from "Why This Exists". **Re-derive each classification from the register's current class table rather than accepting this spec's suggestions.** Note in particular that `required-path-missing-from-modify` already exists at four instances with the skill patch pending, and that defects 1 and 3 both plausibly belong to it, defect 1 arguably to `spec-internally-inconsistent` as well. Reconcile the class instance counts after appending. Where no existing class fits, record a vocabulary gap for operator triage rather than inventing one silently.

The executor-side items from P2R-04a's A1.5 review are **not** register rows; they belong in P2R-04a's worklog Issues section at A2.7.

**Validation:**

- [ ] A pre-image copy and digest of the register exist before the first edit and are retained per the recycle convention
- [ ] SD-068 is corrected or superseded in place with the reproducing evidence and its basis; it is not deleted
- [ ] Each new row carries class, date, repo, spec, found-by, attribution to the spec author, and the exact text the spec did or did not carry
- [ ] Every classification is re-derived against the current class table, with the reasoning recorded; no class is invented silently
- [ ] Class instance counts in the register's table are reconciled with the appended rows
- [ ] The skill's failure-mode table is unchanged unless a class newly reaches its promotion threshold, in which case the patch is recorded per the register's procedure

### Deliverable 7: Close out P2R-04a (gate A2.7)

P2R-04a blocked at A1.5 with four gates landed cleanly. Per the `spec-closeout` Blocked path it closes as `partial`, not `completed`.

Seal its worklog as `partial`, recording its four gate SHAs, its runtime facts, the blocking contradiction, the four executor-side issues its own review self-reported, and this unit as the remediation. Append its registry row with matching status. Archive its spec to the central month folder and commit the byte-identical repository index copy, per Archive Precedence.

Its four commits are not touched. Its content is not revised. This gate completes a record that was left open; it does not reopen a closed one.

**Validation:**

- [ ] P2R-04a's worklog status is `partial`, carrying its four exact gate SHAs and the blocking contradiction
- [ ] The four executor-side issues are recorded in its Issues section, attributed to executor deviation, and are absent from the defect register
- [ ] Exactly one P2R-04a registry row exists, status matching the worklog
- [ ] The P2R-04a spec is present in the central month folder and in the repository index, byte-identical by `cmp`, and absent from the active queue
- [ ] `35e95de`, `f9feada`, `d45f068`, `4f98e49` are unchanged
- [ ] The archived P2R-04 spec, worklog, and registry row are byte-unchanged

### Deliverable 8: Closeout (gate A2.8)

Run the current `spec-closeout` skill. This unit closes as a spec in its own right: its own worklog mirroring this spec's filename, its own registry row, its own archive to the central month folder with a byte-identical repository index copy, and its own attestation naming its central archived path.

**A commit cannot contain its own SHA.** Record exact SHAs for gates A2.1 through A2.7 in the worklog. Identify the A2.8 closeout commit relationally (the closeout commit on this branch, the tip at handoff) and record its resulting SHA afterward in the final handoff and in the ignored run report, not inside the commit it names.

**Validation:**

- [ ] Additive commits only on `task/4-specz-linkage-correction`; no rewritten history from `e65242a` forward
- [ ] No remote operation of any kind was performed, and no claim is made about remote or PR state
- [ ] One commit per gate, each referencing its `A2.n` number
- [ ] The established suite passes in full, including the byte-identity dictionary check, output recorded
- [ ] This unit's worklog exists at the mirrored filename, status `completed`, carrying exact SHAs for A2.1 through A2.7, a relational identification of A2.8, the per-session database identity and enforcement record, and the archive-convention inconsistency note
- [ ] The A2.8 SHA is recorded in the final handoff and the run report, and nowhere inside the commit itself
- [ ] One new registry row for this unit, distinct from P2R-04a's
- [ ] This spec is in the central month folder and the repository index, byte-identical by `cmp`, and absent from the active queue
- [ ] Final handoff states that the branch is a clean local history ready for operator review, push, and PR creation

---

## Human Approval Surface

The corrected `docs/research/specz-linkage-evidence.md`, with `docs/research/specz-linkage-propagation-inventory.md` and this unit's worklog.

Operator disposition authorizes push, PR creation, and merge of `task/4-specz-linkage-correction`, and unblocks the spec-z science surface unit.

---

## Constraints

Inherited constraints stand except where withdrawn. This unit adds:

- **The seal and the regeneration move together.** Updating the digest without regenerating asserts a provenance that never existed. Either both or neither.
- **Do not add a second pinned-bytes provider.** The P2R-03 provider pins a historical surface. This entry is current and was wrong; pinning old bytes makes the defect permanent.
- **A correction is scoped by where the output went, not where the defect was found.** A2.1 traces it. Do not begin repairs from an assumption about which layer is affected.
- **Write authority is one statement class, on an enumerated column set, in one gate, through the comment contract.** The generator's schema-write path is not a legal instrument here.
- **An earlier gate's unmet validation is repaired by a new commit naming it.** History is never rewritten to make a gate look like it passed the first time.
- **A regenerated artifact differing where the inventory did not predict halts the gate.**
- **Nothing asserts remote or PR state.** There is no remote branch. A validation that would require observing one is malformed.
- **A commit never contains its own SHA.** Closeout commits are identified relationally and their SHAs recorded afterward.

---

## What the Executor May Choose

Module decomposition, search strategy at A2.1, test organization and fixtures, guard implementation, inventory document structure, and worklog prose organization.

Frozen: that the seal is updated rather than bypassed; that regeneration and re-seal share a gate; that the diff is bounded by A2.1's inventory; the enumerated column set, the single write statement class, and the comment-contract path; that SD-068 is corrected rather than deleted; that classifications are re-derived rather than accepted from this spec; that earlier-gate repairs are new commits; that P2R-04a closes `partial`; the archive precedence; and every inherited prohibition not listed as withdrawn.

---

## Execution Order

1. Preflight per `spec-startup`, plus this spec's startup prerequisites
2. Gate A2.1 (map the propagation)
3. Gate A2.2 (re-seal and regenerate)
4. Gate A2.3 (propagate corrected comments to the database)
5. Gate A2.4 (repair the A1.1 test discriminators)
6. Gate A2.5 (restore the contiguity guard, documentation repairs)
7. Gate A2.6 (reconcile the defect register)
8. Gate A2.7 (close out P2R-04a as `partial`)
9. Gate A2.8 (closeout)

---

## Notes

**On closing P2R-04a from a different unit.** The amendment convention forbids re-sealing a *closed* parent's worklog, because that collapses two executions into one record. P2R-04a is not closed; it is dangling, with an `in-progress` worklog and no registry row, and a dangling unit makes the queue and registry unable to report what is owed. Its facts are fully recoverable from its four commits and its audit report. Closing it as `partial` from here is the smaller error than leaving it open, and it is named as an explicit operator decision rather than an executor judgement.

**On what the correction did not touch.** F-08's population-A result stands: every one of the 694 representatives names a different catalog source and none names the same one. Its coordinate-basis label was repaired inside A1.4. The corrected surface should not read as though the whole unit were in doubt.

**On the architecture this keeps deferring.** Three units have now been shaped by the F-07 seal mechanism, and the property is broader than first recorded: not only does each dictionary extension add a pinned fallback, but any correction to a sealed generator becomes a cross-cutting change touching the loader, the dictionary, the generated artifacts, and the database. The versioned-input-snapshot direction, where an artifact records its generator version plus the dictionary and evidence commit it was produced against, is overdue and remains explicitly out of scope here.
