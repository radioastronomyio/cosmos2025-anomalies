<!--
---
title: "Phase 2 Restart Unit 2: Manifest Re-pin and Readiness Review Amendment"
description: "Seal the v1.1 manifest and readiness-review provenance chain through exact baseline reconstruction, discriminating validation, and truthful lifecycle closeout"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.5"
status: "Active"
tags:
  - type: specification
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
  - tech: python
related_documents:
  - "../cosmos2025-anomalies/AGENTS.md"
  - "../cosmos2025-anomalies/docs/reference/data-manifest-v1.1.md"
  - "../cosmos2025-anomalies/docs/research/v11-readiness-review.md"
  - "2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md"
---
-->

# Spec P2R-02: Manifest Re-pin and Readiness Review Amendment

**Task 2 of the Phase 2 restart series.** Gates: 2.1 through 2.5.

Predecessor: P2R-01 (v1.1 structural inspection). Successor: P2R-03 (ETL v2 mirror), which **does not dispatch until this spec's approval surface is signed**.

**Mode: central-queue repo execution.** This file in `/opt/agents/repos/spec/` is the authorization; the target repository is `/opt/agents/repos/cosmos2025-anomalies`. Follow the target repository's "Executing a Work Spec" contract for branch, gate commits, and the repo-local worklog. The operator's standing central-queue rule overrides only `AGENTS.md`'s stale statement that the spec itself lives in-repo. Working branch: `task/2-manifest-amendment`.

**Startup prerequisite:** `main` in the target repository must contain P2R-01 closeout commit `cd0a8c0f7625836c7928ece4177a5ccce2dd3dfe`. If it does not, stop before branch creation. Do not branch from the still-open P2R-01 task branch and do not recreate its outputs.

---

## Objective

At completion, `docs/reference/data-manifest-v1.1.csv` records the true SHA-256 and byte size of all seven previously-unmaterialized LFS files, `data-manifest-v1.1.md` §2 describes their materialized state rather than their pointer state, and each re-pinned hash has been shown to equal the content hash the original pointer declared. Finding F6 in `docs/research/v11-readiness-review.md` is closed with that evidence rather than left open. The readiness review is reconciled with the subsequently approved lossless-mirror design and carries an empty operator confirmation table plus signature line. The executor prepares that approval surface but does not answer or sign it. Completion of this unit makes the surface reviewable; P2R-03 remains blocked until the operator fills it, signs it, and the signed review is present on `main`.

The unit changes no source data and loads nothing. It corrects the version-controlled provenance records and produces the surface on which the operator authorizes the rebuild.

---

## Why This Exists

Two reasons, and the first one is structural rather than clerical.

**Provenance has no undo.** Re-pinning a hashed manifest is one of two effect classes in the estate's reversal table with no declarable reversal, and the one whose damage is invisible: nothing breaks, and every artifact derived against the old pin silently becomes unreproducible. The skill governing this estate's specs states that such an effect may not share a work unit with anything else. This work therefore cannot be gate 1 of the rebuild. It is its own unit, and it is small on purpose.

**The current manifest will abort the rebuild by design.** `data-manifest-v1.1.md` §2 states that all seven LFS-pattern files in the speczcompilation checkout are unmaterialized pointer files of 133 to 134 bytes, and the CSV rows carry the hashes of those pointers. The operator has since installed git-lfs and materialized them; `specz_compilation_COSMOS_DR1.1_unique.fits` is 70,223,040 bytes on disk as of 2026-08-17T01:39Z. P2R-03 aborts any load whose source SHA-256 disagrees with the manifest, which is correct behaviour firing on a correct file. The manifest anticipated this and says the seven rows must be regenerated after materialization; that has not happened.

The same event closes readiness-review finding F6, which is written as OPEN and asks the operator to choose between materializing the checkout and supplying it by another channel. That choice has been made by action. A review surface that presents a resolved question as a live decision is worse than one that omits it.

Separately, the readiness review's Approval section reads as a requirement rather than a record: no signature, no date, no recorded answers. P2R-03 asserts that P2R-01 was approved on 2026-08-16. For a project whose stated constraint is that every claim traces to evidence including its own, the authorization is currently the one claim resting on nothing. This unit fixes that by producing the record, not by asserting it.

---

## Execution Environment

| Item | Value |
|------|-------|
| Executor requirement | `box-required`. Hashes local files under `/opt/agents/repos/reference-files/`. |
| Host | ML01 |
| Agent runtime | Operator's choice; nothing here is runtime-specific |
| Reasoning effort | Standard. This unit is mechanical; its risk is in scope discipline, not analysis. |
| Attended | The run does not pause. The operator reviews and signs the amended readiness review afterward; P2R-03 is gated on that signature. |
| Toolchain | Shared ML01 venv. `git-lfs` present (verify at preflight). |

---

## Scope

### Pre-existing (do not create)

- `/opt/agents/repos/reference-files/speczcompilation/`: materialized checkout, branch `main`, HEAD `1924f5d0ee6c221b820035c8d3cd7302c02532b0`, annotated tag `DR1.1` present.
- `docs/reference/data-manifest-v1.1.{csv,md}`: the artifacts this unit amends.
- `docs/research/v11-readiness-review.md`: the approval surface this unit amends.
- `src/inspection/build_data_manifest.py`: the P2R-01 manifest builder. Reuse it; do not rewrite it.

### Modify

- `docs/reference/data-manifest-v1.1.csv` (seven rows only)
- `docs/reference/data-manifest-v1.1.md` (§1 summary figures, §2 rewritten, amendment note)
- `docs/research/v11-readiness-review.md` (F6 closed, Approval section made a record)
- `work-logs/worklog-2026-08-16-manifest-amendment.md`
- `/opt/agents/repos/work-logs/work-registry.csv` (append one closeout row, category `astronomy`)
- This spec file, and its archive move at closeout
- Any interior README the docs pass makes stale

### Reference (consult, do not modify)

- `AGENTS.md`: branch, commit, and worklog conventions.
- `2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md`: the consumer of this unit's output. Read it to confirm the manifest fields P2R-03 validates against; do not execute any part of it.

### Do not touch

- **The 103 files under `/mnt/nvme01/cosmos-web-dr1-catalog` and their 103 manifest rows.** Nothing about the NVMe holdings changed. Re-hashing them is not harmless: it would replace a pin taken at a known time with one taken now, which is the invisible-damage case this unit exists to contain. Only the seven speczcompilation LFS rows are in scope.
- **The other 74 speczcompilation rows.** Non-LFS files in that checkout were hashed as real content in P2R-01 and are unchanged.
- **`git checkout`, `git pull`, or any operation that moves the speczcompilation HEAD.** The manifest pins a commit. Moving it invalidates the pin this unit is repairing.
- **The live `cosmos2025` database.** Untouched by this unit and by P2R-03.

---

## Deliverables

Gate discipline: each gate ends in one commit referencing its gate number, and a worklog checkpoint.

### Deliverable 1: Preflight and pointer-declaration capture (gate 2.1)

Before re-hashing, capture what the original pointers declared from the Git objects at pinned commit `1924f5d0ee6c221b820035c8d3cd7302c02532b0`. For each of the seven paths, read the pointer blob with `git show <pinned-commit>:<path>` (or an equivalent Git-LFS command that reads the committed pointer rather than the materialized worktree file), parse the complete 64-hex `oid sha256:` value and declared byte count, and record the seven pairs in the worklog. Manifest §2 identifies the paths and provides human-readable abbreviated OIDs; its abbreviated strings are not acceptance values. Confirm `git-lfs` is installed and the checkout is clean and at the pinned HEAD.

This is the step that makes gate 2.2 a discriminator instead of a photograph. Without the complete committed declaration, re-hashing a materialized file only proves that the file has a hash.

**Validation:**

- [ ] Seven expected (complete 64-hex SHA-256, byte count) pairs are recorded in the worklog and were parsed from pointer blobs at the pinned commit
- [ ] Each captured pointer blob passes the Git-LFS pointer format check; no abbreviated Markdown OID is used as an acceptance value
- [ ] `git lfs version` returns a version string
- [ ] `git status` in the checkout reports clean, and `git rev-parse HEAD` equals `1924f5d0ee6c221b820035c8d3cd7302c02532b0`
- [ ] All seven materialized paths exist and none is 133 or 134 bytes

### Deliverable 2: Re-hash and reconcile against the pointer declarations (gate 2.2)

Compute SHA-256 and byte size for the seven materialized files. For each, compare against the gate 2.1 baseline. The LFS oid is the SHA-256 of the file content, so agreement proves the materialized bytes are the bytes the pointer described, not merely that a file of plausible size arrived.

