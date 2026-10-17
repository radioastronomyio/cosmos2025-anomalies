---
title: "P2R-06a T_A v2 design repairs worklog"
description: "Gate checkpoints for the nine-finding repair amendment to the T_A v2 design contract"
author: "Kilo (Claude)"
date: "2026-10-16"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: [astronomy, feature-engineering, sed-fitting, spectroscopy]
  agent: "kilo"
  runtime: "Kilo CLI"
  runtime_version: "unreported"
  model: "kilo/zai-coding/glm-5.3"
  hostname: "ML01"
  spec_ref: "/opt/agents/repos/spec/2026-10-05-cosmos2025-spec-p2r-06a-ta-v2-design-repairs.md"
  repo: "cosmos2025-anomalies"
  category: "astronomy"
  duration_seconds:
  token_usage_source: "unavailable"
  tokens_total:
  tokens_input:
  tokens_cached:
  tokens_output:
  tokens_reasoning:
  cost_basis:
  cost_usd:
  priced_date:
  related_documents:
    - "../AGENTS.md"
    - "../docs/research/ta-v2-design/README.md"
    - "../work-logs/worklog-2026-10-05-p2r06-ta-v2-design.md"
---

# P2R-06a: T_A v2 design repairs

## Summary

| Attribute | Value |
|---|---|
| Status | In progress; gate checkpoints appended below |
| Agent | Kilo CLI / kilo(zai-coding glm-5.3) |
| Host | ML01; Python 3.12.3 via `/opt/agents/venv`, pytest 9.0.2 |
| Authorization | Don, Action Registry `recdrZoPWx6IaizkN` (2026-10-16 17:44 EDT: "Write it, GPT will review before running. Approved, execute."); spec v1.2 after GPT-6 pre-run review (v1.0→v1.1 changes; v1.2 lifecycle-only) |
| Starting branch/base | `main` / `156cb9eee863a9fabd14e9f828991042fbe59d4b` (merge of PR #6) |
| Execution branch | `task/p2r06a-ta-v2-design-repairs` |
| Operator interactions | None; the run put no question to the operator (empty record) |

Objective: repair the nine PR #6 review findings (R1-R9), bind Don's five
2026-10-16 design decisions as `proposed_not_adopted` contract material, and
refresh the review surface with TA2-Q07/Q08, without fitting, ranking,
database writes, or any newly computed real-data statistic.

## Startup preflight (spec-startup, before A1.1)

- Lifecycle skills resolved from `/opt/agents/repos/local-agent-skills/skills/`
  (`spec-startup`, `spec-closeout`); closeout identity verified as ML01's
  (astronomy-coding-bot trailer; `/opt/agents/repos/work-logs/work-registry.csv`
  registry). Shared venv active (`/opt/agents/venv`, Python 3.12.3,
  pytest 9.0.2).
- Repo tested with `git rev-parse --is-inside-work-tree` first: true. Tree
  clean (`git status --short` empty) on `main`.
- `main` == `origin/main` == `156cb9eee863a9fabd14e9f828991042fbe59d4b`; PR #6
  state MERGED with that merge commit (`gh pr view 6`). Regression baseline
  `d4bc1a240c0b6b874e875164896e5a5791af69c8` confirmed ancestor; `git diff
  d4bc1a2 main -- docs/research/ta-v2-design/ src/inspection/validate_ta_v2_design.py
  tests/test_ta_v2_design_contract.py` empty (baseline files byte-identical).
  No pre-existing `task/p2r06a*` branch. Parent branch `task/p2r06-ta-v2-design`
  preserved.
- Amendment branch `task/p2r06a-ta-v2-design-repairs` created from `main`
  (parent merged, so the spec's new-branch instruction governs over the
  reuse-parent-branch default).
- Queue spec startup digest recorded:
  SHA-256 `77c612032c0e251c2ddbd45fb0b4746c323a5ae0d0aac60d4e9ef7378f466871`
  (`/opt/agents/repos/spec/2026-10-05-cosmos2025-spec-p2r-06a-ta-v2-design-repairs.md`,
  60,363 bytes). Archive copies at closeout must match these bytes.
- In-repo parent archive verified: `spec/2026-10/2026-10-05-cosmos2025-spec-p2r-06-ta-v2-design.md`
  SHA-256 `04bb896050114207491603f7fc08971b59be274501454532e5c7ed6e5f42ecf0`,
  equal to the digest recorded in `input-identity.json`.
- Scratch baseline captured under gitignored
  `staging/2026-10-16-p2r06a-execution/baseline-d4bc1a2/` via `git show
  d4bc1a2:` exports (validator SHA-256
  `3c853da841bd2bb0990e9518f02dc38e82f5fb4db399e5e095ea2f7584a74234`;
  contract SHA-256
  `81fcf301026d8097d6ab921d1c68b713b8696184a711e4f685460c942f0f8df2`).
  R6 pre-evidence already visible in the baseline: the recorded command in
  `validation-results.json` at `d4bc1a2` is
  `python /opt/agents/repos/cosmos2025-anomalies/docs/src/inspection/validate_ta_v2_design.py`
  — a path under `docs/src/` that does not exist in the repository.

## Gate A1.1: exposure record and query rule

- Created `docs/research/ta-v2-design/exposure-log.md` (frontmatter clean
  under `check_frontmatter.py`) with the three required sections:
  1. Pre-partition diagnostics: frozen project-state inputs restated by
     reference; the 2026-07-10 (v1 baseline) and 2026-09-01 sessions
     transcribed as coordinator-reported history with unknown coverage
     stated explicitly (v1/v1.1 boundary; no per-tile inference; rerun
     prohibited; untouched-holdout claim unavailable).
  2. 2026-10-16 coordinator queries CQ1-CQ8 with SQL and result text
     reproduced from the spec's Appendix A, labeled coordinator-reported
     executions, each with the design change it motivated, plus the
     required distinctions: 160,158 is the whole holdout partition, not
     the CQ2/CQ5 eligible denominator; CQ2 (758,304 single-code) and CQ5
     (634,845 both-code) populations distinct and not contract
     eligibility; CQ6 zero counts do not establish absence of
     missing/non-finite quantiles; CQ5's r ~ -0.30 bounds nothing.
  3. Prospective rule: development-only default for any exploratory query
     computing a T_A output (including context) or combining both codes'
     estimates; exact `catalog_id` join, inherited `run_id`
     `1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c`,
     `assigned_split = 'development'`; no unqualified runs, no missing
     assignments; only the two separately authorized protocol-bound
     exceptions (validation evaluation of frozen choices; one-time
     holdout final evaluation), neither authorizing new exploratory
     choices or fitting; design-influencing covariate-only/single-code
     counts logged without waiving the A1.5-only source-read boundary.
- `evaluation-protocol.md` now links the exposure log and states that
  design was informed by full-catalog summaries containing holdout
  information; no unexposed-holdout claim; future parameters
  development-only; holdout assessment not an untouched test of
  feature-family selection; TA2-Q08 named as the acceptance surface.
- No query was executed in this gate (no database connection of any kind
  was opened).

Validation (gate A1.1 checklist):

- [x] Byte-for-byte comparison of SQL **and** result text recorded:
  `staging/2026-10-16-p2r06a-execution/transcription/extract_appendix_a.py
  verify` reports `CQ1..CQ8: sql == spec, result == spec` for all eight
  blocks and `VERDICT: BYTE-FOR-BYTE IDENTICAL (sql and result text)`
  (ML01-local, gitignored; verdict quoted inline here).
- [x] Query-specific populations stated distinct from CQ8's partition
  totals and from the repaired eligibility contract (exposure-log
  section 2.1).
- [x] Prospective rule names the exact join/run/split requirements and
  permits only separately authorized, protocol-bound validation/final
  evaluation exceptions (section 3).
- [x] No protocol or review claim asserts an unexposed holdout or zero
  historical outcome-derived exposure (protocol edit asserts the
  opposite, affirmatively).
- [x] No query was executed in this gate.

Gate A1.1 checkpoint: this commit.

## Gate A1.2: population gating and SFR scale states (R2, R3, R8)

Old-behaviour evidence (adapter
`staging/2026-10-16-p2r06a-execution/regression/adapter_a12_r2r3r8.py`,
ML01-local; values inline here, JSON evidence in the staging tree):

- **R3:** type-0 record, `mass_med` 10.0, `cigale.mass` 1e9,
  `cigale.mass_err` NULL → d4bc1a2 gives `pop_mass = True` with finite
  `residual_mass_dex = 0.8` (score NULL only because sigma components were
  absent). Same for a negative error. Repair: predicate
  `lephare.type == 0 AND mass_point_state == point_valid AND
  is_null(cigale.mass_err) == false AND cigale.mass_err >= 0` →
  `pop_mass = False`, `pop_mass_reason = not_in_population`, residual/score
  NULL, raw `delta_mass_dex = 1.0` retained.
- **R8:** type-1/2/99 records with valid masses and error → d4bc1a2 gives
  `residual_mass_dex = 0.8`, `score_mass = 3.334941328289389`. Type-1 SFR
  record → `residual_sfr_100_dex = -0.10102999566398119`,
  `score_sfr_100 = -0.356146931659015`. Repair: all NULL with
  `not_in_population`; raw deltas retained (1.0 and 0.1989700043360188).
- **R2:** rel-err 0.31 → d4bc1a2 `score_sfr_100 = -0.32252189801487147`
  with `sfr_100_scale_state` never emitted (the declared SFR scale machines
  were not evaluated at all); reversed quantiles →
  `-0.356146931659015`; median outside ordered endpoints (l68 0.3 ≤ u68
  0.45 < med 0.5) → `-0.4705613149408535`. Repair: scale machines now run
  and emit state/reason (`approximation_out_of_domain` /
  `quantile_order_violation` / `median_outside_quantile_interval` /
  `nonfinite_uncertainty_input` / `missing_uncertainty_input`), scores NULL,
  eligible residuals retained.
- **Boundary controls pass on both sides:** rel-err exactly 0.30 →
  `score_sfr_100 = -0.324429488725637` on d4bc1a2 and after repair
  (identical to 1e-12); 0.29 → `-0.3263071119761467` both; member mass
  delta/residual/score numerically identical.

Repairs:

- `feature-contract.yaml` → version `0.2.0-proposed`; `guard_precedence`
  declaration (population → point domain → scale/uncertainty → arithmetic;
  zero residual never bypasses an earlier guard); POP-MASS predicate gains
  the error conditions with an `input_contract_echo` field; median-
  containment and non-finite rules in all three scale machines;
  `pop_mass_reason`/`pop_sfr_inst_reason`/`pop_sfr_100_reason` outputs;
  `population_gate` fields on residuals and scores; `guards` lists on
  scores; `score_sfr_inst_state/reason` and `score_sfr_100_state/reason`
  outputs; `score_mass_state` domain gains `not_in_population`.
- `validate_ta_v2_design.py`: `evaluate_case` rewritten around the declared
  precedence; population membership and output gating read the contract's
  declared predicates/`population_gate`/`guards` (scratch mutations of
  those declarations change behaviour and are caught); SFR scale machines
  evaluated and emitted; `_Symbol` resolution for bare state-value tokens
  in predicates; `pop_mass_consistency()` compares the predicate and echo
  against the input-contract.md POP-MASS row (R3 drift check); structural
  requirements `population_gate_missing` and `guard_missing`; new mutation
  kinds (`edit_population_predicate`, `edit_pop_mass_echo`,
  `remove_output_field`, `edit_output_guards`,
  `drop_machine_rule_matching`).
- `fixtures.json`: 14 new cases (FX-R3a/b, FX-R8a-e, FX-R2a-g) and
  mutations M10-M15; the eight membership-expecting legacy records
  (FX-02a/b/c1/c2/d, FX-04a/b/c) gained a valid `cigale.mass_err`
  (2e9) so their expectations remain population-membership claims under
  the repaired predicate; `delta_mass_dex` expectations unchanged
  (bit-identical on controls, e.g. FX-01a = 1.0, FX-R8a = 1.0).
- `tests/test_ta_v2_design_contract.py`: `TestA12PopulationAndScaleGates`
  (7 tests) + MUTATIONS extended to M15.

Validation (gate A1.2 checklist):

- [x] Each defect-revealing fixture fails against `d4bc1a2` behaviour
  (adapter old-side assertions on existing fields: pop_mass True,
  residual 0.8, scores -0.3225/-0.3561/-0.4706) and passes after repair;
  boundary controls (FX-R2b/c, FX-04, FX-02f) pass on both.
- [x] Mutations caught with intended reasons, 15/15: error clause removed
  (M10 → case_mismatch:FX-R3a:pop_mass); population gate removed from
  residual emission (M11 → population_gate_missing:residual_mass_dex); SFR
  score gated on point state only (M12 →
  case_mismatch:FX-R2a:score_sfr_100); SFR population gate removed (M13 →
  population_gate_missing:residual_sfr_100_dex); artefact disagreement
  (M14 → pop_mass_echo_drift:error present and ≥ 0); median-containment
  check removed (M15 → case_mismatch:FX-R2e:score_sfr_100).
- [x] `delta_mass_dex` bit-identical on finite point-domain-valid audit
  controls (adapter CTL_member_mass delta/residual/score equal to < 1e-12;
  FX-01a unchanged); new non-finite/domain-invalid cases fail closed
  (FX-R2g nonfinite_uncertainty_input).

Full run: `python src/inspection/validate_ta_v2_design.py` (results to
scratch): cases 42/42, fit requests 4/4, mutations caught 15/15, exit 0.
`pytest tests/test_ta_v2_design_contract.py -v`: 38/38 passed.

Gate A1.2 checkpoint: this commit.

## Gate A1.3: directional LePhare half-widths (R9; decision 2)

Old-behaviour evidence (adapter
`staging/2026-10-16-p2r06a-execution/regression/adapter_a13_r9.py`):
on an asymmetric posterior (med 10.30, l68 10.25 → lo 0.05, u68 10.60 →
hi 0.30) d4bc1a2 emits `sigma_mass_lp_dex = 0.175` for both residual
signs and scores `+0.49567888926745` (positive residual) and
`-0.49567888926744835` (negative residual). After repair the same
records give `+0.891740157358414` (lower side 0.05 selected) and
`-0.31610854496087415` (upper side 0.30 selected), each matching an
independent full-precision oracle to 1e-9 and differing from the old
symmetric values by > 1e-6.

Repairs:

- `feature-contract.yaml` scales section rewritten: `sigma_mass_lp_dex`
  and `sigma_sfr_lp_dex` removed; `sigma_*_lp_lo_dex = med - l68` and
  `sigma_*_lp_hi_dex = u68 - med` added; `width_selection` declares
  `directional_by_residual_sign` with the zero-residual both-widths rule;
  `sigma_sys_*` gains parameter domain (finite, nonnegative), the
  directional-scale MAD determination rule, and a complete solve policy
  (bisection on [0, 10], tolerance 1e-10, max 200 iterations, interval
  tolerance 1e-12, `zero_residual_spread` / `no_admissible_systematic_solution`
  / `sigma_sys_solve_failed` unsupported results; never a negative floor,
  never the historical constants). New declared constants:
  `sigma_sys_solve_tolerance`, `sigma_sys_max_iterations`,
  `sigma_sys_search_upper_dex`, `sigma_sys_interval_tolerance`. Score
  guards gain `directional_width`; score state domains gain
  `degenerate_quantile_width`; structural check forbids any residual
  symmetric `*_lp_dex` output.
- `validate_ta_v2_design.py`: `select_width`/`evaluate_directional_score`
  (side by conditionally centered residual; zero residual requires both
  widths strictly positive; selected width strictly positive; missing/
  negative/non-finite never scored; policy read from the contract so
  policy mutations change behaviour); `solve_sigma_sys` implementing the
  declared deterministic policy; solve checks integrated into
  `run_validation` and the results payload; mutation kind
  `edit_scales_policy`.
- `fixtures.json`: nine new cases FX-R9a-i (asymmetric both signs;
  opposite-sign delta -0.10 vs residual +0.11 selecting the residual side
  with score 0.9820018620764585 where the wrong side would give
  0.3477677796067538; zero-width selected side degenerate; zero-width
  unselected side finite; zero residual with valid widths → score 0;
  zero residual with zero width degenerate; mass median-outside
  containment; SFR directional selection), scenarios SYNTH-C0B and
  SYNTH-C1C (exact-representable zero residual), `sigma_sys_solve_checks`
  SOLVE-1 (analytic oracle 0.3569053410920044 = sqrt((1.4826·0.25)² −
  0.01)), SOLVE-2 (no_admissible_systematic_solution), SOLVE-3
  (zero_residual_spread); mutations M16 (symmetric average restored),
  M17 (side by raw delta), M18 (zero-width guard removed). FX-02f
  expectations updated to lo 0.24/hi 0.16 and the resulting score
  -0.7702956124344129 (residual -0.16 selects hi); FX-05a lo/hi 0.2/0.2
  with the score unchanged (1.586322143174101). M15's intended reason
  updated to the discriminating observation
  (`case_mismatch:FX-R2e:sfr_100_scale_reason`): with directional widths
  the removed containment rule surfaces through the scale state/reason,
  while the directional guard independently fails the negative width.
- `scientific-design.md` section 3.3 rewritten for the directional
  half-widths, complete containment, non-finite rejection, the solve
  policy status (TA2-Q02), and the CQ6 qualification.
- `tests/test_ta_v2_design_contract.py`: `TestA13DirectionalWidths`
  (5 tests) + MUTATIONS extended to M18.

Validation (gate A1.3 checklist):

- [x] Asymmetric-score and wrong-side assertions demonstrate the old
  symmetric behaviour numerically (adapter; values above). New width
  fields have explicit expected values (FX-R9a/b/i, FX-02f, FX-05a);
  mutations fail for their intended reasons, not API absence (M16/M17
  behavioural through the policy field; M18 behavioural
  case_mismatch:FX-R9d plus guard_missing:score_mass:directional_width).
- [x] Mutations caught: symmetric average restored (M16 →
  case_mismatch:FX-R9a:score_mass); side chosen by raw delta (M17 →
  case_mismatch:FX-R9c:score_mass); zero-width guard removed (M18 →
  guard_missing:score_mass:directional_width).
- [x] Raw deltas and eligible residuals remain available when only the
  scale is unsupported (FX-R2a residual retained; FX-R9h delta retained);
  synthetic no-solution and zero-spread cases exercise the declared
  policy (SOLVE-2/3).

Full run: cases 51/51, fit requests 4/4, sigma_sys checks 3/3, mutations
caught 18/18, exit 0. `pytest`: 46/46 passed.

Gate A1.3 checkpoint: this commit.

## Gate A1.4: sSFR component view and non-additivity context (R1; decision 1)

Old-behaviour evidence (adapter
`staging/2026-10-16-p2r06a-execution/regression/adapter_a14_r1.py`): on
the unchanged FX-06a record d4bc1a2 emits
`delta_ssfr_100_dex = 0.6989700043360187` while its own declared coupling
`delta_ssfr_100_dex == delta_sfr_100_dex - delta_mass_dex` requires
`0.1989700043360188`; gap `0.49999999999999994` dex, and no check
enforced the coupling. After repair the same record gives
`0.1989700043360188` (== `0.5 - log10(2)`, matching the coupling to
<= 1e-12) plus `ctx_lp_ssfr_nonadditivity_dex = 0.5` (= -9.0 - (0.5 -
10.0)), with `score_ssfr_100` still NULL.

Repairs:

- `feature-contract.yaml`: `delta_ssfr_T_dex` rewritten to the component
  formula `(lephare.sfr_med - lephare.mass_med) - (log10(cigale.sfr_T) -
  log10(cigale.mass))`, kind `derived_view`, `rankable: false`, emitted on
  the parent raw-delta states (`ssfr_inst_view`/`ssfr_100_view` machines
  replace the native-sSFR-keyed gates); machine-readable `coupling_expr`
  per view; new context output `ctx_lp_ssfr_nonadditivity_dex`
  (`context_only`, never a predictor/ranking input, description states it
  is a difference between LePhare summary estimators, interpretation guard
  denies bimodality/degenerate-fit/physical-cause claims) with its own
  `ctx_lp_ssfr_point` machine; `pop_ssfr_*` driven by parent states;
  forbidden dependency `no-native-ssfr-in-rankable`.
- `validate_ta_v2_design.py`: `check_algebraic_couplings` evaluates every
  declared `coupling_expr` on every fixture where both sides are defined at
  absolute tolerance 1e-12 (split at the `==` node; exact-equality or
  numeric tolerance); `run_math_counterexamples` implements MATH-1
  (bisection solve of exp(-m)(1+m) = 1/2; median non-additivity
  2*ln2 - m = -0.29205262889677 for the unimodal log-concave Exp(1)
  construction); structural checks `context_output_rankable`,
  `native_ssfr_in_rankable_formula`, `native_ssfr_in_delta_formula`;
  CANONICAL_DELTA_FORMULAS updated to the component formulas; mutation
  kinds `set_output_coupling`, `set_output_field`.
- `fixtures.json`: FX-06a/FX-06b expectations rewritten to the component
  values; FX-R1a (inst view with nonzero delta_mass: view = -0.10102999566398196
  = 0.1989700043360188 - 0.3, discriminating the false-coupling mutation),
  FX-R1b (native equals component → context 0), FX-R1c (absent native →
  context NULL, view survives), FX-R1d (out-of-domain native → same);
  MATH-1 counterexample (m = 1.6783469900166605, non-additivity
  -0.29205262889677, analytic, no sampled data); mutations M19
  (native formula reinserted), M20 (false coupling: sum instead of
  difference, caught on FX-R1a), M21 (ctx marked rankable).
- `input-contract.md`: row-7 semantics note — the component view and the
  context-only role of `lephare.ssfr_med`, with the MATH-1 result inline.
- `scientific-design.md` section 4.3 rewritten: rationale, the enforced
  coupling, the context field's guard, the deterministic unimodal
  counterexample, and the CQ2 exposure-context qualifier.
- `tests/test_ta_v2_design_contract.py`: `TestA14SsfrComponentView`
  (5 tests) + MUTATIONS extended to M21.

Validation (gate A1.4 checklist):

- [x] The rewritten FX-06a passes at full precision; the original
  native-sSFR formula on the unchanged record violates the coupling
  numerically (adapter: gap 0.5 dex on d4bc1a2 outputs); the repaired
  component formula agrees to 1e-12. Both timescales tested (FX-R1a inst;
  FX-06a/b 100) and native-sSFR-independent eligibility (FX-R1c/d).
- [x] Mutations caught: native `ssfr_med` reinserted (M19 →
  case_mismatch:FX-06a:delta_ssfr_100_dex, plus
  delta_formula_identity and native_ssfr_in_delta_formula); false
  coupling declared (M20 → algebraic_coupling_violated:delta_ssfr_inst_dex:FX-R1a);
  ctx marked rankable (M21 → context_output_rankable:ctx_lp_ssfr_nonadditivity_dex).

Full run: cases 55/55, fit requests 4/4, sigma_sys checks 3/3, math
counterexamples 1/1, mutations caught 21/21, exit 0. `pytest`: 54/54
passed.

Gate A1.4 checkpoint: this commit.

## Gate A1.5: C1 binning and center support (R7; decision 3)

Old-behaviour evidence (adapter
`staging/2026-10-16-p2r06a-execution/regression/adapter_a15_r7.py`):
with support counts grafted onto a scratch scenario, d4bc1a2 returns
`center_support = "cell"` whenever a cell value is present — a 199-support
cell and a 199-support z-only bin both resolve as `cell`; support counts
do not exist anywhere in the old contract. After repair: 200 → `cell`,
199 → `z_fallback` (z-only 250), z-only 199 → `global_fallback`, with
`center_requested_cell` recorded (`0|1`, `1|0`).

Repairs:

- `feature-contract.yaml`: new declared constant `forced_highz_edge = 5.5`
  (`kind: declared_domain`; rationale cites the coordinator-reported
  slope reversal as a labelled prior finding NOT reproduced in this unit,
  observed against mean mass not the brightness covariate; additional
  fixed edges need a later named change); C1 entry gains machine-readable
  `z_quantile_bins: 6`, `mag_quantile_bins: 5`, the deterministic
  linear-interpolation `quantile_method`, `edge_conventions`
  (duplicate-edge collapse with effective-bin counts; forced edge only
  strictly inside the development support; hull never extended;
  left-closed/right-open with the final endpoint included so z = 5.5 is
  upper-bin and no cell straddles 5.5; missing/non-finite covariates
  unsupported), `support_enforcement: center_min_cell_support`, and the
  rewritten `support_rule` (unique-source counts; duplicated rows
  manufacture no support; requested cell + fallback both recorded; global
  fallback preserves no local high-z structure); new output
  `center_requested_cell`.
- `validate_ta_v2_design.py`: pure functions `_median`/`_quantile`/
  `_collapse_edges`/`_bin_index`; `partition_guard` (shared by every
  synthetic fitter: explicit development assignment, unassigned_partition,
  unknown labels, conflicts, duplicates, validation/holdout rejection);
  `build_center_from_rows` (reads declared contract parameters, no
  database path; expands deterministic synthetic row blocks); 
  `resolve_center_model` (support hierarchy); `evaluate_center` rewritten
  (support enforcement for declared scenarios; fitted-model resolution;
  requested-cell return); `run_binning_demonstrations` (with/without the
  forced edge); structural requirements `support_enforcement_missing`,
  `declared_constant_missing:forced_highz_edge`,
  `binning_parameters_missing`; mutation kinds `set_center_field`,
  `remove_declared_constant`.
- `fixtures.json`: legacy C1 scenarios carry declared support counts;
  `SYNTH-C1S` boundary scenario (200/199/199 + z-only 250/199);
  constructions CONSTR-1 (slope reversal: 11,520 below-3 rows, 1,200 in
  [3,5.5), 1,100 above with 220 per demo cell; quantile top bin [2.8, 7.7]
  split by the forced edge into [2.8,5.5)/[5.5,7.7]), CONSTR-2 (sparse
  high-z: 45/cell, z-only 225 → fallback with retained +0.024 bias),
  CONSTR-3 (support wholly below 5.5; duplicate edges collapse 6 → 4
  effective z bins; forced edge not inserted); `DEMO-SLOPE` demonstration
  (tolerance 0.005 declared before construction; with-edge max residual
  0.0 <= 0.005; without-edge min residual 0.048 > 0.005); cases FX-R7a-e,
  g-j (z exactly 5.5 → upper bin 6|2; max endpoint 7.7 included → cell;
  duplicate-edge fallback); mutations M22 (support counts ignored) and
  M23 (forced edge removed).
- **Optional support evidence (executed once):** the A1.5 development-only
  count ran through the analyst handoff. Role/session verification:
  `cosmos2025_v11_ro` on `cosmos2025_v11`; rolsuper f, rolcreatedb f;
  has_table_privilege source.lephare SELECT t / INSERT f / UPDATE f;
  analysis.specz_p2r05_splits SELECT t / INSERT f; session
  `transaction_read_only` reported `off` — read-only is enforced by role
  privileges, honestly recorded. 0 duplicate development assignments
  under run `1e604a81...`. Fixed audit bins declared in the SQL before
  execution (z: null/[0,1)/[1,3)/[3,5.5)/[5.5,8)/[8,inf); mag:
  null/[0,21)/[21,24)/[24,27)/[27,50)/[50,inf)); exact repaired POP-MASS
  point/error predicates only; sole aggregate `count(DISTINCT l.id)`.
  Counts (16 non-empty cells; e.g. d_z5.5-8|3_m24-27 = 3,005;
  d_z5.5-8|2_m21-24 = 98; full table in the exposure log section 4 and
  staging `support-audit/counts.txt`). No SFR column, no cross-code
  arithmetic, no estimate of any kind returned. One pre-execution
  connection error (unqualified table name) returned no data. The read
  influenced no bin edge or threshold; actual fitted-cell support remains
  unknown until P2R-07.
- `exposure-log.md` section 4 added with the SQL and counts verbatim;
  `tests/test_ta_v2_design_contract.py`: `TestA15BinningAndSupport`
  (5 tests, including direct partition-guard unit tests) + MUTATIONS to
  M23.

Validation (gate A1.5 checklist):

- [x] Mutations caught: support counts ignored (M22 →
  case_mismatch:FX-R7b:center_support + support_enforcement_missing);
  forced edge removed (M23 → case_mismatch:FX-R7d:residual_mass_dex +
  binning_demonstration:DEMO-SLOPE +
  declared_constant_missing:forced_highz_edge).
- [x] The support-boundary fixture fails against d4bc1a2 (adapter:
  199-support cells observed as `cell`) and passes after repair.
- [x] The optional query ran; its text and counts are in the exposure log
  and every listed constraint is satisfied by inspection, recorded above
  and in the worklog (single-code validity predicates only; fixed
  pre-declared bins; development-only join with run/split binding;
  distinct-ID counting; no estimates).

Full run: cases 64/64, fit requests 4/4, sigma_sys 3/3, math 1/1, demo
1/1, mutations caught 23/23, exit 0. `pytest`: 61/61 passed.

Gate A1.5 checkpoint: this commit.

## Gate A1.6: partition and identity fail-closed (R4, R5, R6)

Old-behaviour evidence (adapter
`staging/2026-10-16-p2r06a-execution/regression/adapter_a16_r4r5r6.py`):

- **R4:** on a training row whose catalog_id has no partition assignment,
  d4bc1a2 produces no rejection reason at all — the fixture's own
  `intended reason absent: unassigned_partition` note is the only text
  (the request itself is accepted; `assignment.get(cid)` returns None,
  not a blocked split). Repair: the shared `partition_guard` rejects with
  `unassigned_partition catalog_id 42`; FX-P5 added and passes.
- **R5:** a scratch identity whose authorizing-spec path does not exist
  produces zero authorizing-spec failures on d4bc1a2 (the `exists()`
  guard skips the comparison), and the live recorded central-queue path
  is absent after the parent closeout move, so the skip was live.
  Repair: `identity_missing:authorizing_spec:<path>` for the nonexistent
  path; a one-byte change to a referenced copy fails
  `identity_mismatch:authorizing_spec:<path>`.
- **R6:** the d4bc1a2 recorded command is
  `python /opt/agents/repos/cosmos2025-anomalies/docs/src/inspection/validate_ta_v2_design.py`
  — a `docs/src/` path that does not exist. Repair: results record the
  actual interpreter (`sys.executable`), the argv (JSON list, script
  resolved from the repository root), a shell-safe rendering, and the
  repo-relative script identity; `docs/src` no longer appears.

Repairs:

- `input-identity.json`: `authorizing_spec` (absolute central-queue
  path) replaced by the `authorizing_specs` manifest — the parent entry
  now references the in-repo archive copy by repository-relative path
  `spec/2026-10/2026-10-05-cosmos2025-spec-p2r-06-ta-v2-design.md`
  (SHA-256 `04bb896050114207491603f7fc08971b59be274501454532e5c7ed6e5f42ecf0`,
  unchanged from the recorded digest since the archive copy is
  byte-identical to the hashed queue file); an `amendment_pending` block
  records that the amendment becomes a required entry at A1.9 once its
  archive copy exists, so final validation cannot silently revert to
  parent-only checking.
- `feature-contract.yaml`: `identity_rule` rewritten (repository-root
  resolution, no working-directory dependence, no search-order fallback,
  no skip path) and `minimum_required_authorizing_specs` declared
  (parent path today; the amendment path is added at A1.9 with the
  transition recorded here and in the worklog).
- `validate_ta_v2_design.py`: `check_fit_requests` delegates to the
  shared `partition_guard` (the same guard every synthetic center, scale
  and covariance fitter uses); `identity_checks` rewritten for the
  manifest (schema validation, root-resolved paths,
  missing/mismatch/no-skip, contract-declared minimum checked against
  the identity so deleting a required entry or its digest fails);
  execution recording (interpreter/argv/shell-safe command).
- `fixtures.json`: FX-P5 (unassigned training ID, rejected with
  `unassigned_partition`); mutations M24 (required manifest entry
  deleted → `authorizing_spec_not_declared:spec/2026-10/...p2r-06...md`)
  and M25 (spec digest altered →
  `identity_mismatch:authorizing_spec:spec/2026-10/...p2r-06...md`).
- `tests/test_ta_v2_design_contract.py`: `TestA16PartitionAndIdentity`
  (7 tests): FX-P5 rejection; scratch identity with nonexistent spec
  path fails closed; required-entry deletion fails; command resolves
  from the repository root; **the recorded argv re-executes into a
  distinct scratch file with the same exit code, input hashes, case and
  mutation outcomes and semantic payload** (argv parsed as recorded
  JSON, never as shell text); the committed results bytes stay unchanged
  by reproduction runs; a non-root working directory still resolves
  identities. MUTATIONS extended to M25.

Validation (gate A1.6 checklist):

- [x] FX-P5 (training ID with no assignment) rejected.
- [x] Against d4bc1a2, a scratch identity whose spec path does not exist
  passes (zero authorizing-spec failures, adapter); after repair it
  fails with `identity_missing`, and a one-byte change to the referenced
  copy fails with `identity_mismatch`.
- [x] The recorded command re-executes into a different scratch output
  with the same semantic results; committed result bytes stay unchanged
  (test). Missing/altered files and deleted required manifest entries
  each fail (mutations M5/M24/M25 and the scratch-identity tests); a
  non-root working directory still resolves identities correctly (test).

Full run: cases 64/64, fit requests 5/5, sigma_sys 3/3, math 1/1, demo
1/1, mutations caught 25/25, exit 0. `pytest`: 70/70 passed.

Gate A1.6 checkpoint: this commit.

## Gate A1.7: joint mass-SFR candidate pair (decision 4)

New capability (no d4bc1a2 counterpart, so per spec section 6 the
discriminators are independent numerical oracles plus deliberately wrong
variants, not baseline API comparisons):

- **Kernel checks on stated matrices** (oracle fixtures, never feeding
  the per-source evaluator): correlation 0.8 gives (3,3) →
  3.1622776601683795 and (2.2,−2.2) → 6.957010852370437 (the off-pattern
  source outranks the on-pattern one); correlation 0 gives 3.5355339059327378
  and 3.4 with the surface emitted and no veto; mixture covariance
  [[3.4,−2.5],[−2.5,3.4]] gives (4,−4) → 2.328890038958328 and (3,3) →
  4.4721359549995805, recorded as the covariance-masking limitation
  (D outranks C on the joint surface while C's marginals exceed D's).
- **Analytic pooled-moment demonstrations:** two bins with internal
  correlation 0, means (1,−1)/(−1,1), unit variances, equal weights →
  pooled correlation −0.5; equal zero-mean unit-variance components with
  correlations −0.7 and 0 in a 50/50 mixture → −0.35, not −0.30.
- **Estimator (`winsorized-median-covariance-v1`, fully specified in the
  contract):** componentwise-median centering (spread estimation only;
  the distance keeps the fixed residual origin — disclosed), MAD
  marginals, winsorization at joint_winsor_c = 3.0, (n−1) covariance of
  the winsorized standardized vectors, correlation clamped to
  joint_rho_clamp = 0.95, C = diag(s)·R·diag(s) with no absolute
  dex-squared floor. Checks: CORE rho exactly 0.5 from ±1 patterns
  (counts 6/2/2/6); CONTAM (one (1000,1000) outlier) moves rho only to
  0.9260373689896785 (winsorized; a moment estimator would exceed 0.99);
  DEGEN (identical rows) → zero_marginal_spread; CLAMP-A: a supported
  cell with rho 19996/20000 = 0.9998 clamps to **exactly 0.95**;
  CLAMP-G: the global fit behind the sparse-cell fallback
  (rho_raw 0.9995501436922124) also clamps. Support hierarchy per
  timescale: cell/z-only at 200, global at 200, minimum 10 rows.
- **Evaluator (fits actually feed the scores):** FX-J4 under a fitted
  0.6-correlation, non-unit-scale cell: distance 1.1603624332797386
  (using C; using R instead — the M31 wrong variant — would give
  0.7846177413237612), score 3.075614166692078, fallback cell, support
  200, rho_effective 0.6, regularized false. FX-J5b (type-2): both joint
  outputs NULL not_in_population, raw mass delta survives. FX-J5c
  (relative error 0.31): distance stays valid, score NULL with
  log_error_approximation_domain_exceeded. FX-J5d/FX-J5e: valid
  inst/censored 100 and the reverse — each timescale independent, the
  valid surface emitted, the invalid one NULL. FX-J6: sparse cell →
  global fallback, rho_effective 0.95, regularized true, support 20010.
  FX-J7: zero spread → unsupported, never an invented covariance.
  FX-JP1/2/3: covariance fit requests with duplicate, unassigned, and
  validation-assigned rows all rejected by the shared partition guard.
- **Mutations M26-M33 caught 33/33:** low-correlation veto
  (joint_veto_declared); validation row in the covariance fit
  (joint_fit_partition:JOINT-1:inst:...999999...); marginal output
  removed (required_output_missing:sigma_sfr_cig_100_dex); joint
  population gate removed (population_gate_missing); clamp removed
  (joint_fit_check:CLAMP-A — the exact 0.95 assertion fails at 0.9998);
  full covariance replaced by unit-diagonal correlation
  (case_mismatch:FX-J4 — 0.7846 vs 1.160); estimator bypassed
  (joint_estimator_invalid); timescales incorrectly intersected
  (case_mismatch:FX-J5d).

Contract: `joint_surfaces` section (estimator, minimum support,
fallback hierarchy, degeneracy, fit population, interpretation guard
denying chi-square/p-value/significance/probability labels,
centers-and-coexistence disclosure including the CQ5 non-bound
statement, protocol status); four joint outputs + 16 state/reason/
support/fallback/rho/regularization outputs + `joint_covariance_model_id`;
forbidden dependencies `no-joint-veto`, `joint-matrices-require-fit`,
`joint-surfaces-preserve-marginals`; constants joint_winsor_c,
joint_rho_clamp, joint_min_cell_support, joint_min_global_support,
joint_min_covariance_rows; partition_use rules extended to the
covariance fitter. Protocol (evaluation-protocol.md): the pair added to
the declared comparison set as candidates requiring TA2-Q07 adoption;
section 10 predeclares the three separated criteria (synthetic
correctness; development-tile jackknife summaries; validation-tile
compositional description), forbids criteria rewarding elliptical
distance by construction, fixes top-K overlap mechanics (K and
lexicographic tie handling) in the approved future protocol, keeps tile
jackknife development-only, and records the evidence against adoption
(KERNEL-3 masking; POOLED-1/2 distortion) instead of inventing
thresholds.

Validation (gate A1.7 checklist):

- [x] All six fixture families pass with full-precision independent
  formula/moment oracles (1e-3 only for the spec's rounded examples
  3.162/6.957/3.536/3.400/2.329/4.472); fitter fixtures separately check
  a known core (rho exactly 0.5), contamination response (bounded),
  support fallback (CLAMP-G/FX-J6) and degeneracy (DEGEN/FX-J7);
  documentation claims no proof of robustness for arbitrary mixtures.
- [x] Mutations caught with their intended reasons (list above), 33/33.
- [x] Marginal outputs unchanged with joint outputs present (FX-J4
  residual identical; FX-R9a marginal score identical under the same
  contract).

Full run: cases 71/71, fit requests 5/5, joint fit requests 3/3,
sigma_sys 3/3, math 1/1, demo 1/1, kernel 5/5, joint fit checks 5/5,
mutations caught 33/33, exit 0. `pytest`: 84/84 passed.

Gate A1.7 checkpoint: this commit.

## Gate A1.8: naming restraint and declared limitations

- Structural naming restraint in the validator: output `name` and
  `description` fields may not contain "bimodal", "multimodal", "secure
  redshift", "true anomaly", or "significance"; `interpretation_guard`
  fields (which state what an output does **not** establish) are exempt.
  Current contract scanned clean: zero violations.
- Mutation M34 ("bimodality flag" inserted into the non-additivity
  context's description) caught with
  `naming_restraint:ctx_lp_ssfr_nonadditivity_dex:description:bimodal`;
  34/34 mutations caught.
- `scientific-design.md` section 9 and `review.md` "Declared limitations"
  added, each stating the four claims separately: shared-redshift
  dependence (T_A conditional on LePhare's redshift); no low-T_z
  redshift guarantee (a confident catastrophic photo-z can produce large
  T_A at low T_z; spec-z under the S5 conditions is the diagnostic);
  covariance masking (a fitted joint covariance can absorb a real rare
  population — KERNEL-3); median non-additivity is not bimodality
  (MATH-1's unimodal counterexample, non-additivity about -0.292).
- Tests: `TestA18NamingAndLimitations` checks the mutation, the guard
  exemption, and each limitation claim in both documents in context.

Validation (gate A1.8 checklist):

- [x] Mutation caught: "bimodality flag" inserted into a description
  (M34, naming_restraint failure; also asserted directly by test).
- [x] Both documents separately state all four claims; each checked in
  context by test (fragment-level assertions against both files), not by
  counting phrases.

Full run: cases 71/71, mutations caught 34/34, exit 0. `pytest`: 88/88
passed.

Gate A1.8 checkpoint: this commit.

## Gate A1.9: review surface, results, and closeout

- `review.md` reworked to v2.0: design identity (contract 0.2.0-proposed;
  regenerated counts: 71/71 cases, 5/5 fit requests, 3/3 joint fit
  requests, 3/3 solve checks, 1/1 math counterexamples, 1/1 binning
  demonstrations, 5/5 kernel checks, 5/5 joint estimator checks, 34/34
  mutations, exit 0; P2R-06a authority `recdrZoPWx6IaizkN` plus the
  parent merge `156cb9eee863a9fabd14e9f828991042fbe59d4b`); the withdrawn
  d4bc1a2 claims stated explicitly with what the repaired validation
  covers and does not; the eleven-comment PR #6 response table mapping
  each comment to R1-R9, the change, and its discriminating fixture or
  mutation; findings TA2-F01..F12 revised where the amendment changed
  their subject and new findings TA2-F13..F17 carrying the five
  2026-10-16 decisions (the forced z = 5.5 edge labelled as resting on a
  coordinator-reported prior finding not reproduced in this unit);
  TA2-Q01..Q06 retained with IDs and unanswered state plus a change
  table (no wording changes); TA2-Q07 and TA2-Q08 added verbatim from
  the spec.
- Spec archived: the queue spec moved to the central
  `/opt/agents/repos/spec/2026-10/` and copied in-repo to
  `spec/2026-10/2026-10-05-cosmos2025-spec-p2r-06a-ta-v2-design-repairs.md`;
  both copies SHA-256
  `77c612032c0e251c2ddbd45fb0b4746c323a5ae0d0aac60d4e9ef7378f466871`,
  equal to the startup digest recorded above (archive bytes match the
  frozen execution spec).
- Identity transition executed: `input-identity.json` gained the
  amendment entry (repo-relative archive path + digest, required: true,
  authority `recdrZoPWx6IaizkN`, 2026-10-16 17:44 utterance) and the
  contract's `minimum_required_authorizing_specs` gained the amendment
  path. **The amendment became required at A1.9 once its archive copy
  existed; final validation verifies both the parent and amendment
  manifest entries with no skip path** (validated by the final run and
  by M24/M25 remaining caught).
- `validation-results.json` regenerated by the final committed run
  (exit 0; command
  `/opt/agents/venv/bin/python3 src/inspection/validate_ta_v2_design.py`
  resolved from the repository root).
- Indexes updated: `docs/research/ta-v2-design/README.md` (v2.0,
  exposure-log row, TA2-Q08), `src/inspection/README.md`,
  `tests/README.md`, `docs/research/README.md`, `docs/README.md`,
  `spec/README.md`, `spec/2026-10/README.md` (amendment row; parent row
  notes the PR #6 merge), `work-logs/README.md` (amendment row).
- Parent worklog status-only correction applied (the explicit exception
  to the lifecycle's closed-parent rule): frontmatter
  `status: "in-progress"` → `status: "completed"` and the summary-table
  status cell updated, nothing else; the parent's gates, seal and
  registry row are unchanged. Justification: the parent unit closed at
  gate 6.5 with a stale status field (its closeout wrote the seal but
  left the in-progress markers); this correction is recorded here rather
  than reopening the parent's execution record.
- Offline test boundary inspected before running: the suite imports only
  stdlib + pytest + the repo's validator and runs the validator as a
  subprocess with `--results` redirected to pytest temp paths; no
  install, network, database, or sealed-product writer can run. No
  integration checks were excluded.

Validation (gate A1.9 checklist):

- [x] One commit per gate A1.1-A1.9 on `task/p2r06a-ta-v2-design-repairs`,
  each with the trailer block (table below); branch pushed; exactly one
  amendment PR open and unmerged, linking merged PR #6.
- [x] All applicable pure/offline tests pass: 88/88 pytest; validator
  exit 0 on the repaired contract; nonzero with the intended reason on
  every mutation named in the spec (34/34, including M10-M15, M16-M18,
  M19-M21, M22-M23, M26-M34); results record the command, input and
  contract hashes, and exit codes.
- [x] Each of R1-R9 has worklog evidence of a fixture or mutation failing
  on `d4bc1a2` with meaningful behaviour assertions (adapters quoted
  inline at gates A1.2-A1.6; R1's 0.5-dex coupling gap; R2's finite
  scores with unevaluated scale states; R3's membership without error
  validity; R4's accepted unassigned ID; R5's live skip on the absent
  recorded path; R6's `docs/src/` command; R7's any-present-cell
  resolution; R8's finite residual 0.8 / score 3.334941328289389 for a
  type-1 source; R9's symmetric 0.175 both signs). New capabilities (the
  five decisions) use independent oracles and deliberately wrong
  variants (M16-M34), never baseline API absence.
- [x] `git diff --name-only d4bc1a2..HEAD` contains only this
  amendment's section 5.2 allowlist: `docs/research/ta-v2-design/*`
  (exposure-log.md new; feature-contract, input-contract,
  input-identity, scientific-design, evaluation-protocol, fixtures,
  validation-results, review, README), `src/inspection/validate_ta_v2_design.py`,
  `tests/test_ta_v2_design_contract.py`, the seven interior indexes,
  the two worklogs (parent: status fields only), and the in-repo spec
  archive copy with `spec/2026-10/README.md` and `spec/README.md`.
  `docs/project-state.md`, the root `README.md`, `ROADMAP.md`,
  `src/README.md`, and the frozen parent-spec bytes are unchanged.
- [x] The in-repo and central archive copies of this spec have identical
  SHA-256 (`77c61203...`, verified at archive time and equal to the
  startup digest); `input-identity.json` verifies both authorizing specs
  with no skip path.
- [x] The registry row's `model` equals the `Model:` trailer
  (`kilo/zai-coding/glm-5.3`); the defect register records the ten
  parent entries (SD-1..SD-10) and the six section 8.1 pre-run entries
  (RV-1..RV-6) with correct attribution and no duplicated global IDs.
- [x] The handoff names TA2-Q01..Q08 and states that P2R-07, fitting,
  installation and publication await separate approval (Next steps
  below).

### Per-gate commits

| Gate | Commit |
|---|---|
| A1.1 | `5117546` |
| A1.2 | `343e459` |
| A1.3 | `2d48e67` |
| A1.4 | `f4b9c13` |
| A1.5 | `04d85e0` |
| A1.6 | `8057afd` |
| A1.7 | `c0e7887` |
| A1.8 | `6750c9d` |
| A1.9 | the commit carrying this closeout checkpoint |

## Files changed

| Surface | Change |
|---|---|
| `docs/research/ta-v2-design/` | Repaired contract package: exposure-log.md (new), feature-contract.yaml (0.2.0-proposed), input-contract.md, input-identity.json (manifest), scientific-design.md, evaluation-protocol.md, fixtures.json (71 cases / 34 mutations / kernel-fit-solve-math-demo checks), validation-results.json (regenerated), review.md (v2.0, TA2-F01..F17, TA2-Q01..Q08), README.md |
| `src/inspection/validate_ta_v2_design.py`, `src/inspection/README.md` | Repaired and extended validator + index |
| `tests/test_ta_v2_design_contract.py`, `tests/README.md` | 88-test suite + index |
| `spec/2026-10/`, `spec/README.md` | Amendment archive copy + indexes |
| `work-logs/worklog-2026-10-05-p2r06a-ta-v2-design-repairs.md` (new), `work-logs/worklog-2026-10-05-p2r06-ta-v2-design.md` (status-only), `work-logs/README.md` | Worklogs and index |
| `docs/README.md`, `docs/research/README.md` | Index rows |
| Central queue `/opt/agents/repos/spec/` | Spec moved to `2026-10/` month archive; registry row appended |
| staging (ML01-local, gitignored) | Baseline snapshot, adapters R1-R9 with JSON evidence, transcription verification, support-audit evidence; preserved, not deleted |

## Runtime facts

ML01; executor Kilo CLI, model `kilo/zai-coding/glm-5.3`; Python 3.12.3
via `/opt/agents/venv`; pytest 9.0.2; PyYAML. Elapsed time and token
usage unavailable from this runtime; recorded as such in the registry
row. No operator question was put during the run; the record is empty
(none was needed — the spec pre-decided every point that arose).

## Next steps

Handoff: Don answers TA2-Q01 through TA2-Q08 in
`docs/research/ta-v2-design/review.md`. P2R-07 (development-only
fitting) does not dispatch until Don answers TA2-Q01..TA2-Q08 on this
repaired review surface; fitting, installation, and publication all
await that approval and a later named unit. The amendment PR stays
unmerged until Don instructs the merge in his own words.

<!-- Agent: kilo; Runtime: Kilo CLI; Model: kilo/zai-coding/glm-5.3; Session: interactive -->
