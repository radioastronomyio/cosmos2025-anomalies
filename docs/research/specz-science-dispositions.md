<!--
---
title: "Spec-z Science Dispositions"
description: "Operator decision record for P2R-05 policy and the 2026-10-05 scientific adoption with conditions, linked to the D-01 through D-07 review surface"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-22"
version: "1.1"
status: "Active - P2R-05 product adopted with conditions"
tags:
  - type: decision-record
  - domain: astronomy
  - domain: spectroscopy
  - tech: python
  - tech: postgresql
related_documents:
  - "[Spec P2R-05 v1.0](/opt/agents/repos/spec/2026-09-21-cosmos2025-spec-p2r-05-specz-science-surface.md)"
  - "[Spec-z Linkage Evidence](specz-linkage-evidence.md)"
  - "[P2R-05 Evidence](specz-science-p2r05/README.md)"
---
-->

# Spec-z Science Dispositions (P2R-05 Approval and Decision Record)

This is the durable decision record required by spec P2R-05 before any
deliverable. It records the operator approval that froze the execution
policy, links the inherited D-01 through D-07 closed questions to the policy
sections that dispose them, and separates three things that must never be
conflated:

1. **Approved policy** — the P-01 through P-09 defaults of the named spec
   version, frozen for this execution by the recorded approval below.
2. **Empirical priors** — observations reproduced as evidence in gates 5.3
   and 5.7. They are reproduction targets and diagnostics, not adopted
   science, and no prior was an operator decision.
3. **Scientific adoption decision** — Don answered S5-Q01 through S5-Q05 on
   2026-10-05 and adopted the product with recorded conditions. Downstream
   work follows those conditions. Every sealed product row retains the frozen
   `pending_scientific_adoption` value because no database transition was
   defined or authorized.

## Approval record

| Field | Value |
|---|---|
| Approved artifact | `/opt/agents/repos/spec/2026-09-21-cosmos2025-spec-p2r-05-specz-science-surface.md` |
| Spec version at approval | 1.0 (frontmatter updated from draft v0.3 at the operator's dispatch-session instruction, before digest computation) |
| Approved SHA-256 | `7f481111ad826dd80b01106eeec71bfdaf0f5c649c0cc79b8661a0087af2757b` |
| Approval authority | Don Fountain (operator) |
| Conveyed | Dispatch session on 2026-09-22, before any P2R-05 deliverable was built; durably recorded here and in `specz-science-p2r05/operator-interactions.md` |
| Scope of approval | Spec v1.0 as written, with policy defaults P-01 through P-09 frozen as the execution policy contract |
| Explicitly not approved by the 2026-09-22 policy approval | Scientific adoption of the then-unbuilt product; any change to the approved bytes; any relaxation or alternative selection among the sensitivity variants |

The dispatch session answer, condensed without changing its content: spec
v0.3-as-updated-to-v1.0 is the execution contract with P-01 through P-09
frozen; the frontmatter update to version 1.0 / status Active precedes digest
computation so the carried digest matches the archived artifact; the
dispositions record names the authority, the session, the policy set, and the
v1.0 digest; execution then proceeds 5.1 through 5.9.

## Scientific adoption record

| Field | Value |
|---|---|
| Decision date | 2026-10-05 |
| Authority | Don Fountain (operator), Action Registry `rec4acLZWCuN1tJk9` |
| Decision | Adopted with conditions through S5-Q01 to S5-Q05 |
| Conditions | The exact selection, sensitivity, diagnostic-population, partition, uncertainty and reporting conditions in [the P2R-05 review](specz-science-p2r05/review.md) govern downstream work |
| Database state | Sealed rows retain the frozen `pending_scientific_adoption` value; no database transition or adopted-state alias was defined or authorized |
| Effect | Conditionally approved downstream work may proceed under S5; secure spectroscopic redshifts carry no stellar-mass or SFR truth interpretation |

## D-01 through D-07 linkage

The closed questions of `specz-linkage-evidence.md` section 2 are disposed for
this execution by the following approved policy sections. The historical
recommendations in that document predate the additional `_all` audit and were
not individually adopted; where an approved policy section differs from a
prior recommendation, the approved policy governs.

| Disposition | Closed question (summary) | Disposing policy (spec v1.0) |
|---|---|---|
| D-01 | Population A selection rule | P-01: retain population A in the audit with no preferred reported redshift; ineligible for both secure-use populations; no Priority 0 promotion; no neighbour destination inferred |
| D-02 | Population B resolution rule | P-03 + P-04: preferred entry by valid-confidence ordering with `id_specz` tie-break, never averaged; independent conflict flags with the 0.005 absolute baseline veto |
| D-03 | Spectroscopic sample surface | P-01: association solely through `id_cosmos25 = photometry_primary.id`; `_unique` supplies preferred entries; `_all` supplies the full measurement audit |
| D-04 | Confidence threshold | P-02 + P-05: secure predicate requires recognized flag {3,4,13,14}, confidence in [95,100] consistent with the documented mapping; primary galaxy and separate validation conjunctions in P-05 |
| D-05 | Calibration and held-out validation split | P-06: frozen SHA-256 tile partitions (4 holdout / 4 validation / 12 development over the twenty-label domain), assigned before any fitting or outcome analysis |
| D-06 | Upstream defect report | P-08 prepared the local reproducible report; S5-Q05 later authorized transmission, with the channel pending Don's choice |
| D-07 | T_A v2 spectroscopic unblock | P-09 completed without calibration; the 2026-10-05 S5 record conditionally authorizes downstream use under its selection, sensitivity, partition and interpretation limits |

## What earlier surfaces claimed and this record does not

The P2R-04 review surface's recommendations (exclude population A; accept
agreeing groups; threshold 95; stratified splits; report upstream; do not
unblock T_A v2) were author recommendations attached to closed questions.
The operator's 2026-09-22 approval adopted the spec v1.0 policy set as
written, not those recommendations individually. Where both exist, the
approved policy text is the authority; the recommendations are context.

Don answered S5-Q01 through S5-Q05 on 2026-10-05 and scientifically adopted
the product with conditions. Downstream work may proceed only within those
recorded conditions. The sealed database remains mechanically unchanged:
rows retain `pending_scientific_adoption`, and no consumer-facing alias or
database status transition is implied by the scientific decision.