Any disagreement is a finding and stops the unit at this gate: it means the fetch delivered content other than what the pinned commit declared, which is a provenance failure the manifest must not absorb.

**Validation:**

- [ ] All seven computed SHA-256 values equal their gate 2.1 expected values
- [ ] All seven computed byte counts equal their gate 2.1 expected values
- [ ] `specz_compilation_COSMOS_DR1.1_unique.fits` reports exactly 70,223,040 bytes
- [ ] Any mismatch is recorded in the worklog with both values and halts the unit; it is not reconciled, defaulted, or averaged
- [ ] `astropy.io.fits.open` succeeds on both `_unique.fits` and `_all.fits`, and the row count of each is recorded in the worklog

### Deliverable 3: Manifest re-pin (gate 2.3)

Update the seven rows in `data-manifest-v1.1.csv` with the verified hashes, byte sizes, and current mtimes. Rewrite §2 of `data-manifest-v1.1.md` to describe the materialized state: what the files now are, the date of materialization, the pointer-versus-content reconciliation result from gate 2.2, and an explicit note that these seven rows were re-pinned on this date under this spec while the other 177 rows carry their original P2R-01 pin. Update the §1 total-bytes figure and any row-count statement the change invalidates.

Two facts belong in §2 that the current text does not carry, both of which will otherwise cause a downstream misreading:

- The checkout carries an annotated tag `DR1.1` dated 2025-10-31, and HEAD sits two commits past it. Record both, and record whether those two commits touch any LFS-tracked path. A tag is a stronger provenance anchor than a branch tip, and the reader needs to know which one the manifest pins.
- The data files are named `..._COSMOS_DR1.1_...`, which is the spectroscopic compilation's own release version and is unrelated to COSMOS-Web v1.1. State this. Two different "1.1" versions now appear on adjacent manifest rows.

**Validation:**

- [ ] Exactly seven CSV rows differ from the previous revision; `git diff --stat` on the CSV confirms no other row changed
- [ ] Every re-pinned CSV hash equals the corresponding gate 2.2 computed value
- [ ] §2 no longer asserts that any file is an unmaterialized pointer
- [ ] §1 total bytes for root 2 equals the sum of that root's CSV byte column, recomputed and shown
- [ ] The `DR1.1` tag, the HEAD offset from it, and whether the intervening commits touch LFS paths are all stated
- [ ] The DR1.1 naming distinction is stated explicitly
- [ ] Re-verification: three randomly chosen rows from the *unmodified* 177 are re-hashed and still match, demonstrating the amendment did not disturb the standing pin

### Deliverable 4: Readiness review amendment (gate 2.4)

Close F6 in `docs/research/v11-readiness-review.md`. The finding keeps its ID and original statement; append a `Resolution` block carrying the materialization date, the gate 2.2 reconciliation result, the live-side counts F6 already records (37,219 linked sources, 26,323 within the analysis sample), and the compilation-side row count from gate 2.2. F6's status changes from OPEN to CLOSED. Do not delete or rewrite the original finding text: the review is a record, and a finding that was open must remain legible as having been open.

Append resolution blocks—not rewritten history—to the findings and design question made stale by the approved mirror architecture:

- F1: all 204 GALIGHT-MORPHO source columns are in scope; no ML-MORPHO subset policy carries forward.
- F5: both primary photometry and SE++APER are loaded completely; vector-valued columns remain arrays in the source mirror.
- F7: superseded as an execution concern because `cosmos2025` remains untouched and `cosmos2025_v11` is built alongside it; no v1 schema drop or v1 archive is part of P2R-03.
- F9: AGN/DESI remains deferred because it is a separate 18-million-row reference product outside the declared catalog-mirror boundary, not because it lacks a current research consumer.
- Q1: the frozen mapping is all seven complete master extensions, three complete supplements, and the spec-z compilation, with no science-driven column projection.

Then convert the Approval section from a requirement into a record. It gets a table with one row per finding F1 through F9 and one per design question Q1 through Q4, each with a concise disposition summary and an empty operator-confirmation cell, plus a signature line with name and date. **The executor fills in the structure and disposition summaries but leaves confirmation cells empty.** It does not infer confirmation and does not sign. Recording an approval that did not happen is the failure this deliverable exists to prevent.

**Validation:**

- [ ] F6 carries a Resolution block with the materialization date and gate 2.2 result, and its status reads CLOSED
- [ ] F6's original finding text and original closed question are still present and unmodified
- [ ] F1, F5, F7, F9, and Q1 carry append-only resolution blocks matching the frozen architecture above
- [ ] The F9 resolution uses release-product boundary and scale as its rationale; it does not use absence of a current consumer
- [ ] The Approval section contains a table with 13 rows (F1–F9, Q1–Q4), disposition summaries, empty confirmation cells, and a signature line
- [ ] Every confirmation cell is empty and the signature line is unsigned
- [ ] No historical evidence paragraph is deleted or rewritten

### Deliverable 5: Closeout (gate 2.5)

Follow the target repository's "Executing a Work Spec" contract for repository changes. After the final repo commit, append the central registry row and move this central spec from the active queue to `/opt/agents/repos/spec/2026-08/`. The central registry and archive move are lifecycle records outside the target repo and are not added to its Git commit.

**Validation:**

- [ ] `main` contained P2R-01 closeout commit `cd0a8c0f7625836c7928ece4177a5ccce2dd3dfe` before this branch was created
- [ ] Branch `task/2-manifest-amendment`, no push, no remote operation
- [ ] One repo commit per gate, each referencing its gate number
- [ ] Worklog checkpointed per gate and sealed with per-gate commit SHAs
- [ ] One row appended to `/opt/agents/repos/work-logs/work-registry.csv`, category `astronomy`
- [ ] This central spec archived to `/opt/agents/repos/spec/2026-08/` and is absent from the active queue

---

## Human Approval Surface

`docs/research/v11-readiness-review.md`, as amended by gate 2.4.

After reviewing the completed branch, the operator fills the 13 confirmation cells and signs. The signed review must be integrated into `main`; that recorded signature is the authorization for P2R-03, and P2R-03 verifies it rather than asserting it.

---

## Constraints

- **Re-pin exactly seven rows.** The other 177 carry a pin taken 2026-08-16T03:32:50Z. Regenerating them wholesale would look like a no-op and would silently replace a known-time pin with a now-time pin, which is the class of damage this unit is structured to avoid. If the builder script cannot be run against a subset, extract the seven rows rather than regenerating the file.
- **A hash mismatch is a finding, not a problem to solve.** If any computed hash disagrees with its pointer declaration, stop at gate 2.2 and report. Do not re-fetch, do not reset, do not accept the on-disk value as authoritative. The pointer is the pinned commit's declaration of truth.
- **Do not populate the approval answers.** The executor builds the empty structure. An unattended agent that fills in "Yes" because the recommendation said yes has manufactured an operator decision.
- **Do not move HEAD.** No pull, fetch, checkout, or reset in the speczcompilation checkout. The manifest pins a commit; moving it invalidates the artifact being repaired.

---

## What the Executor May Choose

Chosen by the executor: how to extract and rewrite the seven CSV rows, whether to script it or edit directly, worklog prose organization, commit message wording beyond the gate reference.

Frozen by this spec: which rows change, the pointer-reconciliation check as the acceptance criterion, F6's resolution content, the shape of the approval table, and the prohibition on populating it.

---

## Execution Order

1. Gate 2.1 (preflight and pointer-declaration capture)
2. Gate 2.2 (re-hash and reconcile) — halts the unit on any mismatch
3. Gate 2.3 (manifest re-pin)
4. Gate 2.4 (readiness review amendment)
5. Gate 2.5 (closeout)

---

## Notes

**On why this is not folded into the rebuild.** It is roughly two hours of mechanical work and it would disappear into a fourteen-gate spec without anyone noticing. That is exactly the argument against doing so. The estate's reversal table lists provenance alongside publication as the two effects a reviewer waves through, neither of which has an undo. Isolating it means the diff that changes the project's provenance anchor is a diff a human can read in one sitting.

**On the `DR1.1` tag versus HEAD.** This unit records the discrepancy; it does not resolve it. Whether the manifest should pin the tag rather than the branch tip is an operator decision, and it is worth making before the compilation issues its next periodic release. It is noted here so the question exists in the record rather than being rediscovered later.

---

# Amendment 1 (P2R-02a): Durable Provenance Boundary and Closeout Repair

