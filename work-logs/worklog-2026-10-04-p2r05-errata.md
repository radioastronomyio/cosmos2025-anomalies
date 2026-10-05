---
title: "P2R-05 evidence errata worklog"
description: "Gate checkpoints for repairs to evidence code and documents"
author: "Codex"
date: "2026-10-04"
version: "1.0"
status: "completed"
tags:
  - type: worklog
  - domain: [astronomy, documentation]
agent: "codex"
runtime: "Codex desktop"
runtime_version: "unreported"
model: "unreported"
hostname: "ML01"
spec_ref: "../spec/2026-10/2026-10-04-cosmos2025-spec-01-p2r05-errata.md"
repo: "cosmos2025-anomalies"
category: "astronomy"
duration_seconds: 1466
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
| Status | Completed locally; Claude review pending |
| Agent | Codex desktop; exact runtime/model identifier unreported |
| Host | ML01; shared venv Python 3.12.3, psycopg 3.3.3, pytest 9.0.2 |
| Authorization | Don, coordinator chat, 2026-10-04 21:42 ET “Yes”, conveyed by dispatch |
| Review seat | Claude; handoff through Don, review pending |
| Starting branch/base | `main` / `f358b6d3e317edb0d95e21b612a59b6573c9e57f` |
| Execution branch | `task/p2r05-errata` |
| Evidence | `staging/2026-10-04-astra-p2r05-errata/README.md` |

Objective: repair AR-F01 through AR-F05 without altering the sealed product.

Outcome: all five errata gates pass with local commits and staged review
evidence. Scientific adoption and upstream sending remain Don's decisions.
No new scientific decision is made by this unit.

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


### Gate 2: installed verifier modes (AR-F01)

Gate 1 commit: `ba1582371d512c7fabaf89dd59c338f651715e4e`.

Added explicit `--mode pre-seal` and `--mode post-seal`. The default remains
pre-seal for historical compatibility. Post-seal requires `--run-id` and never
reads finalize-summary; it verifies sealed identities, three recorded and live
content digests, current implementation/run identity, tile-map consistency,
seal presence and pending adoption. Existing SELECT-only capability and source
count checks remain. Updated the review's current verification command.

`gate2-red.log`: 27 contract tests fail before implementation because the
mode-aware contract is absent. `gate2-green.log`: 55 focused tests pass,
including both modes, expected wrong-mode rejection, altered content/seal/input
or implementation, absent run, SELECT-only queries, and no post-seal staging
reads. Cache-free static checks pass (`gate2-lint.log`).

Live post-seal verification passes (`gate2-post-seal.json`). Live pre-seal
verification rejects this sealed run solely with “pre-seal mode requires an
unsealed run” (`gate2-pre-seal.json`), as intended. `gate2-identity.json` repeats
the full protected-module/run-ID/content guard: all identities and the entire
sealed metadata row are unchanged. The verifier hashes current implementation
bytes but uses the run's recorded input identities; it does not rehash raw
FITS files or perform new scientific verification. Gate 2 validation passed.


### Gate 3: visible numerical errata (AR-F03, AR-F04)

Gate 2 commit: `23d83bbe753e47a6787f25e05729dec7b4997c55`.

Corrected both evidence documents with visible errata tables explaining changes
and causes: confidence gains/losses in both populations, 259 eligible broad-line
members versus 261 before type routing (two excluded type-1 sources), 681/20,100
secure-preferred vetoes versus 722 catalog-wide, and the 11,183 / 8,263 / 654
secure-preferred corroboration split. The existing sensitivity table was
already numerically correct; its one-sided characterization was not.

Fresh analyst SELECTs reproduce all denominator and type/broad-line figures
(`gate3-document-counts.json`). `gate3-document-validation.json` confirms the
entire S5 acceptance section and compact policy rendering remain byte-identical
to main. Coverage reproduction now specifies errata staging; scratch-database
negative controls are clearly historical and were not rerun. Diff whitespace
checks pass. Gate 3 validation passed; adoption remains pending.


### Gate 4: upstream draft and local closeout (AR-F05)

Gate 3 commit: `c44e33003ba36ab3a74a4d7d0a8e0daf5309469c`.

