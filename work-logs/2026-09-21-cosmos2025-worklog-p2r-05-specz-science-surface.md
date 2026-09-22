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