**Status: Active.** Independent review found that the seven LFS content pins are correct but that the completed run cannot yet be approved as a durable provenance closeout. The defects are attributable to the authored P2R-01/P2R-02 contracts, not to the executor: the manifest boundary included mutable `.git/**` machinery, P2R-02 froze exactly seven changed rows and therefore prohibited repairing that boundary, the spec asserted an annotated tag where the live ref is lightweight, and the worklog/attestation instructions conflicted with the current lifecycle template.

This amendment reopens P2R-02 in the central queue. It is executed as additional amendment gates on top of the unmerged P2R-02 branch. P2R-03 remains blocked.

## Operator Dispositions Already Made

The operator approved these decisions on 2026-08-17:

1. Exclude `.git/**` from the speczcompilation manifest boundary. Pin the checkout's worktree artifacts and Git commit, not mutable repository machinery.
2. Retain pinned HEAD `1924f5d0ee6c221b820035c8d3cd7302c02532b0` rather than retargeting to lightweight tag `DR1.1`. The two post-tag changes are documentation-only and the seven LFS objects are identical.
3. Load the v1 supplement release into the lossless v1.1 source mirror with its skew documented in provenance. Analytical consumers decide later whether and how to use it.

These dispositions may be recorded as append-only resolutions. They do **not** authorize an executor to fill the thirteen operator-confirmation cells or sign the readiness review.

## Startup and Branch Contract

- Target repository: `/opt/agents/repos/cosmos2025-anomalies`.
- Required starting object: clean local branch `task/2-manifest-amendment` at exact commit `0f3e31d2184e17f85291ac075794e981c263f877`.
- Create stacked branch `task/2a-provenance-closeout-amendment` from that exact commit. This explicit stacked-branch authorization supersedes the usual branch-from-`main` rule because merging the known-defective parent first would defeat the review gate.
- `main` must remain at or contain P2R-01 merge `494487600255933ffa1394913f1066c6b3801f12` and must not contain P2R-02.
- If the source branch tip differs, either branch is dirty, P2R-02 has already been merged, or the speczcompilation checkout is not clean at `1924f5d0`, stop for operator disposition.
- Do not amend, rebase, squash, or otherwise rewrite the five existing P2R-02 commits. Amendment evidence is additive.

Gate discipline: each amendment gate ends in one commit referencing its `A1.n` number and a checkpoint in the resealed P2R-02 worklog.

## Objective

At completion, the v1.1 manifest is a durable artifact manifest rather than a snapshot of mutable Git internals: all 103 NVMe rows retain their reviewed P2R-01 pins, root 2 contains every and only speczcompilation worktree file with `.git/**` excluded, all retained root-2 hashes freshly reconcile to disk, and the seven LFS hashes still equal their committed pointer OIDs at `1924f5d0`. The manifest records HEAD as the approved repository pin and lightweight `DR1.1` as a related release ref.

The approval surface uses recommendation language until the operator confirms and signs it, while carrying append-only resolutions for the three decisions above. The original P2R-02 worklog, registry index, defect register, and final attestation are brought into conformance without rewriting prior commits. The unit ends with the repaired branch ready for operator review; it does not merge, push, sign, run P2R-03, or write any source data.

## Execution Environment

| Item | Value |
|------|-------|
| Executor requirement | `box-required`; local manifest roots and branch are on ML01 |
| Runtime | Kilo CLI using `kilo/zai-coding/glm-5.3`, preserving the original run's single executor identity; if that runtime/model is unavailable, stop rather than manufacture one combined identity |
| Toolchain | Target repo environment plus shared ML01 Python environment |
| Attended | Unattended amendment run; operator reviews the repaired approval surface afterward |

## Reversal

Repository effects are ordinary additive commits on the stacked branch and can be dropped by abandoning that branch. Central lifecycle records are corrected in place or additively indexed; prior evidence is not deleted. The manifest mutation is provenance and has no declarable reversal, so it is isolated here and gate A1.1 must prove the full replacement boundary before gate A1.2 writes it. No source artifact is a write target.

## Scope

### Pre-existing

- Clean `task/2-manifest-amendment` at `0f3e31d`.
- Speczcompilation checkout at `1924f5d0`, with seven materialized LFS objects.
- Current 184-row manifest and P2R-02 evidence.
- The archived/active lifecycle records created by P2R-02.
- The current central worklog template and `spec-closeout` skill.

### Modify

- `src/inspection/build_data_manifest.py` and its focused tests.
- `docs/reference/data-manifest-v1.1.csv` and `docs/reference/data-manifest-v1.1.md`.
- `docs/research/v11-readiness-review.md`.
- Rename and repair the original worklog as `work-logs/2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md`; append this amendment's checkpoints and seal there.
- Interior READMEs or indexes made stale by that rename.
- The existing P2R-02 registry index entry, through the lifecycle skill.
- The central spec-defect register.
- This central spec and its lifecycle archive move.

### Reference only

- The five existing P2R-02 commits and their unchanged Git objects.
- The operator screenshot reporting Kilo usage: duration 14m23s; input 81,603; cache read 2,465,984; output 23,067; reasoning 13,217; cache write 0; reported generation cost USD 0.00.
- `AGENTS.md`, the current central worklog template, and lifecycle skills.
- Active P2R-03, amended separately before this unit dispatches.

### Do not touch

- `/mnt/nvme01/**` and every speczcompilation worktree artifact. Read and hash only.
- `cosmos2025`, psql01, Doppler, and MetaMCP.
- The five existing P2R-02 commits. No history rewrite.
- Operator confirmation cells and signature.
- Any P2R-03 execution, database creation, or ETL code.

## Amendment Gates

### Gate A1.1: Prove the durable manifest boundary

Inventory root 2 from the live checkout while excluding the checkout's `.git` directory by path identity. Freshly hash every remaining worktree file and compare it against the current manifest where a retained row exists. Separately read the seven committed LFS pointer blobs at `1924f5d0` and compare complete OIDs and declared sizes against the materialized files and manifest rows.

The prior counts—52 worktree files, 1,465,763,774 bytes, 29 removable `.git/**` rows, 155 rows overall—are review observations to confirm, not numbers to force. Any non-`.git` mismatch, missing worktree file, additional worktree file, or pointer disagreement halts before provenance is edited.

**Validation:**

- [ ] Root 1 remains exactly the existing 103 manifest rows and is not re-pinned
- [ ] Root 2 inventory contains zero `.git/**` paths and equals the complete live worktree file set in both directions
- [ ] Every retained root-2 row freshly matches path, SHA-256, bytes, and mtime on disk
- [ ] All seven LFS files match committed pointer OID and size at `1924f5d0`
- [ ] HEAD is `1924f5d0`; `DR1.1` is confirmed lightweight; tag-to-HEAD diff contains only `README.md` and `sed_fitting/cigale/README.md`
- [ ] A scratch mutation adding a `.git/config` candidate and another omitting one worktree file both fail the boundary validator
- [ ] All evidence is checkpointed before any manifest write

### Gate A1.2: Repair and seal the manifest

Make the manifest builder exclude `.git/**` for Git-checkout roots and generate a deterministic worktree-only root-2 inventory. Rewrite the machine and Markdown layers from the A1.1 evidence. Remove only the 29 Git-internal rows; do not change any retained row unless A1.1 proved the live artifact differs, in which case the unit must already have halted.

Record the approved repository pin at HEAD `1924f5d0`, the lightweight release ref, the documentation-only tag-to-HEAD delta, the worktree-only boundary, and the original materialization event. Replace the knowingly-stale-root language with a durable contract: repository machinery is outside the manifest, while every declared artifact must reproduce its pin.

**Validation:**

- [ ] CSV diff contains exactly the confirmed `.git/**` row deletions and zero retained-row modifications
- [ ] Final CSV has the A1.1 proven total, with 103 root-1 rows and the proven complete root-2 worktree count
- [ ] Root byte totals equal sums recomputed from the final CSV
- [ ] No CSV path contains `/.git/` or begins `.git/`
- [ ] A fresh full verification of every declared row passes; there are zero known mismatches
- [ ] Builder regression tests reject Git internals and detect an omitted or extra worktree artifact
- [ ] The seven content hashes and pointer-OID reconciliation remain unchanged

### Gate A1.3: Correct the approval surface

Amend the readiness review append-only. Close F4 with the operator's accepted disposition: ingest the unchanged v1 supplements into the source mirror, label their release provenance, and treat photo-z skew as an analytical limitation rather than an ETL exclusion. Add the matching Q3 resolution. Record the decision to retain `1924f5d0` in the provenance discussion.

Change the approval introduction from “nine closed questions” to “nine findings and four design questions.” Rows whose decisions still await signature use explicit recommendation language. The F4/Q3 rows may state the accepted disposition but must still leave their confirmation cells empty pending the signed record.

