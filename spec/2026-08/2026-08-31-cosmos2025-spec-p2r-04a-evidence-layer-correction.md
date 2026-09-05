<!--
---
title: "Phase 2 Restart Unit 4a: Spec-z Linkage Evidence-Layer Correction"
description: "Repair the gate 4.1 identifier-space conflation and the gate 4.7 incomplete confidence distribution, add tests that catch both failure modes, and correct the P2R-04 review surface without touching the sealed mirror"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.0"
status: "Active"
amends: "spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md"
tags:
  - type: specification
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
  - tech: python
  - tech: postgresql
  - tech: astropy
related_documents:
  - "../cosmos2025-anomalies/AGENTS.md"
  - "../cosmos2025-anomalies/docs/research/specz-linkage-evidence.md"
  - "../docs/workload-guidance/astronomy.md"
---
-->

# Spec P2R-04a: Spec-z Linkage Evidence-Layer Correction

**Amendment to P2R-04.** Gates: A1.1 through A1.5.

Parent: `spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md`, executed to completion on branch `task/4-specz-linkage-correction` at closeout `04b42e1`. The parent is archived and write-once. It is not reopened, edited, reversioned, moved, or annotated by this unit.

This spec inherits the parent's scope boundaries, frozen decisions, constraints, and do-not-touch list in full. It states only what changes. Read the parent before starting; do not reconstruct it from what appears here.

**Mode: central-queue repo execution.** Target repository `/opt/agents/repos/cosmos2025-anomalies`. Lifecycle per `spec-startup` and `spec-closeout`.

**Branch: the parent's.** `task/4-specz-linkage-correction` is unmerged with an open PR, so this unit's gates ride that branch and that PR rather than opening a new one.

**Startup prerequisites.** `task/4-specz-linkage-correction` clean at exact commit `04b42e1`, with the ten P2R-04 gate commits intact and unrewritten. `main` at `e65242a`, containing no P2R-04 commit. `cosmos2025_v11.source` holding thirteen relations with the row counts in `source.provenance`, and `specz_compilation_all` at 482,579 rows. `docs/research/specz-linkage-evidence.md` present at its P2R-04 revision. The parent spec present only at `spec/2026-08/` and absent from the active queue. Any disagreement stops before a write.

---

## Objective

At completion, the gate 4.1 evidence command pairs each stored link value with the catalog source that carries it rather than with the source whose `id` coincidentally equals it, and reports the all-links and resolving-subset populations as two separately named quantities. The gate 4.7 confidence and flag distributions carry every observed category with totals that reconcile against independently counted populations. Committed tests fail on identifier-space conflation, on row permutation, on a missing category, and on a non-reconciling total, each for its own named reason.

`docs/research/specz-linkage-evidence.md` carries the corrected values, closes F-06 positively, names the population on every separation statistic, and records the process failure that let a firing check pass. The population-A classification is reported across a range of match radii rather than at one arbitrary value.

No database object changes.

---

## Why This Exists

**Both defects are the executor's, not the spec author's.** P2R-04 asked for the right measurement and required distributions to be full rather than summarized. The evidence command computed one measurement against the wrong identifier space, and the completeness check that should have caught the other was structural rather than discriminating. No entry is owed to `spec/spec-defect-register.md`; both defects belong in the worklog Issues section.

### D1: defective-path geometry computed against the wrong identifier space

In `src/etl/verify_specz_linkage_v11.py`, establishment 3 resolves the catalog side of each pair with:

```python
cat_ra[np.searchsorted(cat_id, link_distinct[hit])]
```

`link_distinct` holds compilation `Id_specz` values. `cat_id` is `arange(784016)`, and the function asserts that at load. The `searchsorted` therefore returns the link value itself, so the expression resolves to the catalog source whose `id` equals the link value rather than the catalog source that carries that link.

The `hit` mask is computed correctly, which is why the population size came out at exactly 24,364 while every pair carries the wrong source on one side. The compilation-crossmatch path a few lines above uses `cat_ra[c25_all[...]]`, which is correct because `Id_COSMOS25` genuinely is a catalog id; that distribution reproduces exactly and is out of scope.

Measured independently, twice by Astropy and once by PostgreSQL spherical trigonometry against the sealed mirror:

| Population | Basis | n | Median | Min | Max |
|---|---|---:|---:|---:|---:|
| All links | `specz_compilation_all.ra_corrected` to the source carrying the link | 37,219 | 4054.34" | ~0" | 9085.0" |
| Resolving subset | `specz_compilation_unique.ra_corrected` to the source carrying the link | 24,364 | 4245.57" | ~0.01" | 9085.0" |
| Resolving subset | as reported by the defective code | 24,364 | 4467.3" | 45.59" | 8727.4" |

The reported minimum is the tell. A true minimum near zero means some links coincidentally point at or beside the right source; a reported minimum of 45.59 arcsec means the small-separation tail was never in the sample.

### D2: incomplete confidence distribution with a non-reconciling total

Gate 4.7 rendered the F-10 selection-function distributions without the `Confidence_level = 85` bucket while the surface text calls them full distributions, and stated a non-resolving entry total of 12,412 against a measured 12,610. Measured directly: 632 resolving and 590 non-resolving entries at confidence 85. The resolving total of 21,700 is correct. The stated total is inconsistent with its own listed components even before the missing bucket is added.

### The compounding failure

`verify_specz_linkage_v11.py` carries `"defective_median": 4054.0` in its `PRIORS` dict and compares against it. **The check fired.** The run received a disagreement on precisely the number that was wrong, and resolved it by authoring finding F-06, which explains the prior as unreconstructible, rather than by debugging the code that failed the check. The prior was correct, and its basis reconstructs from the sealed mirror to two decimal places.

This is the inverse of the usual failure. The discriminator worked. Treating a failing discriminator as a basis ambiguity is what silenced it, and 441 passing tests did not compensate because none of them cross-checks a generated scientific number by a second independent route.

That is why this is a work unit rather than a bug-fix commit: the code fix is one line, and the standard it restores is not.

---

## Prior Observations, To Be Verified

Priors, not facts. The executor confirms each against the artifact and records the observed value beside it.

| Observation | Prior |
|---|---|
| All-links defective-path median, `specz_compilation_all.ra_corrected`/`dec_corrected` | 4054.34" |
| All-links defective-path max | 9085.0" |
| All-links population (stored non-sentinel link values) | 37,219 |
| Resolving-subset defective-path median, `specz_compilation_unique.ra_corrected`/`dec_corrected` | 4245.57" |
| Resolving-subset population (link values also present in `_unique`) | 24,364 |
| Confidence 85 attached entries, resolving-source population | 632 |
| Confidence 85 attached entries, non-resolving-source population | 590 |
| Attached-entry total, non-resolving-source population | 12,610 |
| Attached-entry total, resolving-source population | 21,700 |
| Compilation-crossmatch median (unchanged, control) | 0.0840" |

---

## Execution Environment

Deltas from the parent only.

| Item | Value |
|------|-------|
| Reasoning effort | Standard. The diagnosis is complete; this unit is repair and verification. |
| Seat | Must not be executed by the occupant that executed P2R-04. This unit repairs that run's output, and build and review are separate seats. |
| Database authority | Read-only. This unit has no write authority and must not acquire any. |

### Database access is structurally read-only

This unit is evidence-only, so it does not merely avoid writing: it runs without the ability to write.

Every database session opened by this unit must be read-only-enforced at connection time. Prefer connecting as `cosmos2025_v11_ro`. If that role cannot authenticate from the executor's host, connect as the admin identity with `default_transaction_read_only = on` set in the connection options, which `verify_specz_linkage_v11.py` already does and which every other evidence command in this unit must also do. Record the identity and the enforcement mechanism per session in the worklog.

No code path may clear the read-only setting, open a second unenforced connection, or reconnect to escape it. A correction that appears to require write authority is the finding, not the workaround: stop and signal.

The closeout comparison of relation list, row counts, comments, and provenance is defense in depth. It is not the enforcement mechanism, and on its own it would not detect an `UPDATE` that preserved row counts.

---

## Reversal

Additive commits on an existing branch; reversal is dropping them. The parent's gate 4.5 load seal stands and is not reopened.

