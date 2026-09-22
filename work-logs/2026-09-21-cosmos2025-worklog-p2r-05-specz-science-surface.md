<!--
---
title: "Worklog: P2R-05 Spectroscopic Association and Eligibility Product"
description: "Build and verify the reproducible source-level spectroscopy product in cosmos2025_v11.analysis with explicit eligibility, conflict evidence, separate broad-line validation, and frozen source-level partitions"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-21"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: astronomy
  - domain: spectroscopy
  - domain: data-engineering
  - tech: python
  - tech: postgresql
# --- Runtime Context (required) ---
agent: "kilo"
runtime: "Kilo CLI"
runtime_version: ""
model: "kilo/zai-coding/glm-5.3"
hostname: "ml01"
spec_ref: "spec/2026-09/2026-09-21-cosmos2025-spec-p2r-05-specz-science-surface.md"
repo: "cosmos2025-anomalies"
category: "astronomy"
duration_seconds:
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
  - "docs/research/specz-science-dispositions.md"
  - "docs/research/specz-linkage-evidence.md"
  - "docs/research/specz-science-p2r05/README.md"
---
-->

# Worklog: P2R-05 Spectroscopic Association and Eligibility Product

Long-horizon execution of spec P2R-05 v1.0 (operator approved 2026-09-22,
SHA-256 `7f481111ad826dd80b01106eeec71bfdaf0f5c649c0cc79b8661a0087af2757b`).
Series identifier P2R-05, gates 5.1 through 5.9. Local-commit-only posture:
no push, no PR, no remote operations by the executor.

- Starting branch: `main`
- Base commit: `2f2c84ec3f7d780a96a6344ccc8e14650e5979f3`
- Working branch: `task/5-specz-science-surface`

Operator interactions are recorded in
`docs/research/specz-science-p2r05/operator-interactions.md`. One occurred:
the 2026-09-22 dispatch-session approval of spec v1.0 with P-01 through P-09
frozen, including the instruction to update the spec frontmatter to v1.0 /
Active before computing the approved digest.

---

## Gate 5.1 — Executable contract and input identity

Completed 2026-09-22. Checkpoint facts:

- Startup: ML01 lifecycle skills resolved from
  `/opt/agents/repos/local-agent-skills/skills/` (`spec-startup`,
  `spec-closeout` with the astronomy-coding-bot trailer and the central
  `work-logs/work-registry.csv` registry). Shared venv active
  (`/opt/agents/venv/bin/python`, Python 3.12.3). Tree clean at branch
  creation.
- Approval: operator approved spec v1.0 with P-01..P-09 frozen; spec
  frontmatter updated to version 1.0 / status Active at the operator's
  instruction before digest computation; approved digest recorded in
  `docs/research/specz-science-dispositions.md` with the D-01..D-07 linkage
  and the policy/priors/adoption separation.
- Direct analyst preflight (fresh connection through the fixed handoff):
  database `cosmos2025_v11`, `session_user` = `current_user` =
  `cosmos2025_v11_ro`, connection-time `default_transaction_read_only=on`
  and `transaction_read_only=on`, no superuser/createdb/createrole/
  replication/bypassrls attributes, database CONNECT granted and CREATE
  denied, source schema USAGE granted and CREATE denied. All 13 source
  relations readable with SELECT only; no INSERT/UPDATE/DELETE/TRUNCATE;
  no analyst ownership. Counts: photometry_primary 784,016;
  specz_compilation_unique 261,975; specz_compilation_all 482,579;
  provenance 12. `analysis` schema absent as expected at 5.1.
- Pin comparison: both compilation FITS manifest pins equal freshly
  observed SHA-256 values; all 12 provenance rows agree internally and with
  the manifest for the two specz artifacts; dictionary CSV, data_paths.yaml,
  policy v1 YAML, approved spec bytes, and the dispositions record hashed
  into the input identity.
- Before-state: all 13 source relations captured with column definitions,
  constraints, comments, counts, and seeded content digests (modulus 977,
  offset 3) through the analyst path; protected v1 identity captured through
  the admin transport under an enforced read-only transaction
  (fingerprint SHA-256 recorded in the staging evidence).
- Snapshot: one REPEATABLE READ READ ONLY transaction exported
  photometry_primary (id, tile, flag_star, flag_blend, mag_auto_f150w,
  mag_auto_f277w, mag_auto_f444w), lephare (id, type), and both specz
  compilation tables (all 32 native fields), ordered by primary key, with
  per-file SHA-256 in `staging/derived/specz-p2r05/input-snapshot/manifest.json`
  (manifest digest `4867127853cc73bbd704400c37abffe8605b550e50eeed5c53f87c325a2e71d4`).
  Subsequent passes read this captured identity.