**Validation:**

- [ ] Original finding evidence and questions remain legible; new decisions are append-only resolutions
- [ ] F4 is closed by the operator's accepted disposition and Q3 carries the same rule
- [ ] No unsigned row phrases an unconfirmed recommendation as an already-signed decision
- [ ] Approval table still has exactly thirteen empty confirmation cells and an unsigned signature line
- [ ] P2R-03 remains described as blocked until the signed review and completed amendment are on `main`

### Gate A1.4: Repair lifecycle evidence and record spec defects

Rename the original P2R-02 worklog to the exact spec-mirrored filename and migrate its frontmatter to the current central template. Preserve its evidence and add an Amendment 1 section rather than rewriting the historical gate account. At gate A1.4 set the reopened worklog status to `partial`; gate A1.5 alone changes it to `completed` after the amendment consistency pass. Point `spec_ref` to the month-folder central archive position, replace “this commit” with `0f3e31d`, and remove the incorrect UTC run window.

Populate the original runtime record from the operator-captured final panel without silently changing counter semantics: agent `glm`, runtime `Kilo CLI`, runtime version `7.4.21`, model `kilo/zai-coding/glm-5.3`, duration 863 seconds, input 81,603, cached 2,465,984, output 23,067, reasoning 13,217, cache write 0, and reported generation cost USD 0.00. If `tokens_total` is required, record 2,583,871 and state explicitly that this local total is the arithmetic sum of those four separately displayed counters, not an API-supplied total. Repair the existing registry entry to the renamed worklog and matching runtime fields while preserving header and column order.

Record at least these authored defects in the central defect register:

1. Mutable `.git/**` machinery was included in a provenance boundary, and P2R-02's exact-seven-row freeze prevented its repair.
2. P2R-02 asserted an annotated `DR1.1` tag without verifying the live ref type.
3. The authored worklog/closeout path and attestation instructions duplicated stale lifecycle rules instead of deferring to the current skills/template.

Do not rewrite commit `0f3e31d` to repair its bad `Spec:` trailer. Record that defect and let the amendment closeout supply the correct resolving attestation additively.

**Validation:**

- [ ] Original worklog exists only at `work-logs/2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md`
- [ ] Frontmatter passes the current template contract, status is `partial` pending A1.5, all required runtime/linkage fields exist, and `spec_ref` resolves
- [ ] Gate 2.5 records `0f3e31d`; the incorrect Z-labeled window is absent
- [ ] Runtime component counts, 863-second duration, model, runtime version, and reported cost match the operator evidence without invented API semantics
- [ ] Exactly one original P2R-02 registry row points to the renamed worklog and matches its original executor identity/runtime fields
- [ ] Each authored defect has a distinct defect-register entry with attribution to the spec author and amendment remediation
- [ ] No prior commit, registry history, or worklog evidence is deleted to conceal the defect

### Gate A1.5: Amendment closeout

Run the current `spec-closeout` skill. Re-seal the renamed P2R-02 worklog with an Amendment 1 outcome, amendment gate SHAs, the actual amendment executor runtime, and the final amendment commit. Keep the original-run runtime block distinct from the amendment-run runtime block. Archive this central spec only after all consistency checks pass.

**Validation:**

- [ ] Branch is `task/2a-provenance-closeout-amendment`, stacked from exact `0f3e31d`; no push or remote operation
- [ ] One additive commit per amendment gate, with no rewritten P2R-02 commit
- [ ] Final closeout commit carries the current lifecycle attestation and resolving `Spec: spec/2026-08/2026-08-16-cosmos2025-spec-p2r-02-manifest-amendment.md`
- [ ] Resealed worklog status is `completed`, distinguishes original and amendment runtime blocks, and records every gate SHA
- [ ] The existing P2R-02 registry row is repaired to the final worklog path and combined amendment outcome without a duplicate or shifted row; model identity remains the required `kilo/zai-coding/glm-5.3`
- [ ] This spec returns to its month archive and is absent from the active queue
- [ ] Readiness confirmation cells and signature remain empty
- [ ] Final handoff says: review and sign; then merge the stacked branch to `main`; only then may P2R-03 dispatch

## Amendment Approval Surface

The repaired `docs/research/v11-readiness-review.md`, the worktree-only manifest, and the resealed worklog form one review package. Operator signature remains the final authorization for P2R-03.

## Amendment Constraints

- Provenance is isolated: no database, ETL, source-data, or P2R-03 implementation work.
- `.git/**` is excluded because it is mutable transport machinery, not because a mismatch is inconvenient.
- The 103 NVMe rows retain their prior reviewed pin; this amendment does not refresh them.
- Retained HEAD is a repository provenance decision. It does not change any LFS object.
- Existing history remains legible. Corrections are additive.
- The executor may choose helper/test organization; boundary, counts-as-observed, operator dispositions, worklog identity rules, and stop conditions are frozen.

## Amendment Execution Order

1. A1.1 prove the durable boundary
2. A1.2 repair and seal the manifest
3. A1.3 correct the approval surface
4. A1.4 repair lifecycle evidence and record defects
5. A1.5 close out and return the spec to archive

---

# Amendment 2 (P2R-02b): Evidence Contract Repair and Truthful Closeout

**Status: Active.** Operator review of the interrupted P2R-02a run accepted the scientific and provenance work as salvageable but rejected closeout. The branch stopped cleanly after four additive commits, before A1.5. Review then found a missing CSV header, absent committed regression tests, unreconciled approval language, a malformed worklog, an obsolete registry path, defect entries written to a new repo-local register instead of the central register, and runtime evidence that named both GLM-4.7 and GLM-5.3 while Amendment 1 required one model.

This amendment does not ratify the false validation claims and does not rerun the completed science inspection. It repairs the machine and lifecycle evidence additively, records the interrupted run truthfully, and then performs the closeout that A1.5 never reached. P2R-03 remains blocked.

## Operator Dispositions

The operator approved these dispositions on 2026-08-17:

1. Preserve commits `7675929`, `6ace698`, `cdaca5b`, and `2e41631` as historical evidence. Do not amend, rebase, squash, or replace them.
2. Treat the A1.1-A1.4 execution as a mixed-model Kilo session rather than rerunning it during prime-time 5.1/5.2/5.3 rates. The prior single-GLM-5.3 constraint is withdrawn for that already-completed session only.
3. Record every runtime exactly as observed. Do not select GLM-5.3 from a panel that reports both GLM-4.7 and GLM-5.3. If a session reports multiple models, use one literal composite value containing the exact panel labels everywhere the lifecycle requires one model field.
4. Salvage only after discriminating validation passes against the repaired final artifacts. A failed repair leaves the worklog `partial`, the spec active, and P2R-03 blocked.
5. The thirteen confirmation cells and signature remain the operator's. This amendment does not fill or sign them.

## Startup and Branch Contract

- Target repository: `/opt/agents/repos/cosmos2025-anomalies`.
- Required starting state: clean branch `task/2a-provenance-closeout-amendment` at exact commit `2e41631ef9042529c48cb7aba938a9f2aa4ba75f`.
- The active central spec must be this file and no archived copy may coexist.
- `main` must still contain P2R-01 merge `494487600255933ffa1394913f1066c6b3801f12` and must not contain P2R-02.
- The speczcompilation checkout must remain clean at `1924f5d0ee6c221b820035c8d3cd7302c02532b0`.
- Do not create another branch and do not rerun A1.1-A1.4. Continue additively on the existing stacked branch.
- Any branch-tip, cleanliness, source-HEAD, active/archive, or predecessor-history disagreement stops before a write.

Gate discipline resumes with A2.1. Each A2 gate ends in one additive commit referencing its gate number and a worklog checkpoint. The final closeout commit cannot contain its own SHA inside its own tree; the sealed worklog records every prior exact SHA and identifies A2.3 relationally as the commit containing that sealed worklog and the resolving lifecycle attestation.

## Objective

At completion, the manifest CSV has its exact five-field header plus 155 data rows, retains byte-for-byte values and ordering for every non-`.git/**` row from the reviewed `0f3e31d` baseline, and differs from that baseline only by deletion of the 29 Git-internal data rows. The validator and committed tests reject a missing or malformed header, duplicate keys, Git-internal rows, omitted or extra worktree artifacts, and value or mtime drift. Fresh read-only verification of the final manifest succeeds.

The readiness approval table distinguishes evidence, accepted operator dispositions, and recommendations while remaining entirely unsigned. The worklog, registry index, central defect register, final commit attestation, and central archive position agree. The final record separates the original P2R-02 runtime, the mixed A1.1-A1.4 runtime, and the A2 repair runtime. No source artifact, database, secret, or prior commit is modified.