**Destructive-retry budget: zero.** Evidence-layer work has no legitimate reason to touch data. If a correction appears to require a write to `cosmos2025_v11`, that appearance is itself the finding: stop and signal through the parent's blocked-signal channel.

---

## Scope

The parent's Scope section governs. This section states only the delta.

### Modify

- `src/etl/verify_specz_linkage_v11.py`
- `src/etl/characterize_specz_linkage_v11.py`
- `tests/` and `tests/README.md`
- `docs/research/specz-linkage-evidence.md`: F-01, F-03, F-06, F-08, F-10, one new process finding, and D-01 if the radius sensitivity moves the split
- `work-logs/2026-08-31-cosmos2025-worklog-p2r-04a-evidence-layer-correction.md` (new; this unit's own worklog)
- One new work-registry row for this unit
- This spec and its archive move at closeout
- Interior READMEs and indexes the docs pass makes stale

### Do not touch

The parent's do-not-touch list remains in force unchanged.

**The F-08 radius-sensitivity check in gate A1.3 is the sole authorized analytical extension beyond D1/D2 repair. No other new analysis is permitted.** It is included because D-01 will be decided on the 694 / 338 split and pricing that dependency now is cheap; it is named here rather than folded into a defect repair it does not belong to.

This unit adds:

- **Every database object in `cosmos2025_v11`.** No reload, no DDL, no rename, no provenance edit, no comment change. The mirror was verified independently and is correct.
- **The parent spec.** Archived, write-once. Not reopened, edited, reversioned, moved, or annotated, including with a pointer to this amendment.
- **The parent's worklog and its registry row.** Both closed when its gates finished and are final. This unit writes its own.
- **The ten existing gate commits.** No rewrite, rebase, squash, or amend.
- **Parent gates 4.2 through 4.6 and their outputs**: dictionary, DDL, rename, load, reconciliation, provenance. Verified independently.
- **Findings F-02, F-04, F-05, F-07, F-09, F-11, F-12, F-13.** Reproduced independently and byte-unchanged.
- **The F-07 regeneration architecture.** Real concern, its own unit, recorded in Notes.

---

## Deliverables

Gate discipline: each gate ends in one additive commit referencing its gate number, and a worklog checkpoint.

### Deliverable 1: Reproduce both defects with failing tests (gate A1.1)

Before changing any generator, add tests that fail against the current committed code, and record the failure output.

For D1, the test must catch identifier-space conflation rather than freeze a number. Assert that the catalog source paired with each link value is the source whose `id_specz_khostovan25` equals that value, established by direct lookup rather than by index arithmetic on a coincidentally-ordered array. Include a fixture that permutes the catalog rows before pairing: association is by stored link value, so the computed distribution must be invariant under row permutation. A test asserting only a median would pass a future off-by-one and does not satisfy this gate.

For D2, the test must derive the observed set of `Confidence_level` categories from the data, require every observed category to appear in the rendered distribution, and separately require that bucket counts sum to the stated total and that the stated total equals an independently counted population. Gate 4.7's original check accepted a distribution missing a category while the text claimed completeness; that check is structural and is replaced, not extended.

**Validation:**

- [ ] Both new tests fail against the code at `04b42e1`, with failure output recorded in the worklog
- [ ] The D1 test fails because the wrong catalog source is paired, evidenced by naming a specific link value and both candidate sources, not merely by a numeric difference
- [ ] The permutation fixture is present and demonstrably exercises the pairing path
- [ ] The D2 test fails on the missing category and on the non-reconciling total as two distinct assertions
- [ ] No generator, no report, and no database object changed at this gate

### Deliverable 2: Correct the defective-path geometry (gate A1.2)

Repair establishment 3 so the catalog side of each pair is the source carrying the link. Compute and report both populations, named explicitly and never conflated:

- **All-links population**: all 37,219 stored non-sentinel link values, paired against `specz_compilation_all` by `Id_specz`, using `specz_compilation_all.ra_corrected`/`dec_corrected`.
- **Resolving-subset population**: the link values also present in `specz_compilation_unique`, using that table's `ra_corrected`/`dec_corrected`. These remain the corrected coordinates of the selected spectroscopic measurement; `_unique` is deduplicated by source, which does not make its coordinate columns galaxy-level quantities.

The `PRIORS` entry `defective_median` refers to the all-links population; label it so in the code. Add a cross-check that recomputes the all-links median by a second independent route and asserts agreement, so a regression in one implementation cannot pass silently. The second route must not share the pairing code under test. If it uses the spherical law of cosines, clamp the cosine argument to `[-1, 1]` before `acos()` or use a numerically stable formulation: an independent validation route must not introduce its own floating-point edge case, even one that only bites far from the median under test.

**Validation:**

- [ ] Both populations are computed, named, and reported with n, min, median, p90, p99, max
- [ ] The all-links median reproduces 4054.34 arcsec to two decimals, and the `defective_median` prior check passes rather than being explained
- [ ] The resolving-subset statistics are reported separately and are never presented as the same quantity as the all-links figures
- [ ] The independent cross-check agrees with the primary computation within a stated tolerance, and the tolerance is justified by numerical argument rather than chosen to fit
- [ ] The compilation-crossmatch distribution is byte-unchanged from the P2R-04 run, confirming the repair did not disturb a correct path
- [ ] All gate A1.1 tests now pass, including the permutation fixture
- [ ] No database object changed

### Deliverable 3: Correct the distributions and add radius sensitivity (gate A1.3)

Regenerate the F-10 confidence and flag distributions with every observed category present and totals reconciling against independently counted populations.

In the same pass, report the population-A classification at 3, 5, and 10 arcseconds rather than at 5 alone, and state whether the 694 / 338 split is stable across them. The 5-arcsecond radius was an executor choice that determines a number D-01 will be decided on, and this is the cheapest moment to remove that arbitrary dependency.

Also state whether the self-crossmatch constructs connected components. If A-B and B-C fall within the radius while A-C does not, the resulting group is transitive and "within N arcseconds" means something different from what a reader assumes. This is not necessarily wrong; it must be described rather than left implicit.

**Validation:**

- [ ] Every observed `Confidence_level` category appears in both rendered distributions, including the 85 bucket
- [ ] Bucket counts sum to the stated total in every rendered distribution, and each total equals an independently counted entry population
- [ ] The flag distributions carry the same completeness and reconciliation checks as the confidence distributions
- [ ] Population-A classification is reported at 3, 5, and 10 arcseconds with the split at each, and stability is stated as a conclusion rather than left to the reader
- [ ] Whether the matching is transitive is stated explicitly, with the multi-member component count if it is
- [ ] All gate A1.1 D2 tests pass
- [ ] No database object changed

### Deliverable 4: Correct the review surface (gate A1.4)

Update F-01, F-03, F-08, and F-10 with the corrected values. Every separation statistic names its population and its coordinate basis, so the 37,219 and 24,364 figures cannot be confused again.

Rewrite F-06 as positively closed. The prior's basis is the all-links population, it reproduces to 4054.34 arcsec, and the earlier claim that the basis was unreconstructible was incorrect. Do not replace one caveat with another.

Add one new finding recording the process failure: a prior check fired and was explained in the review surface rather than debugged. Attribute it to the executor, state the corrected practice, and give it a stable ID continuing the existing sequence.

Revisit D-01 if the radius sensitivity moved the population-A split materially; otherwise state that it did not.

**Validation:**

- [ ] Every separation statistic in the surface names its population and coordinate basis
- [ ] F-06 is closed with the reproduced value and states plainly that the earlier non-reconstructibility claim was wrong
- [ ] The new process finding attributes the failure to the executor, without blaming the spec and without softening it
- [ ] No finding retains a superseded number; a diff against the P2R-04 revision shows only intended changes
- [ ] D-01 carries the radius-stability result or an explicit statement that the split did not move
- [ ] Findings F-02, F-04, F-05, F-07, F-09, F-11, F-12, and F-13 are byte-unchanged, verified by diff
- [ ] The surface still decides no policy question and contains no selection rule

### Deliverable 5: Closeout (gate A1.5)

Run the current `spec-closeout` skill. This unit closes out as a spec in its own right: its own worklog mirroring this spec's filename, its own registry row, its own archive move into `spec/2026-08/`, and its own attestation naming its own archived path.

Record both defects in this unit's worklog Issues section, attributed to executor deviation. **Neither belongs in `spec/spec-defect-register.md`**, which records authoring defects, and the parent has none.

**Validation:**

- [ ] Branch `task/4-specz-linkage-correction`, additive commits only, no push, no remote operation, no rewritten history
- [ ] One commit per gate, each referencing its `A1.n` number
- [ ] Full test suite passes, including every gate A1.1 test
- [ ] This unit's worklog exists at the mirrored filename, status `completed`, with every gate SHA and both defects in Issues attributed to executor deviation
- [ ] One new registry row for this unit; the parent's worklog and registry row are byte-unchanged
- [ ] `spec/spec-defect-register.md` is unchanged
- [ ] The parent spec is still at `spec/2026-08/` at version 1.0, byte-unchanged, absent from the active queue, and carries no pointer to this amendment
- [ ] This spec is archived to `spec/2026-08/` and absent from the active queue
- [ ] Every database session ran read-only-enforced, with the identity and the enforcement mechanism recorded per session in the worklog; no session cleared the setting or reconnected to escape it
- [ ] Defense in depth only: relation list, per-table row counts, comment count, and provenance rows compare equal against their pre-run values. Read-only sessions are the enforcement; this comparison would not detect a row-count-preserving UPDATE on its own.
- [ ] Final handoff states that the branch is ready for operator review and merge

---

## Human Approval Surface

The corrected `docs/research/specz-linkage-evidence.md`.

Operator disposition of the corrected surface authorizes the merge of `task/4-specz-linkage-correction` and unblocks the spec-z science surface unit.

---

## Constraints

The parent's constraints remain in force. This unit adds:

- **A failing prior check is a defect report.** It is never resolved by authoring a finding that explains the prior away. If a check fires and the code later proves correct, the evidence for that is an independent recomputation, not an argument.
- **Name the population on every statistic.** Two medians over two populations are two numbers, not a discrepancy.
- **Name the cardinality domain on every count.** Measurement, compilation entry, deduplicated entry, and COSMOS-Web source are four different domains and this investigation has already confused them once. A count says which domain it counts and which population it was drawn over, in the prose as well as the table header.
- **No database write, and the retry budget is zero.** Sessions are read-only-enforced at connection time rather than by intention. If a correction appears to need write authority, that is the finding; stop and signal.
- **Tests target the failure mode, not the number.** A regression freezing today's value would pass a future off-by-one and does not satisfy gate A1.1.
- **Do not widen.** Only the named findings change.

---

## What the Executor May Choose

Module decomposition, the second computation route for the cross-check, test organization and fixtures, the radius-sensitivity implementation, and worklog prose organization.

Frozen: which findings change and which are byte-unchanged; that both populations are reported separately and named; that F-06 closes positively; the zero-write and zero-retry contract; the prohibition on freeze-the-number tests; and the attribution of both defects to executor deviation.

---

## Execution Order

1. Preflight per `spec-startup`, plus this spec's startup prerequisites
2. Gate A1.1 (failing tests for both defects)
3. Gate A1.2 (correct the defective-path geometry)
4. Gate A1.3 (correct the distributions, add radius sensitivity)
5. Gate A1.4 (correct the review surface)
6. Gate A1.5 (closeout)

---

## Notes

**On what the defect did not touch.** F-08's result stands: every one of the 694 population-A representatives names a different catalog source, and none names the same one. That is the most interesting finding in P2R-04, it lives in a different establishment, and the correction does not reach it. The corrected surface should not read as though the whole unit were in doubt.

**Recorded for a successor unit, explicitly out of scope here.** Extending the sealed dictionary invalidated the P2R-03 verification surface's regeneration seals, and P2R-04 repaired it by pinning committed bytes at `e65242a` behind a seal-checked provider. That is the right immediate call and the wrong long-term architecture: every future extension adds another bespoke fallback keyed to another ref, and reproducibility quietly becomes replayability. The direction worth specifying separately is a versioned input snapshot, where a verification artifact records its generator version plus the dictionary and evidence commit it was produced against, so reproducing P2R-03 means running its generator against the P2R-03 snapshot rather than teaching the current generator to impersonate a historical input. Git already stores the snapshots; the missing piece is making the binding explicit.
