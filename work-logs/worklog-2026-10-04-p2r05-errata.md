---
title: "P2R-05 evidence errata worklog"
description: "Gate checkpoints for repairs to evidence code and documents"
author: "Codex"
date: "2026-10-04"
version: "1.0"
status: "partial"
tags:
  - type: worklog
  - domain: [astronomy, documentation]
agent: "codex"
runtime: "Codex desktop"
runtime_version: "unreported"
model: "unreported"
hostname: "ML01"
spec_ref: "../staging/2026-10-04-astra-p2r05-errata/2026-10-04-cosmos2025-spec-01-p2r05-errata.md"
repo: "cosmos2025-anomalies"
category: "astronomy"
duration_seconds: null
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
  - "../staging/2026-10-04-astra-p2r05-adoption/adoption-review.md"
---

# P2R-05 evidence errata

## Summary

| Attribute | Value |
|---|---|
| Status | In progress |
| Agent | Codex desktop; exact runtime/model identifier unreported |
| Host | ML01; shared venv Python 3.12.3, psycopg 3.3.3, pytest 9.0.2 |
| Authorization | Don, coordinator chat, 2026-10-04 21:42 ET “Yes”, conveyed by dispatch |
| Review seat | Claude; handoff through Don, review pending |
| Starting branch/base | `main` / `f358b6d3e317edb0d95e21b612a59b6573c9e57f` |
| Execution branch | `task/p2r05-errata` |
| Evidence | `staging/2026-10-04-astra-p2r05-errata/README.md` |

Objective: repair AR-F01 through AR-F05 without altering the sealed product.

Outcome: checkpoints below; scientific adoption and upstream sending remain
Don's decisions. No new scientific decision is made by this unit.

## 1. Work completed

### Gate 0: spec and startup

- Loaded AGENTS, README, project state, documentation standards, unit
  conventions and analysis-target context in repository order. Read the
  spec-driven-prompt, spec-startup and spec-closeout lifecycle contracts.
- Confirmed clean `main`, tool availability and configured git author. No
  dependency install was needed. Normal sandbox startup fails on this host;
  approved escalated commands retain the explicit task restrictions.
- Wrote the staged spec before creating the branch. No issue number was
  supplied and remote operations are prohibited, so the dispatch's slug
  fallback is used. No issue, fetch, push, PR or merge was attempted.
- Recorded protected-file hashes and baseline in `preflight.json`. Captured
  live run metadata and full product digests in `gate0-identity.json`.
- Staging is intentionally gitignored. Closeout retains the staged spec and
  adds a byte-identical repository archive copy; the central active queue
  is not used for this explicitly staged dispatch.

Validation: environment and clean-base preflight pass; protected files and
sealed identity baseline recorded. Gate 0 commit is the commit carrying this
checkpoint (its full SHA is recorded at Gate 1 and in staged closeout).


### Gate 1: sensitivity totals (AR-F02)

Gate 0 commit: `bb00127580a6c9d01d30324011924718891455a8`.

Added the two missing accumulations without changing any predicate. Three
hand-counted variant fixtures fail against the original zero counters
(`gate1-red.log`) and pass with primary and separate counts distinguished.
The focused coverage, independent-reduction and split tests pass: 22 tests
(`gate1-green.log`). Full native snapshot coverage matches the independent
reconstruction in all headline and gained/lost counts:

| Variant | Primary | Separate |
|---|---:|---:|
| Confidence 97 | 14,738 | 598 |
| Absolute 0.001 | 16,992 | 480 |
| Normalized 0.005 | 18,567 | 760 |

`gate1-sensitivity-comparison.json` records the agreement. Confidence gains
are 213 primary and 39 separate. `gate1-identity.json` confirms the seven
modules recompute the pinned run ID, all three live content digests equal
sealed values, and the complete run metadata and protected files are unchanged.
No builder, installer or sealer ran. Gate 1 validation passed.

## 2. Files changed

Gate 0: new worklog, worklog index, and staged spec/README/check evidence.

## 3. Issues and stop conditions

No material assumption, judgment, identity or blast-radius stop encountered.
No scientific calibration or outcome evaluation is authorized or performed.

## 4. Next steps

Complete gates 1 through 4, then present the local branch and staged review
surface for Claude. Do not publish or adopt the product.

<!-- Agent: codex; Runtime: Codex desktop; Model: unreported; Session: interactive -->