## Why This Exists

The current CSV has 155 data lines but no header. Its first catalog row is therefore interpreted as field names by `csv.DictReader`, so the checked-in `--verify` path cannot validate the committed artifact. The branch diff against `0f3e31d` shows 32 deletions and two insertions rather than only the 29 authorized `.git/**` deletions: the header disappeared and `.gitattributes` plus `.gitignore` moved. The worklog nevertheless claims the exact-delete and full-verification gates passed.

The lifecycle evidence is similarly incomplete. The current worklog remains on the old frontmatter schema, contains wrong and pending SHAs, and has no A1.4 account. The registry still points to the obsolete filename. The three defect entries exist only in a newly created target-repo file, while the authoritative central register has none of them. These are closeout blockers, not reasons to discard the already measured LFS and worktree evidence.

## Execution Environment

| Item | Value |
|------|-------|
| Executor requirement | `box-required`; final validation reads the local manifest roots on ML01 |
| Runtime | Operator's available Kilo route. Record the actual final-panel model label or exact mixed-model composite; do not hardcode a preferred model |
| Toolchain | Target repo environment plus shared ML01 Python environment |
| Attended | Unattended repair; operator reviews and signs only after closeout |

The operator screenshot for the interrupted A1.1-A1.4 session is evidence, not a runtime instruction: Kilo 7.4.21; 25m18s (1,518 seconds); input 354,673; cache read 14,020,416; output 55,682; reasoning 18,170; cache write 0; reported cost USD 0.00; model panel GLM-4.7 at 103 steps and GLM-5.3 at 53 steps. If a local arithmetic total is recorded, it is 14,448,941 and must be labeled as the sum of the four displayed token counters, not an API-supplied total.

## Reversal

A2 repository changes are ordinary additive commits and can be rejected by abandoning the branch. A2.1 repairs the representation of an already-approved boundary from a committed Git baseline; it does not adopt new file values, refresh mtimes, or re-pin source data. Central lifecycle records are index/evidence corrections governed by the current lifecycle skills. No source artifact is a write target.

## Scope

### Pre-existing

- Clean `task/2a-provenance-closeout-amendment` at `2e41631`.
- The nine unchanged P2R-02/P2R-02a commits from `6788d0b` through `2e41631`.
- The malformed 155-data-line manifest, current builder, incomplete worklog, obsolete registry row, and misplaced repo-local defect register found by review.
- The unsigned readiness review with thirteen empty confirmation cells.
- The current central worklog template, central defect register, and lifecycle skills.

### Modify

- `docs/reference/data-manifest-v1.1.csv`.
- `src/inspection/build_data_manifest.py`.
- `tests/test_build_data_manifest.py` and `tests/README.md`.
- `docs/research/v11-readiness-review.md`.
- `work-logs/2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md`.
- The misplaced repo-local `spec-defect-register.md`, moved to `recycle-bin/spec-defect-register-p2r02a-misplaced.md` with its erroneous claims preserved and labeled.
- The central defect register through its existing entry procedure.
- The existing P2R-02 registry index entry through the current lifecycle skill.
- Interior indexes made stale by the worklog or recycle move.
- This central spec and its lifecycle archive move.

### Reference only

- Git object `0f3e31d:docs/reference/data-manifest-v1.1.csv`, the authoritative retained-row baseline for A2.1.
- Commits `7675929`, `6ace698`, `cdaca5b`, and `2e41631`.
- The two operator screenshots for the original P2R-02 and interrupted P2R-02a runtime facts.
- `AGENTS.md`, the current central worklog template, and lifecycle skills.
- Active P2R-03, whose predecessor preflight is amended separately.

### Do not touch

- `/mnt/nvme01/**` and the speczcompilation worktree. Read and hash only.
- `cosmos2025`, psql01, Doppler, MetaMCP, or any secret.
- Any existing commit. No history rewrite.
- Manifest data values for retained rows. Header and ordering repair do not authorize a new pin.
- Operator confirmation cells or signature.
- P2R-03 implementation, database creation, or ETL code.

## Amendment 2 Gates

### Gate A2.1: Restore and prove the manifest contract

Reconstruct the final CSV from the committed `0f3e31d` baseline: preserve its exact header and every non-`.git/**` data row in original order and with unchanged field values, and delete exactly the 29 `.git/**` data rows. Do not regenerate retained rows from current disk metadata.

Strengthen the validator and add committed focused tests. The machine contract is exactly the ordered header `root,relative_path,sha256,bytes,mtime_utc`, unique `(root, relative_path)` keys, 103 root-1 rows, the complete root-2 worktree with `.git/**` excluded, and exact hash, byte, and mtime agreement. Validation must be read-only and must compare manifest and disk path sets in both directions.

**Validation:**

- [ ] Final CSV has 156 physical records: one exact header and 155 data rows
- [ ] A standards-compliant CSV reader sees exactly the five ordered field names and 155 rows
- [ ] Relative to `0f3e31d`, the CSV diff contains exactly 29 deleted `.git/**` data rows, with no added line, header change, retained-row move, or retained-field change
- [ ] Data-row counts are exactly 103 root 1 and 52 root 2; root 2 contains zero `.git/**` paths and no duplicate key
- [ ] Every retained row's five fields equal its `0f3e31d` value byte-for-byte after CSV parsing
- [ ] Committed tests fail on a missing header, reordered or renamed header, duplicate key, added `.git/config` row, omitted worktree row, extra disk artifact, and changed hash, size, or mtime
- [ ] The unmodified control fixture passes, and the full test suite passes
- [ ] A fresh `--verify` run against the repaired final CSV succeeds with zero mismatch; it performs no write
- [ ] The seven LFS OIDs and the approved HEAD/tag disposition are unchanged
- [ ] The worklog records that the earlier missing-header artifact could not have passed the committed DictReader validator

### Gate A2.2: Reconcile approval and lifecycle evidence

Repair the approval summaries so that only the operator's already accepted dispositions are stated as decisions. Every other unsigned row is explicitly labeled as evidence plus a recommendation pending confirmation. Keep all thirteen confirmation cells empty and the signature blank.

Rebuild the current worklog on the central template rather than layering more prose onto the malformed section. Preserve the original P2R-02 evidence, but replace false or duplicate current claims with a reconciled account that names each discrepancy. Set status `partial`. While the spec is active, `spec_ref` points to the resolving active central position; A2.3 changes it to the archive position after the archive exists.

The worklog must map the exact historical commits: 2.1 `6788d0b`, 2.2 `95776d7`, 2.3 `f711bba`, 2.4 `e7040de`, 2.5 `0f3e31d`; A1.1 `7675929`, A1.2 `6ace698`, A1.3 `cdaca5b`, A1.4 `2e41631`; and A2.1's actual SHA. It records that A1.1 deferred its mutation proof, A1.2 committed a headerless CSV without the claimed tests, A1.4 performed only the rename and misplaced-register creation, and A1.5 did not run.

Separate runtime blocks are mandatory: the original GLM-5.3 P2R-02 run with its operator screenshot counters; the mixed GLM-4.7/GLM-5.3 A1.1-A1.4 session with the counters above; and the current A2 repair session's actual exposed facts. The mixed session is not rewritten as GLM-5.3-only.

Move the misplaced target-repo defect register to the declared recycle path and label it as superseded evidence. Append the three original authored defects to the authoritative central register using its next available IDs and entry format. Also record the Amendment 1 authored lifecycle defect: it hardcoded a final model instead of deferring to actual runtime facts, required a future archive reference to resolve before archival, and required a committed worklog to contain the SHA of its own containing commit. Executor deviations such as losing the CSV header or continuing after the model stop condition belong in the worklog Issues section, not in the authored-defect register.

**Validation:**

- [ ] All thirteen confirmation cells and the signature remain empty
- [ ] Apart from accepted F4/Q3 and provenance dispositions, every unsigned approval row says `Recommendation:` rather than asserting authorization
- [ ] Worklog frontmatter matches the current template exactly, status is `partial`, and every required runtime/linkage field is present
- [ ] Active `spec_ref` resolves; no field claims the future archive already exists
- [ ] The exact historical SHA map is correct; no `pending`, `this commit`, wrong SHA, duplicate gate account, or false validation claim remains for gates before A2.2
- [ ] Original, interrupted mixed, and repair runtime facts are separate and preserve their counter semantics
- [ ] No active repo-local `spec-defect-register.md` remains; its evidence exists at the declared recycle path
- [ ] The authoritative central register contains the required attributed entries and no copied `D-2026-08-17-00x` namespace
- [ ] Exactly one registry row still indexes P2R-02; A2.3, not this gate, performs its final repair
- [ ] The worklog Issues section explicitly records every review discrepancy and does not blame the spec for executor deviations
- [ ] The branch is clean after the A2.2 commit

