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
