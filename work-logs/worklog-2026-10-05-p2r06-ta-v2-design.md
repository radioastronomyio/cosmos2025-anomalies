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