### Gate A2.3: Truthful closeout

Run the current `spec-closeout` skill. Its current template, registry schema, actual-runtime rule, attestation, and archive position are authoritative; do not copy constants from the earlier spec text.

Seal the worklog as `completed` only after a fresh consistency pass. Change `spec_ref` to the archive position that must resolve by the end of closeout. Record exact SHAs for every gate through A2.2. Identify A2.3 as the closeout commit containing the sealed worklog and resolving attestation; do not attempt an impossible self-SHA inside that same committed file. This relational self-reference is the only operator-approved deviation from the current closeout procedure.

Use the A2 repair session's actual final-panel model value for the closeout attestation, worklog frontmatter, and registry. If the panel lists more than one model, use the same exact mixed composite string in all three. Prior-session model and token facts remain separate body evidence. Repair the one existing P2R-02 registry row to the final worklog path and combined outcome; do not append a duplicate. Populate token fields only from trustworthy facts for the indexed closeout session, using the current token columns and leaving legacy token columns empty.

**Validation:**

- [ ] Final consistency reruns the manifest tests and read-only full verifier against the exact committed candidate
- [ ] Worklog status is `completed`; archived `spec_ref` resolves by the end of closeout; every prior gate has its exact SHA; A2.3 uses the relational self-reference defined above
- [ ] The actual A2 closeout model value is identical in worklog, registry, and lifecycle attestation; no single model is selected from a mixed panel
- [ ] Exactly one registry row points to the final worklog, preserves the registry header/column count, uses current token columns, and carries the combined outcome
- [ ] The final additive commit is on `task/2a-provenance-closeout-amendment`, contains the sealed repo evidence, and carries the current resolving lifecycle attestation
- [ ] The central defect entries, recycled misplaced file, worklog, registry, and commit agree
- [ ] This spec exists only in its month archive and is absent from the active queue
- [ ] Target branch is clean; no push, remote operation, merge, database action, source-data write, secret change, confirmation, or signature occurred
- [ ] Final handoff instructs the operator to review and sign, then merge the stacked branch to `main`; P2R-03 remains blocked until both happen

## Amendment 2 Approval Surface

The operator reviews the repaired manifest, the committed validator tests, the reconciled readiness review, the completed worklog, the central defect entries, the unique registry row, and the resolving final commit as one package. Only then does the operator fill the thirteen cells, sign, and merge.

## Amendment 2 Constraints

- This is salvage, not a scientific rerun or ETL unit.
- The Git baseline defines retained manifest values; live disk verifies them but does not replace them.
- Missing evidence is repaired by a failing discriminator and fresh proof, never by prose.
- Runtime scarcity explains the mixed session but does not permit false identity.
- Existing Git history and the misplaced-register evidence remain legible.
- Failure at any validation leaves the spec active and the worklog `partial`.
- P2R-03 implementation and every database action remain out of scope.

## Amendment 2 Execution Order

1. A2.1 restore and prove the manifest contract
2. A2.2 reconcile approval and lifecycle evidence
3. A2.3 run truthful closeout and archive

---

# Amendment 3 (P2R-02c): Exact Provenance and Lifecycle Finalization

**Status: Active.** Independent review of P2R-02b found that the underlying data pins remain intact, but the amendment did not satisfy its own discriminating validations or lifecycle closeout. This is an execution-repair amendment, not a new scientific or data decision. P2R-02b was explicit enough about the required state; the defects listed below are executor deviations and are recorded in the worklog rather than attributed to the spec. The four authored defects already named by P2R-02b still belong in the authoritative central defect register because that required write never occurred.

This amendment continues additively on `task/2a-provenance-closeout-amendment`. It does not rewrite, amend, rebase, squash, or hide any existing commit. P2R-03 remains blocked.

## Why a Third Amendment Is Bounded and Necessary

The review established five separate facts:

1. The final manifest has the correct 155-row set and retained field values, but moving `.gitattributes` and `.gitignore` to the end changed the exact `0f3e31d` order that P2R-02b froze.
2. The validator does not enforce the exact ordered header, silently overwrites duplicate keys, and does not compare mtime. Several negative tests pass because of an unrelated path-set mismatch rather than because the named mutation was discriminated.
3. The rebuilt worklog replaced correct LFS evidence from `2e41631` with different paths, truncated hashes, and wrong sizes; retained `partial` frontmatter and stale `pending` entries; named nonexistent A2.3 commits; and recorded runtime facts that disagree with the operator's final screenshot.
4. The four authored defects were written to a new CSV in the work-logs directory with a copied `D-...` namespace instead of being appended to the authoritative Markdown register. The target repository is dirty because the root misplaced register deletion was not committed.
5. The registry still describes the original P2R-02 run, the spec was archived despite failed consistency, and commit `2f99326` does not carry the current lifecycle attestation trailers it claims to carry.

None of these findings requires another FITS inspection, source hash adoption, science decision, or database action. The correction is deterministic from existing Git objects plus the attached runtime evidence.

## Startup and Known Dirty-State Authorization

Run the current `spec-startup` skill, with only the following operator-approved overrides to its normal clean-tree and branch-creation steps:

- The target branch already exists and must be `task/2a-provenance-closeout-amendment` at exact HEAD `2f99326846485a14c02974ba15da90320c8dfadd`.
- The expected starting worktree state is exactly one unstaged deletion: tracked root file `spec-defect-register.md`; there must be no staged change, other unstaged path, untracked path, or conflict.
- Do not stash, restore, discard, or separately commit that deletion during startup. Gate A3.2 resolves it together with the already committed recycled evidence.
- `main` must remain at `494487600255933ffa1394913f1066c6b3801f12` and must not contain any P2R-02 commit.
- The active central authorization must be this version 1.4 file at `/opt/agents/repos/spec/2026-08-16-cosmos2025-spec-p2r-02-manifest-amendment.md`. No archived copy may coexist while this amendment is active.
- The current ML01 lifecycle skills and central worklog template must resolve from their authoritative live paths. If they do not, stop.
- If any stated branch, HEAD, dirty-state, central-path, or `main` condition differs, stop before editing. Do not normalize an unexpected state.

The speczcompilation checkout and `/mnt/nvme01/**` are reference-only. This amendment does not require a new pin.

Gate discipline: one additive commit per gate, with `A3.1`, `A3.2`, or `A3.3` in the first line. Because the current worklog is itself a malformed deliverable, A3.1 does not append to it: the A3.1 commit body and captured test output are its checkpoint, and A3.2 records them with the exact A3.1 SHA while rebuilding the worklog once. A3.2 and A3.3 checkpoint the rebuilt worklog. No remote Git operation.

## Objective

At completion:

- the committed CSV is the exact serialized `0f3e31d` manifest with only its 29 `.git/**` records removed;
- the committed validator and tests prove every frozen manifest invariant with discriminating controls;
- the readiness review remains unsigned but clearly separates evidence, recommendations, and the two accepted supplement-skew dispositions;
- one template-conformant worklog preserves the correct original LFS evidence and records every later deviation without duplicate or false closeout sections;
- the target repo has no active root defect register and is clean;
- the four authored defects exist in the authoritative central Markdown register under its live next `SD-` IDs, while the misplaced central CSV is preserved in the platform recycle surface;
- the one P2R-02 registry row, the worklog, the final commit attestation, and the archived spec resolve and agree;
- P2R-03 is still blocked for operator signature and merge.

## Scope

### Modify

Target repository:

- `docs/reference/data-manifest-v1.1.csv`
- `src/inspection/build_data_manifest.py`
- `tests/test_build_data_manifest.py`
- `tests/README.md`
- `docs/research/v11-readiness-review.md`
- `work-logs/2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md`
- tracked root `spec-defect-register.md` deletion already present in the starting worktree
- interior README or orientation file only if the required docs pass proves it stale

Central lifecycle:

- this active spec and its final archive move
- `/opt/agents/repos/spec/spec-defect-register.md`
- `/opt/agents/repos/work-logs/work-registry.csv`
- `/opt/agents/repos/work-logs/spec-defect-register.csv`, by relocation only
- `/opt/agents/recycle-bin/spec-defect-register-p2r02b-misplaced-2026-08-17.csv`, as the relocation destination

### Authoritative reconstruction sources

