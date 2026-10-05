---
title: "P2R-06 T_A v2 design worklog"
description: "Gate checkpoints for the T_A v2 scientific design contract unit"
author: "Kilo (Claude)"
date: "2026-10-05"
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
  spec_ref: "/opt/agents/repos/spec/2026-10-05-cosmos2025-spec-p2r-06-ta-v2-design.md"
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
    - "../docs/research/specz-science-p2r05/review.md"
---

# P2R-06: T_A v2 scientific design contract

## Summary

| Attribute | Value |
|---|---|
| Status | In progress; gate checkpoints appended below |
| Agent | Kilo CLI / kilo(zai-coding glm-5.3) |
| Host | ML01; system Python 3.12.3, pytest via `/opt/agents/venv` |
| Authorization | Don, Action Registry `rec4acLZWCuN1tJk9` (2026-10-05 09:13/09:15 EDT utterances); dispatched spec P2R-06 v1.0 |
| Remote-operation rule | AGENTS.md as of this base (`01f28ee`) says executors may push only their working branch and open/update its pull request; merges only on Don's explicit instruction. Spec section 4 anticipated a residual conflict at "AGENTS.md lines 72 and 106"; that text was already reconciled by fix-round commit `1244bf0` (PR #3), so no live conflict remains. Recorded here rather than editing AGENTS.md. |
| Starting branch/base | `main` / `01f28ee4...` (merge of PR #3) |
| Execution branch | `task/p2r06-ta-v2-design` |

Objective: deliver the proposed T_A v2 scientific design contract (input
contract, feature contract, synthetic validator, evaluation protocol, review
surface TA2-Q01..Q06) without fitting, adopting, or installing anything.

Lifecycle note: the spec references `spec-startup` / `spec-closeout` skills;
neither exists in this execution environment. The AGENTS.md work-spec
contract is followed directly, and the substitution is recorded here.

## Gate 6.1: authority, source semantics, and populations

### 6.1a: adoption-reference reconciliation (issues #4, #5)

Commit `433ffad`: updated `docs/research/README.md` (P2R-05 entry to
adopted-with-conditions) and
`docs/research/specz-science-p2r05/derived-schema-contract.md`
(`product_state` reconciled to conditional adoption while recording the
retained frozen value; v1.0→1.1), and appended a dated correction note to
`work-logs/worklog-2026-10-05-p2r05-adoption-answers.md` superseding the
changed-surface exclusivity claim (fix round `e50a0c9`..`7c5ca91` changed
`README.md`, `docs/project-state.md`, dispositions, P2R-05 review,
upstream draft, `AGENTS.md`, and work-log surfaces). History not rewritten;
commit carries `closes #4, closes #5`.

### 6.1b: input contract and identity record

- Prerequisite verified: S5 answers are on `main` in review.md ("Acceptance
  questions (answered 2026-10-05)", line 308 at base) and match spec
  section 3's table; answers recorded in the binding table with exact
  locators (Q01 line 321; Q02 323–337; Q03 339–376; Q04 378–385; Q05
  387–392).
- `docs/research/ta-v2-design/` created with interior README; input
  contract written (interface boundary; inherited identities recorded from
  tracked documents without refresh; 32-field inventory bound to dictionary
  evidence; populations POP-MASS / POP-SFR-INST / POP-SFR-100 /
  POP-SPECZ-PRIMARY / POP-SPECZ-SEPARATE / POP-AUDIT; frozen inputs
  restated; planned read set declared clean).
- `input-identity.json` records content hashes: spec `04bb8960...`,
  dictionary `324d3ea1...`, unit-conventions `8a4d3a72...` (equals the
  dictionary's pinned `semantic_note_source_sha256`), manifests, review.md,
  tile map, policy config; ML01-local adoption review `79d1fe50...` with
  the three numbers used from it stated inline (18,402/784,016; 90.80%
  F444W [15,24) primary; 12.22% catalog).
- Field-anchor verification against the sealed dictionary: LePhare
  `mass_l68/med/u68` at lines 312–314, `sfr_l68/med/u68` 315–317 (spec's
  anchors exact); CIGALE `sfr_inst[_err]`/`sfr_100myr[_err]`/`mass[_err]`
  at 526–531, `chi2_best_fit` 534, `chi2_red_best_fit` 535 (exact). Also
  verified: `type` 290, `chi2_best` 295, `nbfilt` 296, `ssfr_*` 318–320,
  `zfinal` 289 (candidate sentinel −99.0 × 92,226), `zpdf_med` 291 (none),
  zero `ssfr` rows for `cigale` in v1.1.
- Unsupported semantics declared at the input layer: no genuine censoring
  limits anywhere in source metadata (so `upper_limit_supported` is
  unreachable on this catalog); CIGALE error shapes undocumented; LePhare
  SFR timescale undocumented; no CIGALE sSFR column.
- Synthetic mass-only path rule declared (POP-MASS requires no SFR state);
  gate 6.3 will prove it with fixture FX-03.

Validation (gate 6.1 checklist):

- [x] Every proposed input exists by exact `source.table.column` name with
  dictionary/source evidence, units, representation, logical domain;
  missing/ambiguous semantics → explicit `unsupported` (four declared);
  no column relies on an inferred sentinel or implicit unit conversion.
- [x] Q01–Q05 table enumerates recorded answer, scope consequence, exact
  review.md locator; no `accepted` predicate is satisfied by a
  recommendation.
- [x] Mass-only synthetic path rule declared; discriminator fixture named.
- [x] Planned read set contains no v1 rerun, no observed residual, no
  holdout outcome, no manifest refresh.
- [x] Identity comparison rule declared (content compare; reject, never
  overwrite); enforced at gate 6.3.

Gate 6.1 checkpoint: this commit. Gate 6.1a commit: `433ffad`.

## Gate 6.2: scientific feature contract and recommended design

- `feature-contract.yaml` (56 outputs, 8 state machines, 9 forbidden
  dependency patterns, 2 center families, 2 scale groups): grain/key;
  declared constants separated into mathematical, declared-domain, and
  development-fitted kinds (ln10; LePhare log domain [-20,15]; CIGALE
  first-order log-error domain 0.3 relative; sfr_floor_k = 1.0; center
  min-support 200; zero-scale guard). Six explicit populations carried
  from gate 6.1. State machines: mass point/scale, sfr_inst/sfr_100
  point/scale, ssfr_inst/ssfr_100 gates — every required SFR state
  (`point_comparable`, `upper_limit_supported` declared unreachable on
  this catalog, `floor_or_censoring_suspected`, `nonpositive_log_undefined`
  with zero/negative reason split, `missing`, `invalid_or_unsupported`)
  present with ordered precedence and reasons.
- Mass outputs: raw `delta_mass_dex` with hidden-shift guard; center
  outputs `expected_delta_mass_dex`/`center_model_id`/`center_support`
  (C0 constant vs C1 binned median over zpdf_med × mag_auto_f444w, both
  development-only, neither fitted here); `residual_mass_dex` as the
  primary proposed ranking surface (rare deviations survive
  normalization); `score_mass` as secondary normalized residual with an
  explicit not-a-calibrated-significance guard; separate lp/cig sigma
  outputs with the approximation domain; sigma_sys by a development-only
  robust-spread rule (historical 0.1/0.2 dex floors are context only).
- SFR/sSFR: per-timescale paths, `timescale_caveat_lephare`, unscored
  `upper_limit_path` (no epsilon, no fabricated floor), declared
  algebraic coupling `delta_ssfr = delta_sfr − delta_mass`, and
  `score_ssfr_*` = `unsupported_correlated_errors` (NULL) because the
  mass–SFR error correlation is unknown.
- Fit context: three separately named chi-square passthroughs plus
  ctx_nbfilt, context-only, never predictors; no quotient under any name;
  no dof recovery.
- Partition use rules and S5-bound spectroscopic interface declarations
  included; forbidden covariate list for centers (any mass/SFR/sSFR
  estimate, chi2, spec-z fields, tile/survey identity, the target delta).
- `scientific-design.md`: rationale/identified-alternative/limitation/
  approval question for every choice above, the frozen-input → response →
  failure-case table, and the explicit non-goals.
- Sanity: YAML parses under `yaml.safe_load`; identity JSON parses.

Validation (gate 6.2 checklist):

- [x] Every state has a complete domain, precedence rule, and explicit
  output and reason; unsupported cases cannot default to a finite ranked
  value (first-match ordered machines; unreachable bound state declared).
- [x] Raw difference, expected center, centered residual, score, support
  flag, and model identity are separate outputs; a universal hidden shift
  is rejected by contract validation (hidden_shift_guard; enforced at
  gate 6.3).
- [x] Center and scale procedures specified with no fitted catalog
  coefficients and no observed residual/ranking distribution; no
  illustrative number appears outside labelled synthetic fixtures.
- [x] Changing SFR between positive, zero, and undefined leaves raw mass
  disagreement unchanged; censored/unsupported SFR cannot manufacture
  infinite or extreme ranked tension (separate populations + state
  machines; proved at gate 6.3 by FX-03/FX-04).
- [x] No chi2_ratio, inferred dof, independent-CIGALE-photo-z field, or
  mass-truth label among permitted predictors/targets; renaming is caught
  by the structural dependency check (gate 6.3).
- [x] Every scientific choice has rationale, alternative, limitation, and
  a linked approval question; none is marked accepted.

Gate 6.2 checkpoint: this commit.

## Gate 6.3: executable synthetic contract checks

- `docs/research/ta-v2-design/fixtures.json`: 28 synthetic cases (FX-01
  unit/sign/sentinel/nonpositive family; FX-02 centering cells, bias +
  isolated-deviation survival, out-of-hull fallback, quantile-order
  violation, full score path; FX-03 four SFR paths incl. the hypothetical
  documented-limit record that no rule may reference; FX-04 mass/SFR
  independence incl. negative-log-SFR point case; FX-05 inst score path;
  FX-06 sSFR coupling/gating/unsupported score; FX-07 context passthroughs;
  FX-08 non-galaxy routing), 4 fit requests (FX-P1..P4), 9 named mutation
  controls (M1..M9), all labelled `provenance: synthetic`.
- `src/inspection/validate_ta_v2_design.py`: pure validator — whitelisted
  safe expression parser (no eval), ordered state-machine evaluation with
  parent preconditions, synthetic center scenarios (C1 binned lookup with
  cell/z/global/out-of-hull support; C0 constant; S0 per-timescale),
  scale/score quadrature with the declared approximation domain and
  zero-scale guard, contract-formula-driven delta evaluation, structural
  dependency checks (chi2 quotient under any name, chi2 predictors,
  dof-from-nbfilt, invented CIGALE photo-z, truth labels, forbidden center
  covariates incl. specz/tile/survey, fit-request rule presence, required
  SFR states, unreachable bound state, fixture synthetic labelling,
  bound-field non-reference), and content-comparison identity checks
  (tracked-file hashes, spec-file hash when present, input-contract
  cross-anchors).
- TDD followed: tests written first and confirmed red (validator absent),
  then implementation to green. `tests/test_ta_v2_design_contract.py`: 26
  tests — clean-run assertions, per-mutation nonzero exits with intended
  reasons, no-op mutation control, boundary tests (no
  psycopg/socket/sqlite in source, no `src.etl` import, no `--mode`
  generation surface), fixture synthetic labelling, required-state and
  unreachable-bound declarations, identity content match, scratch identity
  rejection.
- Recorded run: `docs/research/ta-v2-design/validation-results.json` —
  cases 28/28 passed; fit requests 4/4 passed; mutations caught 9/9;
  exit 0. Command: `python src/inspection/validate_ta_v2_design.py`
  (contract/fixtures/identity SHA-256 values recorded inside).
- Indexes updated: `src/inspection/README.md` and `tests/README.md`.
- Environment note: `python3 src/inspection/check_frontmatter.py` reports
  20 violations, 19 of which pre-date this branch (P2R-05-era research
  docs using the `research`/`decision-record` type tags and work-logs using
  plain YAML frontmatter, matching their existing convention); the one new
  file in that class is this worklog, which follows the established
  work-log frontmatter style of the two most recent logs. All new
  `docs/research/ta-v2-design/*.md` files pass the checker. No pre-existing
  file was modified for the checker.

Validation (gate 6.3 checklist):

- [x] Validator exits 0 on the complete contract with every expected
  synthetic result within declared tolerance, and exits nonzero on each
  named mutation with the intended reason (9/9 recorded).
- [x] Results record correct cases and negative controls with stable case
  IDs, expected and observed behaviour, command, input and contract
  hashes, and exit codes.
- [x] No fixture is described as astrophysical validation, measured
  calibration, power estimate or real-data ranking (asserted by test).
- [x] Validator has no database connection, no installer import and no
  catalog feature-generation mode (asserted by tests and CLI surface).

Gate 6.3 checkpoint: this commit.

## Gate 6.4: evaluation protocol and review surface

- `evaluation-protocol.md`: preregistered plan separating non-spectroscopic
  disagreement characterization from the redshift diagnostics; split-use
  table implementing the Q04 conditions (development-only fitting,
  validation for declared choices with the C0 tie-break fixed in writing
  before outcomes, single holdout after the freeze checklist); declared
  comparison set (C0/C1 mass centers, S0 SFR centers, robust-spread
  scales; state constants explicitly not tuned); strata plan (redshift,
  magnitude, colour, survey, support); the three frozen sensitivity
  variants predeclared and never choice-driving; clustered tile+survey
  uncertainty with the four holdout tiles (A1, A7, B3, B7) and
  upstream-calibration independence stated as unestablished; support
  policy (explicit unsupported strata, no weighted extrapolation);
  separate-labelled diagnostics with the 16 tentative-only broad-line
  cases reported explicitly; descriptive vs model-affecting table;
  no outcome metric computed.
- `review.md`: design identity table; twelve findings TA2-F01..F12, each
  with statement, exact evidence locator (contract section, fixture, or
  mutation control), recommendation, limitation, and closed question;
  the six closed questions TA2-Q01..Q06 verbatim from the spec with
  per-question resolution pointers; propagation guarantees (Q03 population
  has no primary-fitting path; Q05 has no dependency edge); the truthful
  reduced-SFR-scope recommendation; and the explicit approve/does-not-
  authorize boundary.
- Frontmatter and interior README links verified for the new documents;
  every status says proposed/pending; no adopted claim or release promise.

Validation (gate 6.4 checklist):

- [x] Every question resolves to a concrete contract or protocol section
  and discriminating evidence; none asks approval of an unspecified
  threshold or algorithm.
- [x] Every frozen input maps to a design response and at least one
  failure case (TA2-F12; scientific-design.md section 7).
- [x] S5 conditions propagate exactly; the Q03 population has no path into
  primary fitting; Q05 has no dependency edge into scoring.
- [x] Metrics, strata, model-choice rules and support thresholds are
  specified before fitting; holdout results are absent.
- [x] The review truthfully recommends reduced SFR scope (TA2-F06).
- [x] Documentation has required frontmatter and interior README links and
  says proposed or pending; no adopted claim or release promise.

Gate 6.4 checkpoint: this commit.

## Gate 6.5: closeout

- Bounded `docs/project-state.md` entry added (links the proposed design as
  pending approval; frozen facts unchanged); `docs/README.md` research row
  updated; `spec/2026-10/` archive copy added byte-identical (SHA-256
  `04bb896050114207491603f7fc08971b59be274501454532e5c7ed6e5f42ecf0`),
  `spec/2026-10/README.md` and `spec/README.md` indexes updated;
  `work-logs/README.md` row added; this worklog sealed.
- Central spec moved to the central month archive
  `/opt/agents/repos/spec/2026-10/` (byte-identical; central archive
  authoritative), per the repo's existing pattern.
- Registry row appended to `/opt/agents/repos/work-logs/work-registry.csv`
  after the final commit, with `model` equal to the `Model:` trailer
  (`kilo/zai-coding/glm-5.3`).
- Remote operations (authorized by current AGENTS.md and the spec's
  lifecycle note): push `task/p2r06-ta-v2-design`, open one pull request
  carrying `Closes #4, closes #5`. No merge; merges only on Don's explicit
  instruction. The spec's anticipated AGENTS.md conflict at lines 72/106
  was already resolved on `main` by fix-round commit `1244bf0`; recorded
  in the Summary above, no AGENTS.md edit made.
- Scope note: `docs/research/specz-science-p2r05/derived-schema-contract.md`
  and `work-logs/worklog-2026-10-05-p2r05-adoption-answers.md` are outside
  spec section 5.2's modify list; both edits were explicitly instructed by
  the dispatch (issues #4/#5) and are recorded here as dispatch-authorized
  surface. All other changes lie within section 5.2. No raw holding,
  source table, P2R-05 product, production tension formula, or credential
  was touched; no database statement of any kind ran in this unit.
- No spec defects encountered; no stop condition arose; no lane was
  stopped.

### Per-gate commits

| Gate | Commit |
|---|---|
| 6.1a (issues #4/#5, dispatch-authorized) | `433ffad615aaf43fc20f3300759a4f47e9a622c2` |
| 6.1 | `5b395c41ceb0bfb7600d28b774af2a37f54e2a7a` |
| 6.2 | `56b3dc98d636b4dfacc876074717fcf09014c27f` |
| 6.3 | `8eae442b6482b43db6c78e417eda493d6f5b2a98` |
| 6.4 | `66fa849c1c3ceb32a53efa0c681eb34d66332bd5` |
| 6.5 | the commit carrying this closeout checkpoint |

### Final validation

- `pytest tests/test_ta_v2_design_contract.py -v`: 26/26 passed.
- `python src/inspection/validate_ta_v2_design.py`: cases 28/28, fit
  requests 4/4, mutations caught 9/9, exit 0; results tracked at
  `docs/research/ta-v2-design/validation-results.json`.
- Change surface verified against spec section 5.2 plus the two
  dispatch-authorized files (`git diff --name-only main..HEAD`).
- All new `docs/research/ta-v2-design/*.md` pass `check_frontmatter.py`.

Runtime facts: ML01; system Python 3.12.3 with PyYAML for the validator,
pytest 9.x via `/opt/agents/venv` for the suite. Elapsed time and token
usage unavailable from this runtime; recorded as such in the registry row.

## Files changed

| Surface | Change |
|---|---|
| `docs/research/ta-v2-design/` (README, input-contract, input-identity.json, feature-contract.yaml, scientific-design, fixtures.json, validation-results.json, evaluation-protocol, review) | Created; the proposed design contract and its evidence |
| `src/inspection/validate_ta_v2_design.py`, `src/inspection/README.md` | Pure validator and index row |
| `tests/test_ta_v2_design_contract.py`, `tests/README.md` | Contract suite and index section |
| `docs/research/README.md`, `docs/README.md`, `docs/project-state.md` | Index/status updates (bounded) |
| `docs/research/specz-science-p2r05/derived-schema-contract.md` | Adoption-state reconciliation (dispatch, issue #4) |
| `work-logs/worklog-2026-10-05-p2r05-adoption-answers.md` | Dated correction note (dispatch, issue #5) |
| `spec/2026-10/`, `spec/README.md`, `work-logs/README.md`, this worklog | Archive, indexes, per-gate checkpoints |
| Central queue `/opt/agents/repos/spec/` | Spec moved to `2026-10/` month archive; registry row appended |

## Next steps

Handoff: Don answers TA2-Q01 through TA2-Q06 in
`docs/research/ta-v2-design/review.md`. Implementation, fitting, database
installation, production scoring, and publication all await that approval
and a later named implementation unit. The PR stays unmerged until Don
instructs the merge in his own words.

<!-- Agent: kilo; Runtime: Kilo CLI; Model: kilo/zai-coding/glm-5.3; Session: interactive -->