- Policy machine checks: `configs/specz_science_policy_v1.yaml` validated by
  32 tests in `tests/test_specz_science_policy.py` (missing/extra/wrong-type/
  out-of-domain rejections, flag→confidence mapping per the pinned
  compilation README, P-06 tile algorithm determinism, order-independence,
  salt sensitivity, unassigned handling, duplicate-domain and count-sum
  rejection).
- Evidence files: `staging/derived/specz-p2r05/preflight-5-1-analyst-pins.json`,
  `preflight-5-1-before-state.json`, `preflight-5-1-v1-identity.json`,
  `input-snapshot/manifest.json`.

Gate 5.1 validation checklist: all six items satisfied; noted deviations:
none.

---

## Gate 5.2 — Remove the three known execution hazards

Completed 2026-09-22 (checkpoint appended with the 5.3 commit; the 5.2
commit is `13d2291`).

- `src/features/compute_tension_scalars.py`: `main()` now refuses with an
  explanatory SystemExit before `load_config` or the connection factory can
  be called; no override flag exists; all computation/report helpers remain
  importable and the historical tests still pass.
- `src/etl/load_specz_all_v11.py`: the load transaction is extracted into
  `_load_transaction` with `_handle_load_failure` and
  `_classify_uncertain_commit`. Precommit failures roll back with no
  compensating DROP; failures at/after the commit attempt are classified
  read-only through an independent admin connection and retained.
  `_ensure_target_absent` refuses pre-existing relations. No production
  invocation of load/provenance/comment-mutation modes occurred; the source
  mirror was not reloaded or mutated.
- `REVIEW.md`: corrected the join-direction bullet (compilation
  `Id_COSMOS25` into `photometry_primary.id` is the only verified path; the
  catalog link column does not resolve against the held DR1.1 compilation),
  updated the mirror boundary to twelve mirrors, added the grain bullet for
  the two compilation surfaces, and separated source fidelity from
  permissible derived rejection under approved policy.
- Tests: `tests/test_specz_hazard_repairs.py` (14 tests) cover the CLI
  refusal, no-connection assertion, no-override scan, helper importability,
  precommit rollback, uncertain-commit retention with independent
  classification, interruption, classification failure, unknown state
  reporting, and — under the scoped Doppler runtime — scratch-database
  proofs that a post-commit failure retains the installed table and data,
  a precommit failure leaves no table, and the existing-object guard
  retains observable values. Verified under `doppler run --project ml01
  --config dev` (14 passed).

## Gate 5.3 — Reproduce and extend the decision evidence

Completed 2026-09-22.

- The snapshot column list was extended before any build consumed it with
  `photometry_primary.ra`, `dec`, and `id_specz_khostovan25` (required for
  the P-08 defective-path reproduction on its documented all-links basis).
  The re-captured manifest SHA-256 is
  `06b19654fc715106ba1f788b52e084df1e94043343517f2b8a49fd44abfff7a4`; the
  superseded first manifest's diagnostic evidence is preserved in this
  paragraph (first manifest `48671278...`, photometry digest then
  `65d72042...`). This is a pre-seal export replacement, not a destructive
  rebuild: no build output existed.
- `src/features/specz_science/verify.py` re-derives every prior from the
  captured snapshot independently of the P2R-04 generators and the 5.4
  builders. All priors reproduced exactly on first computation, including
  the defective-path median (4,054.3415558937 arcsec vs the recorded
  4,054.341555894), the full 17-row prior table, and the v0.2
  qualified-before-type cross-tab (19,419; type 0/1/2 = 18,473/349/597;
  broad-line 71/2/188).
- Structural results: `_unique` == `_all`@Priority 1 across all 31 non-key
  native fields over 261,975 rows (identifier-lookup join); per-surface
  unrecognized-flag bound reproduced (flag 5 @ 90 in both surfaces, 6/10 @
  -99, confidence-zero categories, -3 in `_all` only, nothing >= 95); zero
  mapping inconsistencies among flag-domain/conf-range entries (272,909 in
  `_all`); secure preferred population 20,100 with 681 P-04 vetoes.
- Durable evidence: `docs/research/specz-science-p2r05/evidence-5-3.md`
  (tracked) and `staging/derived/specz-p2r05/priors-5-3.json` (staging).
- Hostile fixtures: `tests/test_specz_science_verify.py` (11 tests) —
  shuffled/non-contiguous/colliding identifiers, tampered-equality
  detection, single-`_unique` + conflicting secure Priority 0 detection,
  population-A structural zero with no neighbour claim, tie-break and
  invalid-confidence ordering, Priority 0 never preferred, manual
  defective-median haversine check, per-surface unrecognized bound,
  B-count/enumeration reconciliation, historical rule boundaries, and the
  0.005 threshold boundary with the float caveat verified empirically
  (zero production pairs within ulps of the threshold).

Gate 5.3 validation checklist: all five items satisfied; discrepancies:
none.

---

## Gate 5.4 — Build the complete measurement and source products

Completed 2026-09-22.