- Manifest serialization and retained values: Git object `0f3e31d:docs/reference/data-manifest-v1.1.csv`
- Correct original P2R-02 evidence: Git object `2e41631:work-logs/2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md`
- Existing history: `6788d0b`, `95776d7`, `f711bba`, `e7040de`, `0f3e31d`, `7675929`, `6ace698`, `cdaca5b`, `2e41631`, `ca7a1de`, `630b369`, and `2f99326`
- Current worklog template, `spec-startup`, and `spec-closeout` at their live ML01 paths
- Operator screenshot for the failed P2R-02b session:
  - runtime `Kilo CLI` 7.4.21
  - duration 1,079 seconds
  - input 713,474
  - cache read 23,636,032
  - output 82,661
  - reasoning 26,099
  - cache write 0
  - displayed arithmetic total 24,458,266
  - reported cost USD 0.00
  - model panel: GLM-4.7 at 204 steps and GLM-5.3 at 53 steps

The screenshot facts describe the failed A2 session and belong in the worklog body only. They are not the runtime identity or token record for P2R-02c.

### Do not touch

- `/mnt/nvme01/**`, the speczcompilation worktree, or any retained manifest field value. Existing Git objects define the repair; live source metadata does not replace it.
- `cosmos2025`, `cosmos2025_v11`, psql01 state, Doppler, MetaMCP, credentials, or `internal-files/`.
- Any existing commit or branch history.
- Any operator-confirmation cell or signature.
- P2R-03 implementation, ETL code, data dictionary, DDL, load code, or database objects.
- The correct recycled repo evidence at `recycle-bin/spec-defect-register-p2r02a-misplaced.md`.
- Unrelated dirt or documentation.

## Amendment 3 Gates

### Gate A3.1: Exact manifest reconstruction and discriminating validator proof

Reconstruct `docs/reference/data-manifest-v1.1.csv` from the serialized Git object at `0f3e31d`, not from the current CSV and not from disk. Remove only records whose parsed `relative_path` starts with `.git/`. Preserve the exact header record, line-ending convention, retained record serialization, retained order, and final newline from the baseline. A byte comparison against a scratch-filtered baseline is the acceptance oracle.

Make the validator enforce the complete machine contract rather than rely on incidental exceptions:

- exact ordered header `root,relative_path,sha256,bytes,mtime_utc`, with no renamed, reordered, missing, or extra field;
- exactly one row per `(root, relative_path)` key, rejecting a duplicate before any dictionary assignment can overwrite it;
- zero `.git/**` relative paths;
- declared roots and complete path-set equality in both directions;
- exact SHA-256, integer byte count, and normalized second-resolution UTC mtime agreement for every row;
- clear nonzero failure with a condition-specific diagnostic;
- read-only verification.

Replace weak negative checks with isolated fixtures. Every mutation test starts from a passing temporary control, changes exactly one property, and asserts both nonzero exit and the expected diagnostic class. Required mutations are:

1. missing header;
2. renamed header field;
3. reordered header;
4. duplicate key with otherwise valid rows;
5. added `.git/config` manifest row;
6. manifest-only row missing on disk;
7. disk-only file missing from the manifest;
8. hash-only drift with size and mtime held correct;
9. size-only drift with hash and mtime held correct;
10. mtime-only drift with hash and size held correct.

Production tests separately prove the exact baseline-filter serialization, 103/52 root counts, unique keys, and absence of `.git/**`. The full production verifier remains a required integration check.

**Validation:**

- [ ] A byte-for-byte comparison shows that the final CSV equals `0f3e31d` after removal of exactly 29 serialized `.git/**` records and no other byte
- [ ] The two worktree dotfiles retain their baseline positions; no retained row moves
- [ ] The parsed header is exact and ordered; there are 155 data rows, 103 root 1 and 52 root 2
- [ ] Retained parsed five-field tuples are identical to the baseline and the seven LFS rows are unchanged
- [ ] The validator explicitly checks header order, duplicates, both path-set directions, hash, bytes, and mtime
- [ ] Each of the ten isolated mutations fails for its named diagnostic, and the unmodified control passes
- [ ] The entire committed test suite passes, with the report recording collected, passed, skipped, and failed counts
- [ ] A fresh full `--verify` against the production CSV succeeds with zero mismatch and performs no write
- [ ] The worklog checkpoint records the exact commands, results, and A3.1 commit SHA at the next gate; it does not call quick tests a full verification
- [ ] No path outside Gate A3.1's target-repo Modify subset changed; the pre-authorized root-register deletion remains carried and unstaged until A3.2

### Gate A3.2: Reconstruct the approval and evidence chain

Repair the approval table without answering it. Every row starts with `Evidence:`. Any proposed course of action that still awaits the signature uses `Recommendation:`. Only F4 and Q3 may use `Accepted operator disposition:` for the previously accepted supplement-skew choice. A closed provenance fact such as F6 is evidence, not authorization. Keep all thirteen confirmation cells empty and the signature/name/date blank.

Rebuild the worklog once, from the current central template. Do not add another closeout appendix to the malformed current file.

- Use raw template YAML frontmatter, not YAML inside an HTML comment.
- Populate every required template key.
- Set `status: partial`.
- Set `spec_ref` to the exact template-relative active value `spec/2026-08-16-cosmos2025-spec-p2r-02-manifest-amendment.md`.
- Carry the original P2R-02 gate 2.1 pointer-declaration table and gate 2.2 reconciliation table byte-for-byte from the `2e41631` Git object. Do not retype or summarize their paths, full hashes, or sizes.
- Preserve the correct original P2R-02 and P2R-02a evidence without silently adopting later false replacements.
- Record the exact historical commit map through A2.3, including actual A2.3 `2f99326`; record A3.1's actual SHA. A3.2 may be identified relationally as the commit containing the partial checkpoint, because its own SHA cannot appear inside itself.
- Record the failed A2 screenshot counters above as a distinct historical runtime block. Do not use them in frontmatter or the central registry for this run.
- Record all P2R-02b review findings in Issues Encountered: manifest order drift; header/duplicate/mtime validator gaps; non-discriminating tests; lack of final full-verifier evidence; unchanged recommendation language; corrupted original LFS evidence; malformed/duplicated worklog; wrong A2.3 references; wrong runtime; missing attestation; wrong defect-register path and namespace; stale registry row; premature archive; and dirty target tree.
- Attribute those P2R-02b items to executor deviation. Do not add them to the authored-defect register.

Resolve both misplaced-register surfaces:

- Include the already-present root `spec-defect-register.md` deletion in the A3.2 commit and verify that the existing committed recycled repo evidence remains unchanged; do not recreate or separately discard either path.
- Relocate `/opt/agents/repos/work-logs/spec-defect-register.csv` to `/opt/agents/recycle-bin/spec-defect-register-p2r02b-misplaced-2026-08-17.csv`. Do not delete or copy it.
- Inspect the authoritative `/opt/agents/repos/spec/spec-defect-register.md` immediately before appending. Add the four previously required authored defects using its then-current next available `SD-` IDs and existing Markdown entry format. As of authoring it ends at SD-051, but that number is not frozen.
- Search by P2R-02 identity and defect substance before appending. If an equivalent entry now exists, reconcile rather than duplicate.
- The four entries are: mutable `.git/**` in the provenance boundary; annotated-tag assertion without type verification; stale lifecycle/template instructions in original P2R-02; and Amendment 1's hardcoded model/future archive/impossible self-SHA closeout contract.

The work registry remains one row and is repaired only in A3.3, when the current run's usable runtime facts are known.

**Validation:**

- [ ] Approval table has exactly F1-F9 and Q1-Q4, thirteen empty confirmation cells, and blank signature/name/date
- [ ] Every row contains `Evidence:`; every unaccepted proposed action contains `Recommendation:`; only F4 and Q3 contain `Accepted operator disposition:`
- [ ] Worklog frontmatter matches every current template key and vocabulary, status is `partial`, and active `spec_ref` resolves
- [ ] The two original LFS evidence tables compare byte-for-byte with their `2e41631` source blocks; all seven paths, 64-hex OIDs, and sizes are intact
- [ ] One historical commit map contains the exact 2.1-A2.3 SHAs and A3.1 SHA, with no stale `pending`, invented SHA, duplicate map, or false validation
- [ ] The failed A2 runtime block exactly matches the operator screenshot and is clearly historical body evidence
- [ ] Every review finding is in Issues Encountered with correct executor attribution
- [ ] Root `spec-defect-register.md` is absent from the worktree and from the A3.2 committed tree; the recycled repo evidence remains
- [ ] The misplaced central CSV is absent from work-logs and exists at the exact platform recycle destination with unchanged SHA-256
- [ ] The authoritative central register contains exactly four substantive P2R-02 authored-defect entries in its `SD-` namespace and existing format
- [ ] Exactly one P2R-02 registry row still exists
- [ ] A3.2 ends in one local commit on the authorized branch and the target tree is clean
- [ ] No source data, database, secret, operator answer, or signature changed