Applied all four report corrections: separate unique/all lookup counts and
227 same-source correspondences; zero stored-coordinate identity versus
nonzero corrected-coordinate geometry; distinct defective and crossmatch joins;
full file hashes, held checkout/release refs, exact SQL and output-safe local
reproduction. Updated the existing S5-F10 summary to match this corrected
report, with a visible AR-F05 erratum, so the review does not retain the same
misleading compilation-wide non-resolution shorthand. No question or policy
text changed. The report remains local and unsent.

Executed the three SQL blocks and the exact embedded reproduction program.
`gate4-upstream-queries.json` and `upstream-query-rerun.json` agree.
`gate4-upstream-validation.json` matches independent counts exactly and angular
statistics within 1e-7 arcsec, confirms full manifest pins, and verifies the
local HEAD/release identities and identical FITS pointer blobs. No raw FITS
rehash, checkout change, download or remote operation occurred.

Closeout follows spec-closeout's local-only exception. The requested staged
spec is retained and a byte-identical copy is archived with an interior README
and archive index. Corrected its relative reference links before archival;
its scope and acceptance criteria are unchanged. Worklog and archive indexes
were checked for valid paths. No parent spec, worklog or registry record changed.
`review-handoff.md` gives Claude five pending closed questions with evidence.

`final-validation.json` confirms allowed changed paths, unchanged protected
files and live seal metadata, byte-identical policy/S5 sections, exact archive
copy, matching portable reproduction, valid Markdown frontmatter/links and no
deleted paths. Code was unchanged after the 55-test passing suite and static
check. Full content guards passed after both code gates; no additional build
or broad write-capable test suite was needed. No stop condition arose.

#### Per-gate commits

| Gate | Commit |
|---|---|
| 0 | `bb00127580a6c9d01d30324011924718891455a8` |
| 1 | `ba1582371d512c7fabaf89dd59c338f651715e4e` |
| 2 | `23d83bbe753e47a6787f25e05729dec7b4997c55` |
| 3 | `c44e33003ba36ab3a74a4d7d0a8e0daf5309469c` |
| 4 | The commit carrying this closeout checkpoint; full SHA in staged `closeout.json` and the appended registry summary |

Runtime facts: shared venv Python 3.12.3, psycopg 3.3.3, pytest 9.0.2.
Elapsed 1466 seconds from staged preflight to this closeout preparation;
this excludes earlier context loading. The runtime does not expose an exact
model/version string or trustworthy token/cost totals, so those are recorded
as unreported/unavailable. The closeout attestation and registry use the same
model value. The registry row is appended after the final local commit;
staged `closeout.json` records its receipt and all five full commit SHAs.

## 2. Files changed

| Surface | Change |
|---|---|
| `src/features/specz_science/coverage.py` | Two counter accumulations |
| `src/features/specz_science/check_installed_product.py` | Explicit modes and sealed-metadata verification |
| `tests/test_specz_science_coverage.py`, `tests/test_specz_science_installed_check.py` | Focused synthetic regressions and SELECT-only/CLI checks |
| `docs/research/specz-science-p2r05/review.md`, `coverage-baseline.md`, `upstream-report-draft.md` | Visible errata and accurate reproducible report |
| `spec/2026-10/`, `spec/README.md` | This new spec's archive and indexes |
| This worklog and `work-logs/README.md` | Per-gate checkpoints and closeout |
| Errata staging | Spec, check scripts, retained red/green logs, exact query outputs, identity guards, README and review handoff |

## 3. Issues and stop conditions

No material assumption, judgment, identity or blast-radius stop encountered.
No scientific calibration or outcome evaluation is authorized or performed.

## 4. Next steps

Handoff: Claude reviews `staging/2026-10-04-astra-p2r05-errata/review-handoff.md`
and the local branch against main. Don owns disposition, push and any later
merge or upstream send. All S5 answers remain pending; this unit does not
authorize T_A v2 or scientific use. No contact, paid model invocation, deletion
or recycle action occurred.

<!-- Agent: codex; Runtime: Codex desktop; Model: unreported; Session: interactive -->