- `src/features/specz_science/canonical.py`: canonical JSONL serialization
  (sorted keys, declared row order), streaming digests, run identity over
  policy digest + snapshot digests + implementation module bytes and
  dependency versions (closeout commit deliberately excluded), and the
  three-domain content digest document.
- `src/features/specz_science/build.py`: measurement audit records (32
  native fields untouched plus derived association status, resolved catalog
  id, `_unique` membership, numeric/quality predicates and reasons) and
  source summary records (preferred entry with tie provenance, entry
  counts, A/B membership, three independent conflict flags with resolvable
  witness records, classification evidence, broad-line/QSO evidence,
  mask/blend context, pre-split eligibility bases, and overlapping
  exclusion reasons). Split-dependent eligibility fields are null here by
  design; `finalize_eligibility` applies the P-06 gate at 5.5.
- `src/features/specz_science/pipeline.py --phase build`: run id
  `a956dca27a3fe9dacd0ad3d522ee27bfada11a5eadb1cc3e69a1ae4433b5a1f7`;
  482,579 measurement rows; 784,016 source rows; zero
  unresolved-identifier entries (no contract discrepancy on this hold);
  measurements content digest
  `e494df8a6d7ec610545406fa2da14bd4559ec537521b4e3e2920593b71076933`.
- `src/features/specz_science/check_build_agreement.py`: full-data
  independent comparison against the verify.py restatements over the
  complete snapshot — key-set equality both products, preferred-entry and
  tie-list agreement for every source, conflict-flag agreement, population
  A/B agreement (1,032 / 185), no Priority 0 preferred, native-field
  fidelity for every audited entry. Status OK. One verifier defect was
  found and fixed during this check: `conflict_flags_independent` had
  iterated only `_unique` groups and missed population-A sources for the
  audit-only `other_measurement_disagreement` flag (129 sources); the fix
  widens its domain to the union of both group maps and all 5.3 priors
  were re-verified unchanged afterwards.
- Baseline pre-split bases: primary-galaxy 18,402; separate-validation
  668; vetoed sources 722; corroboration: singly 11,490, multiply 8,357,
  conflicting 671, not assessable 763,498.
- Tests: `tests/test_specz_science_build.py` (36 tests) — z failure modes,
  flag categories including 0/10/unrecognized, secure conjunction and
  named block reasons, native/derived separation, association statuses,
  zero/one/multiple representatives, tie-break and invalid-confidence
  ordering, copy-not-average, conflict boundaries and vetoes (secure
  alternatives veto; low-quality demoted disagreement does not),
  witness resolution, classification routing and reasons, broad-line
  routing and numeric-validity requirement, flag_star inertness for
  classification/eligibility, population A reasons, mutual exclusivity
  across the fixture zoo, and the split gate in finalize_eligibility.

Gate 5.4 validation checklist: all six items satisfied.

---

## Gate 5.5 — Freeze assignments and finalize eligibility

Completed 2026-09-22.

- `pipeline.py --phase finalize` regenerates all three products under one
  run identity `2bb71fb075cb5bd72a8f28908765bc8e0484c59f212a9e74ed26dbc06b333ae5`
  (a mid-run verifier repair had changed the implementation digest after
  the first 5.4 build; rather than ship mixed identities, finalize now
  rebuilds measurements in the same pass — the superseded pre-split
  artifacts remain in staging as diagnostic evidence, no sealed product
  was destroyed). Content digests: measurements
  `1086a118ec4bd6c4...`, sources `31c6179385bb9f21...`, splits
  `52313bb4095d3a4d...` (full values in
  `staging/derived/specz-p2r05/products/finalize-summary.json`).
- Tile map: canonical digest
  `c6406d37e32e4b5cfeb89fc91cda0eb9ed4abf0a192d8c5ab7e56fb893635937`;
  tracked artifact `docs/research/specz-science-p2r05/tile-map.md`.
  Holdout A1, A7, B3, B7; validation A3, A10, B1, B5; development the
  remaining twelve labels.
- Zero unassigned production sources (native tile domain check and the
  independent assignment reduction both). Source split counts:
  development 476,137, validation 147,721, holdout 160,158.
- Finalized eligibility: primary galaxy 18,402; separate validation 668;
  both true 0 (mutually exclusive). Eligible sources appear in all three
  partitions as the map dictates; no redistribution occurred.
- `check_splits_agreement.py`: independent SHA-256 map recomputation (no
  imports from the builder's splits module) matches the recorded map and
  every one of the 784,016 assignments; source/split agreement; the split
  gate applies exactly; mutual exclusivity holds.
- Tests: `tests/test_specz_science_splits.py` (8) — production map equals
  independent recomputation; invariance to ordering/batching/filtering;
  moved-source, changed-salt, and duplicate-assignment negative controls;
  injected null/out-of-domain tiles visible, ineligible, unredistributed;
  measurement-inherits-source; no-balance-redistribution.

Gate 5.5 validation checklist: all five items satisfied.