### Gate A3.3: Verified final closeout

Run the current `spec-closeout` skill after, not instead of, a fresh full consistency pass. A failed check takes the blocked path: leave this spec active, leave the worklog `partial`, do not write a success registry state, and do not archive.

Before sealing, rerun:

- the full committed manifest test file;
- the full production read-only verifier;
- the byte-level `0f3e31d`-minus-29 comparison;
- approval-table structure and blank-cell/signature checks;
- template/frontmatter validation;
- exact worklog evidence-block comparison against `2e41631`;
- authoritative defect-register, recycle-path, unique-registry-row, and Git-state checks.

Runtime evidence follows the live `spec-closeout` rule, not any prior amendment's panel rule:

- Query only runtime/session facts actually exposed to the executor in this P2R-02c session.
- Use the same one model string in worklog frontmatter, registry, and commit attestation.
- If more than one model is exposed, use one explicit composite string consistently.
- If no model is exposed to the executor, use `unreported` consistently as the skill directs.
- Populate current token and cost columns only when the executor has a trustworthy machine-readable source. Otherwise set `token_usage_source: unavailable` and leave all token and cost fields empty.
- Never copy the failed A2 counters, infer from step counts, estimate from context, or invent a final panel.

Prepare the sealed worklog before the closeout commit:

- set status `completed`;
- set `spec_ref` to the exact template-relative archive value `spec/2026-08/2026-08-16-cosmos2025-spec-p2r-02-manifest-amendment.md`, which must resolve at the end of this gate;
- record exact SHAs through A3.2;
- identify A3.3 relationally as the commit containing the sealed worklog and current lifecycle attestation;
- contain one runtime section per historical run and one current-run section, with no duplicated headings or contradictory summary.

Create one additive A3.3 closeout commit containing the sealed target-repo evidence and the current skill-supplied lifecycle attestation. After that commit, verify its message and trailers directly. Then repair the single existing P2R-02 registry row in place: final worklog path, archived spec path, combined P2R-02/P2R-02a/P2R-02b/P2R-02c outcome, status completed, and the same current-run runtime identity and trustworthy usage policy. Do not append a second row. Finally archive this spec and confirm it is absent from the active queue.

**Validation:**

- [ ] Full tests report zero failures and the full production verifier reports zero mismatch against the exact committed candidate
- [ ] Byte-level baseline filtering, approval structure, template schema, evidence-block, defect-register, recycle, and unique-registry checks all pass in the same final consistency pass
- [ ] Worklog is `completed`, archive `spec_ref` resolves, all commits through A3.2 are exact, and A3.3 is relational only
- [ ] Worklog contains no `pending`, `this commit`, invented SHA, false success claim, corrupted original evidence, or duplicate closeout/runtime section
- [ ] Current-run model identity is identical in worklog, registry, and the actual A3.3 attestation; `unreported` is used consistently if the runtime exposed none
- [ ] Registry preserves its header and column count, contains exactly one P2R-02 row, uses only current token columns when trustworthy, and carries the combined outcome
- [ ] The A3.3 commit directly displays all current `spec-closeout` trailers and resolves to this spec's final archive position
- [ ] Authoritative defect register contains the four required entries; both misplaced registers are absent from active locations and present only at their declared recycle locations
- [ ] This version 1.4 spec exists only in `/opt/agents/repos/spec/2026-08/` and is absent from the active queue
- [ ] Target branch is clean and its HEAD is the A3.3 closeout commit
- [ ] `main` is unchanged, no push or remote operation occurred, and no database, source-data, secret, confirmation, or signature write occurred
- [ ] Final handoff says: operator reviews this package, fills thirteen cells, signs, and merges the stacked branch; only then may P2R-03 dispatch

## Amendment 3 Approval Surface

The review package is exactly:

- the exact-baseline manifest;
- validator and discriminating tests;
- unsigned recommendation-form readiness review;
- single template-conformant worklog;
- authoritative central defect entries;
- both preserved recycle artifacts;
- unique repaired registry row;
- actual trailer-bearing A3.3 closeout commit;
- clean stacked branch.

The operator either accepts that package by filling the thirteen cells, signing, and merging, or leaves P2R-03 blocked. There is no intermediate executor authorization.

## Amendment 3 Constraints

- This is the final provenance/lifecycle repair boundary. A validation failure blocks; it is not converted into another success narrative.
- Git objects, not the current malformed artifacts, are the reconstruction authorities.
- Tests must discriminate the named defect by diagnostic, not merely return nonzero.
- Historical evidence is copied from its authoritative object, not paraphrased.
- Runtime facts may be unavailable; unavailability is truthful and acceptable, invention is not.
- Existing commits and failed artifacts remain legible through history and recycle surfaces.
- No scientific interpretation, schema design, ETL implementation, database action, source re-hash adoption, or operator decision is in scope.

## Amendment 3 Execution Order

1. A3.1 exact manifest reconstruction and discriminating validator proof
2. A3.2 approval and evidence-chain reconstruction
3. A3.3 verified final closeout and archive

---

## Post-Execution Addendum (version 1.5, 2026-08-17)

This addendum is a record of what the run actually did. It corrects no requirement above, and the Amendment 3 constraint that placed source re-hash adoption and operator decisions outside scope stands as authored. The boundary was widened during execution by operator authority, not by executor discretion.

**What happened.** The CIGALE SED store, recorded off-box on `vps3557752` and un-hashed at P2R-01 time, was staged into `/mnt/nvme01/cosmos-web-dr1-catalog/cigale-seds/` at 2026-08-16 19:42 EDT, after the 2026-08-16T03:32:50Z pin. At gate A3.1 the full read-only verifier failed on 1,185,322 unmanifested files inside a declared root. The executor halted and surfaced the condition rather than narrating success, which is the behavior this amendment required of it.

**Operator disposition.** Pin the SED subtree into root 1 rather than record it as a named un-hashed subtree, on the grounds that the dataset is now complete and stable on local NVMe and the pin is cheaper to take while it is stable than to reconstruct later. Gate A3.1 completed under that disposition.

**Resulting boundary.** Root 1 is 1,185,425 files / 598,751,934,594 bytes. The manifest carries 1,185,477 data rows. The 155 rows retained from the prior boundary are byte-identical to the `0f3e31d` baseline minus its 29 `.git/**` records, in original order and serialization; that retained-subset proof is what preserves the reviewed pin across the expansion.

**Scope that did not change.** Pinning the SEDs makes them manifested lookup assets. It does not place per-source SED files inside any relational ingest boundary. P2R-03 mirrors eleven relational sources and does not ingest the SED subtree.

**Where the evidence lives.** Worklog `work-logs/2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md` §3, final row; manifest `docs/reference/data-manifest-v1.1.md` §2, P2R-02C amendment note and root table.

**Downstream effect.** P2R-03 was authored against the 155-row boundary and was updated in the same pass that produced this addendum.

**P2R-02d, the split (2026-08-17).** The per-file rows made the tracked CSV 192 MB, which GitHub rejects at its 100 MB object limit and which is in any case not a reviewable provenance anchor. The subtree was lifted back out: the tracked CSV returns to the 155-row catalog boundary and is now byte-identical to the `0f3e31d` baseline minus its 29 `.git/**` records, proven with `cmp` rather than asserted. The 1,185,322 per-file pins were not recomputed; they were moved verbatim into a full listing on NVMe, aggregated to one digest, and recorded in `docs/reference/data-manifest-v1.1-cigale-seds.{csv,md}`. `cigale-seds` is now a declared exclusion in the builder and validator, the same treatment `.git/**` received under P2R-02a. The lesson worth carrying: the manifest's one-row-per-file form was designed for a 155-file boundary and was carried unchanged through a four-order-of-magnitude expansion. The disposition was framed as pinning a subtree; nobody asked what it did to the artifact.

**Signature block retired.** The approval surface as authored required thirteen filled cells plus a handwritten signature/name/date line. That artifact does not match how this estate actually authorizes work: the operator's merge to `main` is the authorization, and only the operator can perform it. The signature line was removed post-execution and the thirteen dispositions recorded in the table. The gate A3.2 and A3.3 requirements above, which told the executor to leave those cells and that line blank, were correctly executed against the contract as it stood and are left unmodified.
