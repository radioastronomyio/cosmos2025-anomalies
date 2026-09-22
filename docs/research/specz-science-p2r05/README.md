# specz-science-p2r05 — P2R-05 Evidence and Review Surface

Durable evidence, derived schema contract, counts summaries, the review
document, and the local upstream-report draft for spec P2R-05. Large exports
and resumable checkpoints live under `staging/derived/specz-p2r05/`
(gitignored); anything an exclusion or conflict claim depends on is persisted
in the database product and referenced here by run/table/key identity.

## Contents

| Path | Content |
|---|---|
| `operator-interactions.md` | Durable operator decision record for this run |
| `evidence-5-3.md` | Gate 5.3 prior reproduction with surfaces, predicates, denominators |
| `tile-map.md` | Frozen P-06 partition map with canonical digest |
| `coverage-baseline.md` | Gate 5.7 coverage, attrition, and sensitivity evidence |
| `derived-schema-contract.md` | Physical field names and meanings of all derived columns |
| `review.md` | Gate 5.8 human review document with S5-F01+ findings and S5-Q01..Q05 |
| `upstream-report-draft.md` | Local, unsent incompatibility report (renumbering hypothesis unconfirmed) |

The approval/decision record for the run is
[`../specz-science-dispositions.md`](../specz-science-dispositions.md).
Staging evidence (snapshot manifest, priors, coverage JSON, negative
controls, seal record, product summaries) lives under
`staging/derived/specz-p2r05/` and is gitignored; every durable claim in
the tracked documents carries its reproduction command.
